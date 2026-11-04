from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import require_admin
from app.models import Game, LibraryEntry, SyncJob, SyncJobStatus, User
from app.schemas.admin import AdminOverview, AdminUser, AdminUserPage, AdminUserUpdate, EnqueuedOut
from app.services.queue import get_queue

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _ago(**delta: float) -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(**delta)


async def _count(db: AsyncSession, model, *where) -> int:
    return await db.scalar(select(func.count()).select_from(model).where(*where))


def _admin_user(user: User, games: int) -> AdminUser:
    fields = {f: getattr(user, f) for f in AdminUser.model_fields if f != "games"}
    return AdminUser(**fields, games=games)


@router.get("/overview", response_model=AdminOverview)
async def overview(db: AsyncSession = Depends(get_db)):
    return AdminOverview(
        users=await _count(db, User),
        active_users_30d=await _count(db, User, User.last_seen_at >= _ago(days=30)),
        steam_users=await _count(db, User, User.steam_id.is_not(None)),
        games=await _count(db, Game),
        games_without_metadata=await _count(db, Game, Game.igdb_id.is_(None)),
        library_entries=await _count(db, LibraryEntry),
        failed_jobs_24h=await _count(
            db, SyncJob, SyncJob.status == SyncJobStatus.FAILED, SyncJob.created_at >= _ago(days=1)
        ),
    )


@router.get("/users", response_model=AdminUserPage)
async def list_users(
    q: str = Query("", max_length=255),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    where = []
    if term := q.strip().lower():
        like = f"%{term}%"
        where.append(or_(func.lower(User.username).like(like), func.lower(User.email).like(like)))
    games = (
        select(func.count())
        .where(LibraryEntry.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    rows = await db.execute(
        select(User, games).where(*where).order_by(User.id.desc()).limit(limit).offset(offset)
    )
    return AdminUserPage(
        items=[_admin_user(u, n) for u, n in rows.all()],
        total=await _count(db, User, *where),
    )


async def _target(db: AsyncSession, user_id: int, admin: User) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == admin.id:
        # Avoids locking yourself out by accident; the CLI can still do it
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No puedes modificar tu propia cuenta aquí."
        )
    return user


@router.patch("/users/{user_id}", response_model=AdminUser)
async def update_user(
    user_id: int,
    body: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await _target(db, user_id, admin)
    user.role = body.role
    await db.commit()
    return _admin_user(user, await _count(db, LibraryEntry, LibraryEntry.user_id == user.id))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    await db.delete(await _target(db, user_id, admin))
    await db.commit()


@router.post("/reenrich", response_model=EnqueuedOut)
async def reenrich_missing(db: AsyncSession = Depends(get_db)):
    """Retry the IGDB match for every game that still has no metadata."""
    ids = list(await db.scalars(select(Game.id).where(Game.igdb_id.is_(None))))
    if ids:
        await (await get_queue()).enqueue_job("enrich_games", ids)
    return EnqueuedOut(enqueued=len(ids))
