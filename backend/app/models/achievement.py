from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Platform, pg_enum


class Achievement(Base):
    """An achievement definition for a game on a platform (shared by all users)."""

    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("game_id", "platform", "api_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    platform: Mapped[Platform] = mapped_column(pg_enum(Platform, "platform"))
    api_name: Mapped[str] = mapped_column(String(255))
    # English (Steam's default); the UI languages are in `localized`
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    # {"es": {"name": ..., "description": ...}, "fr": {...}, "en": {...}}
    localized: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    icon_url: Mapped[str | None] = mapped_column(String(512))
    icon_locked_url: Mapped[str | None] = mapped_column(String(512))
    hidden: Mapped[bool] = mapped_column(default=False, server_default="false")
    # Share of all players who unlocked it (0..100), from the platform's global stats
    global_percent: Mapped[float | None]
    display_order: Mapped[int] = mapped_column(default=0, server_default="0")

    def text_in(self, lang: str) -> tuple[str, str | None]:
        """Name and description in `lang`, falling back to English."""
        texts = (self.localized or {}).get(lang) or {}
        return texts.get("name") or self.name, texts.get("description") or self.description


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    achievement_id: Mapped[int] = mapped_column(
        ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    unlocked_at: Mapped[datetime | None]
