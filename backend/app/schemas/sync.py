from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Platform, SyncJobStatus


class SyncJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: Platform
    status: SyncJobStatus
    imported_count: int
    error: str | None
    created_at: datetime
    finished_at: datetime | None
    automatic: bool = False
    # True only for the most recent completed file import (undo works like a stack)
    undoable: bool = False
