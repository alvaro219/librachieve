from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    avatar_url: str | None
    is_public: bool
    created_at: datetime


class UserMe(UserPublic):
    email: str | None
    role: UserRole
    steam_id: str | None
    # Steam-only accounts have none until they set one
    has_password: bool


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_\-]+$")
    is_public: bool | None = None


class PasswordChange(BaseModel):
    # Required when the account already has a password
    current_password: str | None = None
    new_password: str = Field(min_length=8, max_length=128)


FriendState = Literal["none", "friends", "outgoing", "incoming"]


class UserSummary(BaseModel):
    """What other users see of someone in search results and friend lists."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    avatar_url: str | None
    is_public: bool


class UserSearchResult(UserSummary):
    friendship: FriendState = "none"
    friendship_id: int | None = None


class GenreStat(BaseModel):
    genre: str
    playtime_minutes: int
    games: int


class PlatformStat(BaseModel):
    platform: str
    games: int


class UserStats(BaseModel):
    total_games: int
    total_playtime_minutes: int
    completed_games: int
    completion_ratio: float = Field(description="completed / owned (wishlist excluded), 0..1")
    games_by_status: dict[str, int]
    achievements_unlocked: int
    achievements_total: int
    perfect_games: int = Field(description="Games with every achievement unlocked")
    top_genres: list[GenreStat]
    games_by_platform: list[PlatformStat]
