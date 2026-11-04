from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class AdminOverview(BaseModel):
    users: int
    active_users_30d: int
    steam_users: int
    games: int
    games_without_metadata: int
    library_entries: int
    failed_jobs_24h: int


class AdminUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    avatar_url: str | None
    role: UserRole
    is_public: bool
    steam_id: str | None
    created_at: datetime
    last_seen_at: datetime | None
    games: int


class AdminUserPage(BaseModel):
    items: list[AdminUser]
    total: int


class AdminUserUpdate(BaseModel):
    role: UserRole


class EnqueuedOut(BaseModel):
    enqueued: int
