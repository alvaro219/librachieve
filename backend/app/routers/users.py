from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user, get_optional_user, require_admin
from app.models import User, UserRole
from app.schemas.user import UserMe, UserPublic, UserStats, UserUpdate
from app.services.stats import compute_user_stats

router = APIRouter(prefix="/users", tags=["users"])


def can_view(viewer: User | None, owner: User) -> bool:
    return owner.is_public or (
        viewer is not None and (viewer.id == owner.id or viewer.role == UserRole.ADMIN)
    )


async def get_visible_user(db: AsyncSession, username: str, viewer: User | None) -> User:
    owner = await db.scalar(select(User).where(func.lower(User.username) == username.lower()))
    # Private profiles answer 404, not 403, so their existence isn't revealed.
    if owner is None or not can_view(viewer, owner):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return owner


@router.get("/me", response_model=UserMe)
async def read_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserMe)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.username and body.username.lower() != user.username.lower():
        taken = await db.scalar(
            select(User.id).where(func.lower(User.username) == body.username.lower())
        )
        if taken:
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already in use")
    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.delete(user)
    await db.commit()


@router.get("/me/stats", response_model=UserStats)
async def my_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await compute_user_stats(db, user.id)


@router.get("", response_model=list[UserMe], dependencies=[Depends(require_admin)])
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return (await db.scalars(select(User).order_by(User.id).limit(limit).offset(offset))).all()


@router.get("/{username}", response_model=UserPublic)
async def read_profile(
    username: str,
    viewer: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_visible_user(db, username, viewer)


@router.get("/{username}/stats", response_model=UserStats)
async def profile_stats(
    username: str,
    viewer: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    owner = await get_visible_user(db, username, viewer)
    return await compute_user_stats(db, owner.id)
