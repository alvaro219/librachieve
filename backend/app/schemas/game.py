from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    igdb_id: int | None
    steam_appid: int | None
    cover_url: str | None
    summary: str | None
    release_date: date | None
    genres: list[str]
    igdb_rating: float | None = None
    igdb_rating_count: int | None = None
    critic_rating: float | None = None
    critic_rating_count: int | None = None
    community_rating: float | None = None
    community_rating_count: int = 0


class RatingIn(BaseModel):
    score: int = Field(ge=0, le=100)


class RatingOut(BaseModel):
    score: int | None
    community_rating: float | None
    community_rating_count: int


class IgdbSearchResult(BaseModel):
    igdb_id: int
    title: str
    cover_url: str | None
    release_date: date | None
    genres: list[str]
    summary: str | None
    igdb_rating: float | None = None
    igdb_rating_count: int | None = None
    critic_rating: float | None = None
    critic_rating_count: int | None = None
