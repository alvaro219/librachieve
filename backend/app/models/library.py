from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import GameStatus, Platform, pg_enum


class LibraryEntry(Base):
    """A game in a user's library, on a given platform."""

    __tablename__ = "library_entries"
    __table_args__ = (UniqueConstraint("user_id", "game_id", "platform"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    platform: Mapped[Platform] = mapped_column(pg_enum(Platform, "platform"))
    status: Mapped[GameStatus] = mapped_column(
        pg_enum(GameStatus, "game_status"),
        default=GameStatus.BACKLOG,
        server_default=GameStatus.BACKLOG.value,
        index=True,
    )
    # Free-form folder name, only meaningful when status == OTHER
    custom_folder: Mapped[str | None] = mapped_column(String(64))
    playtime_minutes: Mapped[int] = mapped_column(default=0, server_default="0")
    last_played_at: Mapped[datetime | None]
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="library_entries")
    game = relationship("Game", lazy="joined")
