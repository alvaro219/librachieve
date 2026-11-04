import logging
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import describe_error
from app.core.ratelimit import hit
from app.core.redis import get_redis
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Friendship, FriendshipStatus, User
from app.schemas.friends import (
    FriendOut,
    FriendRequestCreate,
    FriendsOverview,
    SteamFriendsAdded,
)
from app.schemas.user import UserSearchResult, UserSummary
from app.services import friends, steam

router = APIRouter(prefix="/friends", tags=["friends"])
logger = logging.getLogger(__name__)


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


async def _steam_friends_here(db: AsyncSession, redis: Redis, user: User) -> list[User]:
    """Librachieve users who are the current user's friends on Steam."""
    if not user.steam_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vincula tu cuenta de Steam primero.")
    await hit(redis, f"steam-friends:user:{user.id}", limit=30, window_seconds=3600)
    try:
        ids = await steam.get_friend_ids(user.steam_id)
    except steam.SteamProfilePrivate as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
    except (steam.SteamError, httpx.HTTPError) as e:
        logger.warning("Steam friend list failed for user %s: %s", user.id, describe_error(e))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Steam no responde. Prueba otra vez en un rato."
        ) from e
    if not ids:
        return []
    rows = await db.scalars(
        select(User).where(User.steam_id.in_(ids), User.id != user.id).order_by(User.username)
    )
    return list(rows)


@router.get("/steam", response_model=list[UserSearchResult])
async def steam_friends(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Your Steam friends who use Librachieve, with how you relate to each here."""
    found = await _steam_friends_here(db, redis, user)
    links = {
        friends.other_id(f, user.id): f
        for f in await db.scalars(select(Friendship).where(friends.involving(user.id)))
    }
    return [
        UserSearchResult.model_validate(u).model_copy(
            update={
                "friendship": friends.state_for(links.get(u.id), user.id),
                "friendship_id": links[u.id].id if u.id in links else None,
            }
        )
        for u in found
    ]


@router.post("/steam", response_model=SteamFriendsAdded)
async def add_steam_friends(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Befriend every Steam friend who uses Librachieve, without a request: the friendship
    is already mutual on Steam (checked with Steam's API, not taken from the client)."""
    added = 0
    for other in await _steam_friends_here(db, redis, user):
        f = await friends.get_between(db, user.id, other.id)
        if f is None:
            f = Friendship(requester_id=user.id, addressee_id=other.id)
            db.add(f)
        elif f.status == FriendshipStatus.ACCEPTED:
            continue
        f.status = FriendshipStatus.ACCEPTED
        f.accepted_at = _now()
        added += 1
    await db.commit()
    return SteamFriendsAdded(added=added)


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
