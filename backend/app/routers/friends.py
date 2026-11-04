from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ratelimit import hit
from app.core.redis import get_redis
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Friendship, FriendshipStatus, User
from app.schemas.friends import FriendOut, FriendRequestCreate, FriendsOverview
from app.schemas.user import UserSummary
from app.services import friends

router = APIRouter(prefix="/friends", tags=["friends"])


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _out(f: Friendship, other: User) -> FriendOut:
    return FriendOut(
        id=f.id,
        user=UserSummary.model_validate(other),
        created_at=f.created_at,
        accepted_at=f.accepted_at,
    )


async def _own(db: AsyncSession, friendship_id: int, user: User) -> Friendship:
    f = await db.get(Friendship, friendship_id)
    if f is None or user.id not in (f.requester_id, f.addressee_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friendship not found")
    return f


@router.get("", response_model=FriendsOverview)
async def list_friends(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(Friendship).where(friends.involving(user.id)))).all()
    other_id = {f.id: friends.other_id(f, user.id) for f in rows}
    others = {u.id: u for u in await db.scalars(select(User).where(User.id.in_(other_id.values())))}
    result = FriendsOverview(friends=[], incoming=[], outgoing=[])
    for f in rows:
        getattr(result, friends.state_for(f, user.id)).append(_out(f, others[other_id[f.id]]))
    result.friends.sort(key=lambda x: x.user.username.lower())
    result.incoming.sort(key=lambda x: x.created_at, reverse=True)
    result.outgoing.sort(key=lambda x: x.created_at, reverse=True)
    return result


@router.post("/requests", response_model=FriendOut, status_code=status.HTTP_201_CREATED)
async def send_request(
    body: FriendRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Send a request. If that user had already sent you one, it is accepted instead."""
    await hit(redis, f"friends:user:{user.id}", limit=30, window_seconds=3600)
    other = await db.scalar(
        select(User).where(func.lower(User.username) == body.username.strip().lower())
    )
    if other is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if other.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes añadirte a ti mismo.")

    f = await friends.get_between(db, user.id, other.id)
    if f is None:
        f = Friendship(requester_id=user.id, addressee_id=other.id)
        db.add(f)
    elif f.status == FriendshipStatus.PENDING and f.addressee_id == user.id:
        f.status = FriendshipStatus.ACCEPTED
        f.accepted_at = _now()
    elif f.status == FriendshipStatus.ACCEPTED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya sois amigos.")
    else:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya le enviaste una solicitud.")
    await db.commit()
    await db.refresh(f)
    return _out(f, other)


@router.post("/{friendship_id}/accept", response_model=FriendOut)
async def accept_request(
    friendship_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await _own(db, friendship_id, user)
    if f.addressee_id != user.id or f.status != FriendshipStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "No hay ninguna solicitud que aceptar.")
    f.status = FriendshipStatus.ACCEPTED
    f.accepted_at = _now()
    await db.commit()
    return _out(f, await db.get(User, f.requester_id))


@router.delete("/{friendship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(
    friendship_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject or cancel a request, or remove a friend."""
    await db.delete(await _own(db, friendship_id, user))
    await db.commit()
