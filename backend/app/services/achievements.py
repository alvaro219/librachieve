"""Steam achievements sync (official Steam Web API).

Per game: the schema (names, icons, in Spanish) and global unlock percentages are shared by all
users and refreshed at most weekly; the player's unlocks are fetched on every sync, but only for
games with playtime (an unplayed game can't have unlocks).
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from redis.asyncio import Redis
from sqlalchemy import delete, func, select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.http import describe_error
from app.models import Achievement, Game, LibraryEntry, Platform, UserAchievement

logger = logging.getLogger(__name__)

API_URL = "https://api.steampowered.com/ISteamUserStats"
SCHEMA_TTL_SECONDS = 7 * 24 * 3600
LANGUAGE = "spanish"
_CONCURRENCY = 6


@dataclass
class _SteamGameData:
    schema: list[dict] | None = None  # None = not refreshed this time
    global_percent: dict[str, float] = field(default_factory=dict)
    player: dict[str, int] | None = None  # api_name -> unlock unix time (0 = locked)


async def _get_json(client: httpx.AsyncClient, url: str, params: dict) -> dict | None:
    """Steam answers 400/403 for games without stats or not owned: treat as no data."""
    resp = await client.get(url, params=params)
    if resp.status_code in (400, 403, 404):
        return None
    resp.raise_for_status()
    return resp.json()


async def _fetch_game(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    steam_id: str,
    appid: int,
    refresh_schema: bool,
    fetch_player: bool,
) -> _SteamGameData:
    data = _SteamGameData()
    async with sem:
        if refresh_schema:
            schema = await _get_json(
                client,
                f"{API_URL}/GetSchemaForGame/v2/",
                {"key": settings.steam_api_key, "appid": appid, "l": LANGUAGE},
            )
            stats = ((schema or {}).get("game") or {}).get("availableGameStats") or {}
            data.schema = stats.get("achievements") or []
            if data.schema:
                pct = await _get_json(
                    client,
                    f"{API_URL}/GetGlobalAchievementPercentagesForApp/v2/",
                    {"gameid": appid},
                )
                for a in ((pct or {}).get("achievementpercentages") or {}).get("achievements", []):
                    try:
                        data.global_percent[a["name"]] = float(a["percent"])
                    except (KeyError, TypeError, ValueError):
                        pass
        if fetch_player:
            player = await _get_json(
                client,
                f"{API_URL}/GetPlayerAchievements/v1/",
                {"key": settings.steam_api_key, "steamid": steam_id, "appid": appid},
            )
            stats = (player or {}).get("playerstats") or {}
            if stats.get("success"):
                data.player = {
                    a["apiname"]: int(a.get("unlocktime") or 0) or (1 if a.get("achieved") else 0)
                    for a in stats.get("achievements") or []
                    if a.get("achieved")
                }
    return data


async def _store_schema(db: AsyncSession, game_id: int, data: _SteamGameData) -> None:
    rows = [
        {
            "game_id": game_id,
            "platform": Platform.STEAM,
            "api_name": a["name"],
            "name": (a.get("displayName") or a["name"])[:255],
            "description": a.get("description") or None,
            "icon_url": a.get("icon"),
            "icon_locked_url": a.get("icongray"),
            "hidden": bool(a.get("hidden")),
            "global_percent": data.global_percent.get(a["name"]),
            "display_order": i,
        }
        for i, a in enumerate(data.schema or [])
        if a.get("name")
    ]
    if rows:
        stmt = insert(Achievement).values(rows)
        cols = (
            "name",
            "description",
            "icon_url",
            "icon_locked_url",
            "hidden",
            "display_order",
        )
        await db.execute(
            stmt.on_conflict_do_update(
                index_elements=["game_id", "platform", "api_name"],
                set_={c: stmt.excluded[c] for c in cols}
                # A failed percentages fetch must not wipe the values we already have
                | {
                    "global_percent": func.coalesce(
                        stmt.excluded.global_percent, Achievement.global_percent
                    )
                },
            )
        )
    # Achievements removed from the game's schema
    names = [r["api_name"] for r in rows]
    await db.execute(
        delete(Achievement).where(
            Achievement.game_id == game_id,
            Achievement.platform == Platform.STEAM,
            Achievement.api_name.not_in(names) if names else true(),
        )
    )


async def _store_player(
    db: AsyncSession, user_id: int, game_id: int, unlocked: dict[str, int]
) -> None:
    ids_by_name = dict(
        (
            await db.execute(
                select(Achievement.api_name, Achievement.id).where(
                    Achievement.game_id == game_id, Achievement.platform == Platform.STEAM
                )
            )
        ).all()
    )
    rows = [
        {
            "user_id": user_id,
            "achievement_id": ids_by_name[name],
            "unlocked_at": datetime.fromtimestamp(ts, UTC).replace(tzinfo=None) if ts > 1 else None,
        }
        for name, ts in unlocked.items()
        if name in ids_by_name
    ]
    if rows:
        stmt = insert(UserAchievement).values(rows)
        await db.execute(
            stmt.on_conflict_do_update(
                index_elements=["user_id", "achievement_id"],
                set_={"unlocked_at": stmt.excluded.unlocked_at},
            )
        )


async def _refresh_counters(db: AsyncSession, entry: LibraryEntry) -> None:
    total = await db.scalar(
        select(func.count()).where(
            Achievement.game_id == entry.game_id, Achievement.platform == entry.platform
        )
    )
    unlocked = await db.scalar(
        select(func.count())
        .select_from(UserAchievement)
        .join(Achievement, Achievement.id == UserAchievement.achievement_id)
        .where(
            UserAchievement.user_id == entry.user_id,
            Achievement.game_id == entry.game_id,
            Achievement.platform == entry.platform,
        )
    )
    entry.achievements_total = total or 0
    entry.achievements_unlocked = unlocked or 0


async def sync_steam_achievements(
    db: AsyncSession, redis: Redis, user_id: int, steam_id: str
) -> int:
    """Sync schemas + the user's unlocks for every Steam game in their library.

    Returns the number of games that have achievements.
    """
    rows = (
        await db.execute(
            select(LibraryEntry, Game.steam_appid)
            .join(Game, Game.id == LibraryEntry.game_id)
            .where(
                LibraryEntry.user_id == user_id,
                LibraryEntry.platform == Platform.STEAM,
                Game.steam_appid.is_not(None),
            )
        )
    ).all()
    if not rows:
        return 0

    sem = asyncio.Semaphore(_CONCURRENCY)
    plans = []
    for entry, appid in rows:
        fresh = await redis.exists(f"steam:achievements-schema:{appid}")
        plans.append((entry, appid, not fresh, entry.playtime_minutes > 0))

    async with httpx.AsyncClient(timeout=20) as client:
        results = await asyncio.gather(
            *(
                _fetch_game(client, sem, steam_id, appid, refresh, player)
                for _, appid, refresh, player in plans
            ),
            return_exceptions=True,
        )

    with_achievements = 0
    for (entry, appid, _, _), data in zip(plans, results, strict=True):
        if isinstance(data, BaseException):
            logger.warning("Steam achievements failed for app %s: %s", appid, describe_error(data))
            continue
        if data.schema is not None:
            await _store_schema(db, entry.game_id, data)
            await redis.set(f"steam:achievements-schema:{appid}", "1", ex=SCHEMA_TTL_SECONDS)
        if data.player:
            await _store_player(db, user_id, entry.game_id, data.player)
        await _refresh_counters(db, entry)
        if entry.achievements_total:
            with_achievements += 1
    return with_achievements
