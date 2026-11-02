"""IGDB client. Every API response is cached in Redis for settings.igdb_cache_ttl_seconds (24h).

Matching strategy (most to least reliable):
1. Steam games: IGDB `external_games` lookup by Steam app id (exact).
2. Other titles: exact (case-insensitive) name match, preferring main games with most ratings.
3. No exact match: leave the game without metadata rather than attach the wrong game.
"""

import asyncio
import json
import logging
import re
from datetime import UTC, datetime

import httpx
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.game import Game
from app.schemas.game import IgdbSearchResult
from app.services.catalog import normalize_title

logger = logging.getLogger(__name__)

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
API_URL = "https://api.igdb.com/v4"
COVER_URL = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"
FIELDS = (
    "fields name,summary,first_release_date,cover.image_id,genres.name,"
    "total_rating_count,game_type;"
)
STEAM_SOURCE = 1  # external_game_source id for Steam
# game_type: 0 main game, 8 remake, 9 remaster, 10 expanded game, 11 port
_MAIN_GAME_TYPES = {0, 8, 9, 10, 11}

_TOKEN_KEY = "igdb:token"
_TRADEMARKS = re.compile(r"[™®©]")


class IgdbNotConfigured(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(settings.igdb_client_id and settings.igdb_client_secret)


async def _get_token(redis: Redis, client: httpx.AsyncClient) -> str:
    token = await redis.get(_TOKEN_KEY)
    if token:
        return token
    resp = await client.post(
        TOKEN_URL,
        params={
            "client_id": settings.igdb_client_id,
            "client_secret": settings.igdb_client_secret,
            "grant_type": "client_credentials",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    await redis.set(_TOKEN_KEY, data["access_token"], ex=max(int(data["expires_in"]) - 300, 60))
    return data["access_token"]


async def _post(redis: Redis, endpoint: str, body: str) -> list[dict]:
    """Uncached IGDB request. Retries once on an expired token or rate limit (4 req/s)."""
    if not is_configured():
        raise IgdbNotConfigured("IGDB_CLIENT_ID / IGDB_CLIENT_SECRET are not set")
    async with httpx.AsyncClient(timeout=20) as client:
        for attempt in range(2):
            token = await _get_token(redis, client)
            resp = await client.post(
                f"{API_URL}/{endpoint}",
                content=body,
                headers={"Client-ID": settings.igdb_client_id, "Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 401 and attempt == 0:
                await redis.delete(_TOKEN_KEY)
                continue
            if resp.status_code == 429 and attempt == 0:
                await asyncio.sleep(1)
                continue
            break
        resp.raise_for_status()
        return resp.json()


async def _query(redis: Redis, endpoint: str, body: str, cache_key: str) -> list[dict]:
    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)
    data = await _post(redis, endpoint, body)
    await redis.set(cache_key, json.dumps(data), ex=settings.igdb_cache_ttl_seconds)
    return data


def _to_result(raw: dict) -> IgdbSearchResult:
    cover = raw.get("cover") or {}
    ts = raw.get("first_release_date")
    return IgdbSearchResult(
        igdb_id=raw["id"],
        title=raw.get("name", ""),
        cover_url=COVER_URL.format(image_id=cover["image_id"]) if cover.get("image_id") else None,
        release_date=datetime.fromtimestamp(ts, UTC).date() if ts else None,
        genres=[g["name"] for g in raw.get("genres") or [] if "name" in g],
        summary=raw.get("summary"),
    )


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def clean_title(title: str) -> str:
    """'Battlefield™ 1' -> 'Battlefield 1' (what IGDB stores)."""
    return " ".join(_TRADEMARKS.sub("", title).split())


async def search(redis: Redis, query: str, limit: int = 10) -> list[IgdbSearchResult]:
    query = clean_title(query)
    body = f'search "{_escape(query)}"; {FIELDS} limit {limit};'
    key = f"igdb:search:{normalize_title(query)}:{limit}"
    return [_to_result(r) for r in await _query(redis, "games", body, key)]


async def get_by_id(redis: Redis, igdb_id: int) -> IgdbSearchResult | None:
    body = f"{FIELDS} where id = {int(igdb_id)};"
    rows = await _query(redis, "games", body, f"igdb:game:{igdb_id}")
    return _to_result(rows[0]) if rows else None


async def get_many(redis: Redis, igdb_ids: list[int]) -> dict[int, IgdbSearchResult]:
    """Batch fetch, sharing the per-id cache with get_by_id."""
    found: dict[int, IgdbSearchResult] = {}
    missing = []
    for igdb_id in dict.fromkeys(igdb_ids):
        cached = await redis.get(f"igdb:game:{igdb_id}")
        if cached is None:
            missing.append(igdb_id)
        elif rows := json.loads(cached):
            found[igdb_id] = _to_result(rows[0])
    for i in range(0, len(missing), 200):
        chunk = missing[i : i + 200]
        rows = await _post(
            redis, "games", f"{FIELDS} where id = ({','.join(map(str, chunk))}); limit 500;"
        )
        by_id = {r["id"]: r for r in rows}
        for igdb_id in chunk:
            raw = by_id.get(igdb_id)
            await redis.set(
                f"igdb:game:{igdb_id}",
                json.dumps([raw] if raw else []),
                ex=settings.igdb_cache_ttl_seconds,
            )
            if raw:
                found[igdb_id] = _to_result(raw)
    return found


async def igdb_ids_for_steam(redis: Redis, appids: list[int]) -> dict[int, int]:
    """Map Steam app ids to IGDB game ids. Unknown app ids are cached as misses ("0")."""
    result: dict[int, int] = {}
    missing = []
    for appid in dict.fromkeys(appids):
        cached = await redis.get(f"igdb:steam:{appid}")
        if cached is None:
            missing.append(appid)
        elif cached != "0":
            result[appid] = int(cached)
    for i in range(0, len(missing), 200):
        chunk = missing[i : i + 200]
        uids = ",".join(f'"{a}"' for a in chunk)
        rows = await _post(
            redis,
            "external_games",
            f"fields game,uid; where external_game_source = {STEAM_SOURCE} & uid = ({uids});"
            " limit 500;",
        )
        mapping = {int(r["uid"]): r["game"] for r in rows if r.get("game") and r.get("uid")}
        for appid in chunk:
            await redis.set(
                f"igdb:steam:{appid}",
                str(mapping.get(appid, 0)),
                ex=settings.igdb_cache_ttl_seconds,
            )
        result.update(mapping)
    return result


def pick_exact(title: str, rows: list[dict]) -> dict | None:
    """Best IGDB row whose name equals the title: main games first, then most rated."""
    wanted = normalize_title(title)
    exact = [r for r in rows if normalize_title(r.get("name", "")) == wanted]
    if not exact:
        return None
    return max(
        exact,
        key=lambda r: (r.get("game_type", 0) in _MAIN_GAME_TYPES, r.get("total_rating_count", 0)),
    )


async def find_by_title(redis: Redis, title: str) -> IgdbSearchResult | None:
    name = clean_title(title)
    key = normalize_title(name)
    # `~` is case-insensitive equality; IGDB's fuzzy `search` often ranks the famous game low.
    rows = await _query(
        redis, "games", f'{FIELDS} where name ~ "{_escape(name)}"; limit 50;', f"igdb:name:{key}"
    )
    best = pick_exact(name, rows)
    if best is None:
        rows = await _query(
            redis, "games", f'search "{_escape(name)}"; {FIELDS} limit 20;', f"igdb:search:{key}:20"
        )
        best = pick_exact(name, rows)
    return _to_result(best) if best else None


def apply_metadata(game: Game, meta: IgdbSearchResult) -> None:
    game.cover_url = meta.cover_url or game.cover_url
    game.summary = meta.summary or game.summary
    game.release_date = meta.release_date or game.release_date
    game.genres = meta.genres or game.genres
    game.metadata_updated_at = datetime.now(UTC).replace(tzinfo=None)


async def enrich_game(
    db: AsyncSession, redis: Redis, game: Game, meta: IgdbSearchResult | None = None
) -> bool:
    """Fill cover/genres/summary/release date from IGDB. Returns True if metadata was found.

    `meta` may be pre-fetched by the caller (batch Steam lookups).
    """
    if meta is None:
        if game.igdb_id:
            meta = await get_by_id(redis, game.igdb_id)
        else:
            meta = await find_by_title(redis, game.title)

    if meta is None:
        game.metadata_updated_at = datetime.now(UTC).replace(tzinfo=None)
        return False

    if game.igdb_id is None:
        taken = await db.scalar(select(Game.id).where(Game.igdb_id == meta.igdb_id))
        if taken is None:
            game.igdb_id = meta.igdb_id
        else:
            # Another catalogue row already represents this IGDB game (e.g. same title from a
            # different store). Keep both rows but share the metadata.
            logger.info("IGDB id %s already linked to game %s", meta.igdb_id, taken)
    apply_metadata(game, meta)
    return True
