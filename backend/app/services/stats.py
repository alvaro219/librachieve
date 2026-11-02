from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Game, GameStatus, LibraryEntry
from app.schemas.user import GenreStat, PlatformStat, UserStats


async def compute_user_stats(db: AsyncSession, user_id: int, top_genres: int = 8) -> UserStats:
    by_status_rows = await db.execute(
        select(LibraryEntry.status, func.count())
        .where(LibraryEntry.user_id == user_id)
        .group_by(LibraryEntry.status)
    )
    by_status = {status.value: count for status, count in by_status_rows.all()}

    total_playtime = await db.scalar(
        select(func.coalesce(func.sum(LibraryEntry.playtime_minutes), 0)).where(
            LibraryEntry.user_id == user_id
        )
    )

    ach_unlocked, ach_total, perfect = (
        await db.execute(
            select(
                func.coalesce(func.sum(LibraryEntry.achievements_unlocked), 0),
                func.coalesce(func.sum(LibraryEntry.achievements_total), 0),
                func.count().filter(
                    LibraryEntry.achievements_total > 0,
                    LibraryEntry.achievements_unlocked >= LibraryEntry.achievements_total,
                ),
            ).where(LibraryEntry.user_id == user_id)
        )
    ).one()

    platform_rows = await db.execute(
        select(LibraryEntry.platform, func.count())
        .where(LibraryEntry.user_id == user_id, LibraryEntry.status != GameStatus.WISHLIST)
        .group_by(LibraryEntry.platform)
        .order_by(func.count().desc())
    )

    genre = func.unnest(Game.genres).label("genre")
    genre_sub = (
        select(genre, LibraryEntry.playtime_minutes.label("playtime"))
        .join(Game, Game.id == LibraryEntry.game_id)
        .where(LibraryEntry.user_id == user_id, LibraryEntry.status != GameStatus.WISHLIST)
        .subquery()
    )
    genre_rows = await db.execute(
        select(genre_sub.c.genre, func.sum(genre_sub.c.playtime), func.count())
        .group_by(genre_sub.c.genre)
        .order_by(func.sum(genre_sub.c.playtime).desc(), func.count().desc())
        .limit(top_genres)
    )

    total = sum(by_status.values())
    owned = total - by_status.get(GameStatus.WISHLIST.value, 0)
    completed = by_status.get(GameStatus.COMPLETED.value, 0)

    return UserStats(
        total_games=total,
        total_playtime_minutes=int(total_playtime or 0),
        completed_games=completed,
        completion_ratio=round(completed / owned, 4) if owned else 0.0,
        games_by_status={s.value: by_status.get(s.value, 0) for s in GameStatus},
        achievements_unlocked=int(ach_unlocked),
        achievements_total=int(ach_total),
        perfect_games=perfect,
        top_genres=[
            GenreStat(genre=g, playtime_minutes=int(p or 0), games=c) for g, p, c in genre_rows
        ],
        games_by_platform=[PlatformStat(platform=p.value, games=c) for p, c in platform_rows],
    )
