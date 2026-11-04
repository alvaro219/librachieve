from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Friendship, FriendshipStatus
from app.schemas.user import FriendState


def involving(user_id: int):
    return or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id)


def between(a: int, b: int):
    return or_(
        and_(Friendship.requester_id == a, Friendship.addressee_id == b),
        and_(Friendship.requester_id == b, Friendship.addressee_id == a),
    )


async def get_between(db: AsyncSession, a: int, b: int) -> Friendship | None:
    return await db.scalar(select(Friendship).where(between(a, b)))


def state_for(f: Friendship | None, viewer_id: int) -> FriendState:
    if f is None:
        return "none"
    if f.status == FriendshipStatus.ACCEPTED:
        return "friends"
    return "outgoing" if f.requester_id == viewer_id else "incoming"


def other_id(f: Friendship, user_id: int) -> int:
    return f.addressee_id if f.requester_id == user_id else f.requester_id
