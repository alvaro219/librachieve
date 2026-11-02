from datetime import date, datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Game(Base):
    """Shared game catalogue. One row per real game, independent of who owns it."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    normalized_title: Mapped[str] = mapped_column(String(255), index=True)
    igdb_id: Mapped[int | None] = mapped_column(unique=True)
    steam_appid: Mapped[int | None] = mapped_column(unique=True)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    summary: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None]
    genres: Mapped[list[str]] = mapped_column(ARRAY(String(64)), default=list, server_default="{}")
    metadata_updated_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
