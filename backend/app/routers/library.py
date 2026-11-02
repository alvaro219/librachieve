import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_db
from app.deps import get_current_user, get_optional_user
from app.models import Achievement, Game, GameStatus, LibraryEntry, Platform, User, UserAchievement
from app.routers.users import can_view
from app.schemas.library import (
    AchievementOut,
    LibraryEntryCreate,
    LibraryEntryOut,
    LibraryEntryUpdate,
    LibraryPage,
)
from app.services import igdb
from app.services.catalog import get_or_create_game, upsert_library_entry
from app.services.queue import get_queue

router = APIRouter(prefix="/library", tags=["library"])


@router.get("", response_model=LibraryPage)
async def list_library(
    status_: GameStatus | None = Query(None, alias="status"),
    platform: Platform | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Simple listing. For advanced filtering/sorting use the GraphQL `library` query."""
    filters = [LibraryEntry.user_id == user.id]
    if status_:
        filters.append(LibraryEntry.status == status_)
    if platform:
        filters.append(LibraryEntry.platform == platform)

    total = await db.scalar(select(func.count()).select_from(LibraryEntry).where(*filters))
    items = await db.scalars(
        select(LibraryEntry)
        .join(Game)
        .where(*filters)
        .order_by(Game.title)
        .limit(limit)
        .offset(offset)
    )
    return LibraryPage(items=list(items.unique()), total=total or 0)


async def _get_own_entry(db: AsyncSession, entry_id: int, user: User) -> LibraryEntry:
    entry = await db.get(LibraryEntry, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Library entry not found")
    return entry


@router.post("", response_model=LibraryEntryOut, status_code=status.HTTP_201_CREATED)
async def add_to_library(
    body: LibraryEntryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    needs_enrichment = False
    if body.game_id:
        game = await db.get(Game, body.game_id)
        if game is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    elif body.igdb_id:
        try:
            meta = await igdb.get_by_id(redis, body.igdb_id)
        except igdb.IgdbNotConfigured as e:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e
        except httpx.HTTPError as e:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "IGDB request failed") from e
        if meta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "IGDB game not found")
        game = await get_or_create_game(db, meta.title, igdb_id=meta.igdb_id)
        if game.igdb_id is None:
            game.igdb_id = meta.igdb_id
        igdb.apply_metadata(game, meta)
    else:
        game = await get_or_create_game(db, body.title)
        needs_enrichment = game.metadata_updated_at is None

    entry, created = await upsert_library_entry(
        db,
        user_id=user.id,
        game=game,
        platform=body.platform,
        playtime_minutes=body.playtime_minutes,
        status=body.status,
    )
    if not created:
        raise HTTPException(status.HTTP_409_CONFLICT, "Game already in library on that platform")
    entry.custom_folder = body.custom_folder if body.status == GameStatus.OTHER else None
    await db.commit()
    await db.refresh(entry, ["game"])

    if needs_enrichment:
        await (await get_queue()).enqueue_job("enrich_games", [game.id])
    return entry


@router.patch("/{entry_id}", response_model=LibraryEntryOut)
async def update_entry(
    entry_id: int,
    body: LibraryEntryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_own_entry(db, entry_id, user)
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(entry, field, value)
    if entry.status != GameStatus.OTHER:
        entry.custom_folder = None
    await db.commit()
    await db.refresh(entry, ["game", "updated_at"])
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_own_entry(db, entry_id, user)
    await db.delete(entry)
    await db.commit()


@router.get("/{entry_id}/achievements", response_model=list[AchievementOut])
async def list_achievements(
    entry_id: int,
    viewer: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Achievements of a library entry: your own, or one from a public profile."""
    entry = await db.get(LibraryEntry, entry_id)
    owner = await db.get(User, entry.user_id) if entry else None
    if entry is None or owner is None or not can_view(viewer, owner):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Library entry not found")

    rows = await db.execute(
        select(Achievement, UserAchievement.unlocked_at, UserAchievement.user_id.is_not(None))
        .outerjoin(
            UserAchievement,
            (UserAchievement.achievement_id == Achievement.id)
            & (UserAchievement.user_id == entry.user_id),
        )
        .where(Achievement.game_id == entry.game_id, Achievement.platform == entry.platform)
        .order_by(Achievement.display_order)
    )
    return [
        AchievementOut(
            id=a.id,
            name=a.name,
            description=a.description,
            icon_url=a.icon_url,
            icon_locked_url=a.icon_locked_url,
            hidden=a.hidden,
            global_percent=a.global_percent,
            unlocked=bool(unlocked),
            unlocked_at=unlocked_at,
        )
        for a, unlocked_at, unlocked in rows
    ]
