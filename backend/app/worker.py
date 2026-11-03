"""ARQ worker: `arq app.worker.WorkerSettings`.

Jobs live in Redis, so a sync survives an API restart. Job results/state the user sees are
written to Postgres (sync_jobs), which stays the source of truth.
"""

import asyncio
import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.redis import redis_client
from app.db.session import SessionLocal
from app.models import Game, Platform, SyncJob, SyncJobStatus
from app.services import achievements, igdb, steam
from app.services.catalog import get_or_create_game, upsert_library_entry
from app.services.queue import redis_settings

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def sync_steam(ctx: dict, job_id: int, steam_id: str) -> int:
    async with SessionLocal() as db:
        job = await db.get(SyncJob, job_id)
        if job is None:
            return 0
        job.status = SyncJobStatus.RUNNING
        await db.commit()

        try:
            owned = await steam.get_owned_games(steam_id)
            new_game_ids: list[int] = []
            for g in owned:
                game = await get_or_create_game(db, g.name, steam_appid=g.appid)
                await upsert_library_entry(
                    db,
                    user_id=job.user_id,
                    game=game,
                    platform=Platform.STEAM,
                    playtime_minutes=g.playtime_minutes,
                    last_played_at=g.last_played_at,
                )
                if game.metadata_updated_at is None:
                    new_game_ids.append(game.id)
            job.imported_count = len(owned)
            await db.commit()

            # Achievements are a bonus: a failure here keeps the imported library.
            try:
                await achievements.sync_steam_achievements(db, redis_client, job.user_id, steam_id)
                await db.commit()
            except (httpx.HTTPError, SQLAlchemyError) as e:
                logger.warning("Steam achievements sync failed for job %s: %s", job_id, e)
                await db.rollback()
                job = await db.get(SyncJob, job_id)
                job.error = "Biblioteca importada, pero falló la sincronización de logros."
            job.status = SyncJobStatus.SUCCESS
        except Exception as e:  # any failure must leave the job in a terminal state
            if not isinstance(e, steam.SteamError | httpx.HTTPError):
                logger.exception("Steam sync %s crashed", job_id)
            await db.rollback()
            job = await db.get(SyncJob, job_id)
            job.status = SyncJobStatus.FAILED
            job.error = str(e)[:1000]
            new_game_ids = []
        job.finished_at = _now()
        await db.commit()

    if new_game_ids:
        await ctx["redis"].enqueue_job("enrich_games", new_game_ids)
    return job.imported_count


async def enrich_games(ctx: dict, game_ids: list[int]) -> int:
    if not igdb.is_configured():
        logger.warning("IGDB not configured; skipping enrichment of %d games", len(game_ids))
        return 0
    enriched = 0
    async with SessionLocal() as db:
        games = (await db.scalars(select(Game).where(Game.id.in_(game_ids)))).all()

        # Steam games are matched exactly by app id, in two batched requests.
        prefetched: dict[int, igdb.IgdbSearchResult] = {}
        steam_games = [g for g in games if g.steam_appid and not g.igdb_id]
        try:
            by_appid = await igdb.igdb_ids_for_steam(
                redis_client, [g.steam_appid for g in steam_games]
            )
            metas = await igdb.get_many(redis_client, list(by_appid.values()))
            for g in steam_games:
                if (igdb_id := by_appid.get(g.steam_appid)) and igdb_id in metas:
                    prefetched[g.id] = metas[igdb_id]
        except httpx.HTTPError as e:
            logger.warning("IGDB Steam batch lookup failed, falling back to titles: %s", e)

        # Games already matched to IGDB: refresh their metadata (incl. ratings) in batches too.
        known = [g for g in games if g.igdb_id and g.id not in prefetched]
        try:
            metas = await igdb.get_many(redis_client, [g.igdb_id for g in known])
            for g in known:
                if g.igdb_id in metas:
                    prefetched[g.id] = metas[g.igdb_id]
        except httpx.HTTPError as e:
            logger.warning("IGDB batch refresh failed, falling back to one by one: %s", e)

        for game in games:
            try:
                if game.id not in prefetched:
                    await asyncio.sleep(0.3)  # stay under IGDB's 4 requests/second
                if await igdb.enrich_game(db, redis_client, game, prefetched.get(game.id)):
                    enriched += 1
                await db.commit()
            except httpx.HTTPError as e:
                logger.warning("IGDB enrichment failed for game %s: %s", game.id, e)
    logger.info("Enriched %d/%d games", enriched, len(game_ids))
    return enriched


class WorkerSettings:
    functions = [sync_steam, enrich_games]
    redis_settings = redis_settings
    max_jobs = 5
    job_timeout = 600
