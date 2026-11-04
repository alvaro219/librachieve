from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ratelimit import hit
from app.core.redis import get_redis
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.deps import get_current_user, get_optional_user
from app.models import Friendship, User, UserRole
from app.schemas.user import (
    PasswordChange,
    UserMe,
    UserPublic,
    UserSearchResult,
    UserStats,
    UserUpdate,
)
from app.services import friends
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


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChange,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Change the password, or set a first one on a Steam-only account."""
    await hit(redis, f"password:user:{user.id}", limit=10, window_seconds=900)
    if user.password_hash and not (
        body.current_password and verify_password(body.current_password, user.password_hash)
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La contraseña actual no es correcta.")
    user.password_hash = hash_password(body.new_password)
    await db.commit()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.delete(user)
    await db.commit()


@router.get("/me/stats", response_model=UserStats)
async def my_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await compute_user_stats(db, user.id)


@router.get("/search", response_model=list[UserSearchResult])
async def search_users(
    q: str = Query(min_length=2, max_length=32),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Public profiles whose name contains `q`; a private one only by its exact name
    (so friends can still find each other) or if it is already a friend or request."""
    term = q.strip().lower()
    # "_" and "%" are LIKE wildcards ("_" is valid in usernames): match them literally
    escaped = term.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    related = (
        select(Friendship.requester_id)
        .where(friends.involving(user.id))
        .union(select(Friendship.addressee_id).where(friends.involving(user.id)))
    )
    name = func.lower(User.username)
    rows = (
        await db.scalars(
            select(User)
            .where(
                User.id != user.id,
                name.like(f"%{escaped}%", escape="!"),
                or_(User.is_public, name == term, User.id.in_(related)),
            )
            # Exact match first, then names starting with the term
            .order_by((name == term).desc(), name.like(f"{escaped}%", escape="!").desc(), name)
            .limit(20)
        )
    ).all()
    links = {
        friends.other_id(f, user.id): f
        for f in await db.scalars(
            select(Friendship).where(
                friends.involving(user.id),
                or_(
                    Friendship.requester_id.in_([u.id for u in rows]),
                    Friendship.addressee_id.in_([u.id for u in rows]),
                ),
            )
        )
    }
    return [
        UserSearchResult.model_validate(u).model_copy(
            update={
                "friendship": friends.state_for(links.get(u.id), user.id),
                "friendship_id": links[u.id].id if u.id in links else None,
            }
        )
        for u in rows
    ]


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
