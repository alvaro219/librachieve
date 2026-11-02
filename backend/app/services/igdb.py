"""IGDB client. Every API response is cached in Redis for settings.igdb_cache_ttl_seconds (24h)."""

import json
import logging
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
FIELDS = "fields name,slug,summary,first_release_date,cover.image_id,genres.name;"

_TOKEN_KEY = "igdb:token"


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


async def _query(redis: Redis, endpoint: str, body: str, cache_key: str) -> list[dict]:
    if not is_configured():
        raise IgdbNotConfigured("IGDB_CLIENT_ID / IGDB_CLIENT_SECRET are not set")

    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    async with httpx.AsyncClient(timeout=15) as client:
        token = await _get_token(redis, client)
        resp = await client.post(
            f"{API_URL}/{endpoint}",
            content=body,
            headers={"Client-ID": settings.igdb_client_id, "Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 401:  # token revoked early: drop it and retry once
            await redis.delete(_TOKEN_KEY)
            token = await _get_token(redis, client)
            resp = await client.post(
                f"{API_URL}/{endpoint}",
                content=body,
                headers={"Client-ID": settings.igdb_client_id, "Authorization": f"Bearer {token}"},
            )
        resp.raise_for_status()
        data = resp.json()

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


async def search(redis: Redis, query: str, limit: int = 10) -> list[IgdbSearchResult]:
    query = query.strip()
    body = f'search "{_escape(query)}"; {FIELDS} limit {limit};'
    key = f"igdb:search:{normalize_title(query)}:{limit}"
    return [_to_result(r) for r in await _query(redis, "games", body, key)]


async def get_by_id(redis: Redis, igdb_id: int) -> IgdbSearchResult | None:
    body = f"{FIELDS} where id = {int(igdb_id)};"
    rows = await _query(redis, "games", body, f"igdb:game:{igdb_id}")
    return _to_result(rows[0]) if rows else None


def _best_match(title: str, results: list[IgdbSearchResult]) -> IgdbSearchResult | None:
    if not results:
        return None
    wanted = normalize_title(title)
    for r in results:
        if normalize_title(r.title) == wanted:
            return r
    return results[0]


def apply_metadata(game: Game, meta: IgdbSearchResult) -> None:
    game.cover_url = meta.cover_url or game.cover_url
    game.summary = meta.summary or game.summary
    game.release_date = meta.release_date or game.release_date
    game.genres = meta.genres or game.genres
    game.metadata_updated_at = datetime.now(UTC).replace(tzinfo=None)


async def enrich_game(db: AsyncSession, redis: Redis, game: Game) -> bool:
    """Fill cover/genres/summary/release date from IGDB. Returns True if metadata was found."""
    if game.igdb_id:
        meta = await get_by_id(redis, game.igdb_id)
    else:
        meta = _best_match(game.title, await search(redis, game.title, limit=5))

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
