from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import FriendshipStatus, pg_enum


class Friendship(Base):
    """A friend request (pending) or a friendship (accepted). One row per pair of users."""

    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id"),
        CheckConstraint("requester_id <> addressee_id", name="not_self"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    addressee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[FriendshipStatus] = mapped_column(
        pg_enum(FriendshipStatus, "friendship_status"),
        default=FriendshipStatus.PENDING,
        server_default=FriendshipStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    accepted_at: Mapped[datetime | None]
