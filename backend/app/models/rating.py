from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GameRating(Base):
    """A user's 0-100 score for a game (one per game, whatever store it is owned on)."""

    __tablename__ = "game_ratings"
    __table_args__ = (CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    score: Mapped[int]
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
