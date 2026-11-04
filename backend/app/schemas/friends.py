from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserSummary


class FriendRequestCreate(BaseModel):
    username: str = Field(min_length=1, max_length=32)


class FriendOut(BaseModel):
    """A friendship or request, seen from the current user's side."""

    id: int
    user: UserSummary
    created_at: datetime
    accepted_at: datetime | None


class FriendsOverview(BaseModel):
    friends: list[FriendOut]
    incoming: list[FriendOut]
    outgoing: list[FriendOut]
