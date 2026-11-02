from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Platform, SyncJobStatus, pg_enum


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
