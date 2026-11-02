import re
import unicodedata
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GameStatus, LibraryEntry, Platform
from app.models.game import Game

_TRADEMARKS = re.compile(r"[™®©]")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_title(title: str) -> str:
    """Lowercase, strip accents/trademarks/punctuation so 'DOOM®' and 'Doom' match."""
    text = _TRADEMARKS.sub("", title)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return _NON_ALNUM.sub(" ", text.lower()).strip()


async def get_or_create_game(
    db: AsyncSession,
    title: str,
    *,
    steam_appid: int | None = None,
    igdb_id: int | None = None,
) -> Game:
    title = title.strip()
    normalized = normalize_title(title)

    game = None
    if steam_appid is not None:
        game = await db.scalar(select(Game).where(Game.steam_appid == steam_appid))
    if game is None and igdb_id is not None:
        game = await db.scalar(select(Game).where(Game.igdb_id == igdb_id))
    if game is None and normalized:
        game = await db.scalar(
            select(Game).where(Game.normalized_title == normalized).order_by(Game.id).limit(1)
        )

    if game is None:
        game = Game(
            title=title,
            normalized_title=normalized,
            steam_appid=steam_appid,
            igdb_id=igdb_id,
            genres=[],
        )
        db.add(game)
        await db.flush()
    elif steam_appid is not None and game.steam_appid is None:
        game.steam_appid = steam_appid
    return game


async def upsert_library_entry(
    db: AsyncSession,
    *,
    user_id: int,
    game: Game,
    platform: Platform,
    playtime_minutes: int = 0,
    last_played_at: datetime | None = None,
    status: GameStatus | None = None,
) -> tuple[LibraryEntry, bool]:
    """Insert or refresh an entry. Re-syncs update playtime but keep the user's chosen status.

    Returns (entry, created).
    """
    entry = await db.scalar(
        select(LibraryEntry).where(
            LibraryEntry.user_id == user_id,
            LibraryEntry.game_id == game.id,
            LibraryEntry.platform == platform,
        )
    )
    if entry is None:
        entry = LibraryEntry(
            user_id=user_id,
            game_id=game.id,
            platform=platform,
            status=status or GameStatus.BACKLOG,
            playtime_minutes=playtime_minutes,
            last_played_at=last_played_at,
        )
        db.add(entry)
        await db.flush()
        return entry, True

    entry.playtime_minutes = max(entry.playtime_minutes, playtime_minutes)
    if last_played_at and (entry.last_played_at is None or last_played_at > entry.last_played_at):
        entry.last_played_at = last_played_at
    return entry, False
