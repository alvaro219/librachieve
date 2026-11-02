"""GraphQL is used only for library list queries with complex filtering (see CLAUDE.md)."""

import enum
from datetime import date, datetime

import strawberry
from fastapi import Depends, HTTPException, Request
from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext, GraphQLRouter

from app.db.session import get_db
from app.deps import user_from_token
from app.models import Game, LibraryEntry, User
from app.models import GameStatus as GameStatusModel
from app.models import Platform as PlatformModel
from app.routers.users import get_visible_user
from app.services.catalog import normalize_title

GameStatus = strawberry.enum(GameStatusModel)
Platform = strawberry.enum(PlatformModel)


@strawberry.enum
class LibrarySortField(enum.Enum):
    TITLE = "title"
    PLAYTIME = "playtime"
    ADDED_AT = "added_at"
    LAST_PLAYED = "last_played"
    RELEASE_DATE = "release_date"
    ACHIEVEMENTS = "achievements"


@strawberry.enum
class SortDirection(enum.Enum):
    ASC = "asc"
    DESC = "desc"


@strawberry.type
class GameType:
    id: int
    title: str
    igdb_id: int | None
    steam_appid: int | None
    cover_url: str | None
    summary: str | None
    release_date: date | None
    genres: list[str]


@strawberry.type
class LibraryEntryType:
    id: int
    platform: Platform
    status: GameStatus
    custom_folder: str | None
    playtime_minutes: int
    is_favorite: bool
    last_played_at: datetime | None
    added_at: datetime
    achievements_unlocked: int
    achievements_total: int
    game: GameType


@strawberry.type
class LibraryPageType:
    items: list[LibraryEntryType]
    total: int


@strawberry.input
class LibraryFilter:
    statuses: list[GameStatus] | None = None
    platforms: list[Platform] | None = None
    genres: list[str] | None = strawberry.field(
        default=None, description="Entries whose game has ANY of these genres"
    )
    search: str | None = None
    custom_folder: str | None = None
    favorites_only: bool = False
    min_playtime_minutes: int | None = None
    max_playtime_minutes: int | None = None
    released_after: date | None = None
    released_before: date | None = None


@strawberry.input
class LibrarySort:
    field: LibrarySortField = LibrarySortField.TITLE
    direction: SortDirection = SortDirection.ASC


class Context(BaseContext):
    def __init__(self, db: AsyncSession, user: User | None):
        super().__init__()
        self.db = db
        self.user = user


async def get_context(request: Request, db: AsyncSession = Depends(get_db)) -> Context:
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else None
    return Context(db, await user_from_token(db, token))


_SORT_COLUMNS = {
    LibrarySortField.TITLE: Game.normalized_title,
    LibrarySortField.PLAYTIME: LibraryEntry.playtime_minutes,
    LibrarySortField.ADDED_AT: LibraryEntry.added_at,
    LibrarySortField.LAST_PLAYED: LibraryEntry.last_played_at,
    LibrarySortField.RELEASE_DATE: Game.release_date,
    # Completion ratio; games without achievements sort last (NULL)
    LibrarySortField.ACHIEVEMENTS: LibraryEntry.achievements_unlocked
    * 1.0
    / func.nullif(LibraryEntry.achievements_total, 0),
}


def apply_filter(stmt: Select, f: LibraryFilter | None) -> Select:
    if f is None:
        return stmt
    if f.statuses:
        stmt = stmt.where(LibraryEntry.status.in_([GameStatusModel(s.value) for s in f.statuses]))
    if f.platforms:
        stmt = stmt.where(LibraryEntry.platform.in_([PlatformModel(p.value) for p in f.platforms]))
    if f.genres:
        stmt = stmt.where(Game.genres.overlap(f.genres))
    if f.search:
        stmt = stmt.where(Game.normalized_title.contains(normalize_title(f.search)))
    if f.favorites_only:
        stmt = stmt.where(LibraryEntry.is_favorite.is_(True))
    if f.custom_folder:
        stmt = stmt.where(LibraryEntry.custom_folder == f.custom_folder)
    if f.min_playtime_minutes is not None:
        stmt = stmt.where(LibraryEntry.playtime_minutes >= f.min_playtime_minutes)
    if f.max_playtime_minutes is not None:
        stmt = stmt.where(LibraryEntry.playtime_minutes <= f.max_playtime_minutes)
    if f.released_after:
        stmt = stmt.where(Game.release_date >= f.released_after)
    if f.released_before:
        stmt = stmt.where(Game.release_date <= f.released_before)
    return stmt


def _to_type(e: LibraryEntry) -> LibraryEntryType:
    g = e.game
    return LibraryEntryType(
        id=e.id,
        platform=e.platform,
        status=e.status,
        custom_folder=e.custom_folder,
        playtime_minutes=e.playtime_minutes,
        is_favorite=e.is_favorite,
        last_played_at=e.last_played_at,
        added_at=e.added_at,
        achievements_unlocked=e.achievements_unlocked,
        achievements_total=e.achievements_total,
        game=GameType(
            id=g.id,
            title=g.title,
            igdb_id=g.igdb_id,
            steam_appid=g.steam_appid,
            cover_url=g.cover_url,
            summary=g.summary,
            release_date=g.release_date,
            genres=list(g.genres or []),
        ),
    )


@strawberry.type
class Query:
    @strawberry.field(description="Your library, or a public user's library when username is set")
    async def library(
        self,
        info: strawberry.Info[Context, None],
        username: str | None = None,
        filter: LibraryFilter | None = None,
        sort: LibrarySort | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> LibraryPageType:
        ctx = info.context
        if username:
            try:
                owner = await get_visible_user(ctx.db, username, ctx.user)
            except HTTPException as e:
                raise PermissionError("User not found") from e
        elif ctx.user is None:
            raise PermissionError("Not authenticated")
        else:
            owner = ctx.user

        limit = max(1, min(limit, 200))
        base = apply_filter(
            select(LibraryEntry).join(Game).where(LibraryEntry.user_id == owner.id), filter
        )
        total = await ctx.db.scalar(select(func.count()).select_from(base.subquery()))

        sort = sort or LibrarySort()
        column = _SORT_COLUMNS[sort.field]
        order = (
            desc(column).nulls_last()
            if sort.direction == SortDirection.DESC
            else asc(column).nulls_last()
        )
        rows = await ctx.db.scalars(
            base.order_by(order, LibraryEntry.id).limit(limit).offset(max(offset, 0))
        )
        return LibraryPageType(items=[_to_type(e) for e in rows.unique()], total=total or 0)

    @strawberry.field(description="Distinct custom folder names used in your 'Other' category")
    async def custom_folders(self, info: strawberry.Info[Context, None]) -> list[str]:
        ctx = info.context
        if ctx.user is None:
            raise PermissionError("Not authenticated")
        rows = await ctx.db.scalars(
            select(LibraryEntry.custom_folder)
            .where(LibraryEntry.user_id == ctx.user.id, LibraryEntry.custom_folder.is_not(None))
            .distinct()
            .order_by(LibraryEntry.custom_folder)
        )
        return list(rows)


schema = strawberry.Schema(query=Query)
graphql_router = GraphQLRouter(schema, context_getter=get_context)
