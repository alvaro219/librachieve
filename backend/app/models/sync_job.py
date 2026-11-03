from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import GameStatus, Platform, SyncJobStatus, pg_enum


class SyncJob(Base):
    """Tracks a platform import so the frontend can poll its progress."""

    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform: Mapped[Platform] = mapped_column(pg_enum(Platform, "platform"))
    status: Mapped[SyncJobStatus] = mapped_column(
        pg_enum(SyncJobStatus, "sync_job_status"),
        default=SyncJobStatus.PENDING,
        server_default=SyncJobStatus.PENDING.value,
    )
    imported_count: Mapped[int] = mapped_column(default=0, server_default="0")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None]


class SyncJobChange(Base):
    """What a file import did to one library entry, so the import can be undone.

    `created` entries are deleted on undo; otherwise the previous values are restored.
    entry_id has no FK on purpose: the user may delete the entry later and undo just skips it.
    """

    __tablename__ = "sync_job_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("sync_jobs.id", ondelete="CASCADE"), index=True)
    entry_id: Mapped[int]
    created: Mapped[bool]
    prev_status: Mapped[GameStatus | None] = mapped_column(pg_enum(GameStatus, "game_status"))
    prev_playtime_minutes: Mapped[int | None]
    prev_last_played_at: Mapped[datetime | None]
    prev_is_favorite: Mapped[bool | None]
    prev_custom_folder: Mapped[str | None] = mapped_column(String(64))
