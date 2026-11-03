"""Management commands.

Usage:
  python -m app.cli make-admin <username>
  python -m app.cli reenrich [--all]   # queue IGDB lookups (--all re-matches every game)
  python -m app.cli refresh-metadata   # re-fetch IGDB data (covers, ratings...) keeping matches
"""

import asyncio
import sys

from sqlalchemy import func, select, update

from app.db.session import SessionLocal, engine
from app.models import Game, User, UserRole
from app.services.queue import close_queue, get_queue


async def make_admin(username: str) -> int:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(func.lower(User.username) == username.lower()))
        if user is None:
            print(f"User '{username}' not found", file=sys.stderr)
            return 1
        user.role = UserRole.ADMIN
        await db.commit()
    print(f"'{username}' is now an admin")
    return 0


async def reenrich(all_games: bool) -> int:
    async with SessionLocal() as db:
        if all_games:
            await db.execute(
                update(Game).values(
                    igdb_id=None,
                    cover_url=None,
                    summary=None,
                    release_date=None,
                    genres=[],
                    metadata_updated_at=None,
                )
            )
            await db.commit()
        ids = list(await db.scalars(select(Game.id).where(Game.metadata_updated_at.is_(None))))
    if ids:
        await (await get_queue()).enqueue_job("enrich_games", ids)
        await close_queue()
    print(f"Queued {len(ids)} games for IGDB enrichment")
    return 0


async def refresh_metadata() -> int:
    """Re-download IGDB metadata for every game, keeping the existing IGDB matches."""
    from app.core.redis import redis_client

    keys = [k async for k in redis_client.scan_iter("igdb:game:*")]
    if keys:
        await redis_client.delete(*keys)
    async with SessionLocal() as db:
        ids = list(await db.scalars(select(Game.id)))
    if ids:
        await (await get_queue()).enqueue_job("enrich_games", ids)
        await close_queue()
    print(f"Queued {len(ids)} games for an IGDB metadata refresh")
    return 0


async def _run(coro) -> int:
    try:
        return await coro
    finally:
        await engine.dispose()


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "make-admin":
        return asyncio.run(_run(make_admin(args[1])))
    if args == ["refresh-metadata"]:
        return asyncio.run(_run(refresh_metadata()))
    if args[:1] == ["reenrich"] and args[1:] in ([], ["--all"]):
        return asyncio.run(_run(reenrich(args[1:] == ["--all"])))
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
