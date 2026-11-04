import enum

from sqlalchemy import Enum


class UserRole(enum.StrEnum):
    USER = "user"
    ADMIN = "admin"


class GameStatus(enum.StrEnum):
    BACKLOG = "backlog"
    PLAYING = "playing"
    COMPLETED = "completed"
    DROPPED = "dropped"
    WISHLIST = "wishlist"
    OTHER = "other"


class Platform(enum.StrEnum):
    STEAM = "steam"
    EPIC = "epic"
    GOG = "gog"
    AMAZON = "amazon"
    OTHER = "other"


class SyncJobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    REVERTED = "reverted"  # a file import the user undid


class FriendshipStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"


def pg_enum(enum_cls: type[enum.Enum], name: str) -> Enum:
    """Native Postgres enum that stores the lowercase values, not the member names."""
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])
