from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import GameStatus, Platform
from app.schemas.game import GameOut


class LibraryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: Platform
    status: GameStatus
    custom_folder: str | None
    playtime_minutes: int
    is_favorite: bool
    last_played_at: datetime | None
    added_at: datetime
    achievements_unlocked: int
    achievements_total: int
    game: GameOut


class AchievementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    icon_url: str | None
    icon_locked_url: str | None
    hidden: bool
    global_percent: float | None
    unlocked: bool
    unlocked_at: datetime | None


class LibraryEntryCreate(BaseModel):
    """Add a game either by catalogue id, IGDB id, or plain title."""

    game_id: int | None = None
    igdb_id: int | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    platform: Platform = Platform.OTHER
    status: GameStatus = GameStatus.BACKLOG
    custom_folder: str | None = Field(None, max_length=64)
    playtime_minutes: int = Field(0, ge=0)

    @model_validator(mode="after")
    def _one_identifier(self):
        if not (self.game_id or self.igdb_id or self.title):
            raise ValueError("Provide game_id, igdb_id or title")
        return self


class LibraryEntryUpdate(BaseModel):
    status: GameStatus | None = None
    is_favorite: bool | None = None
    custom_folder: str | None = Field(None, max_length=64)
    playtime_minutes: int | None = Field(None, ge=0)


class LibraryPage(BaseModel):
    items: list[LibraryEntryOut]
    total: int
