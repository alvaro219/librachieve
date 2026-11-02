from datetime import date

from pydantic import BaseModel, ConfigDict


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


class IgdbSearchResult(BaseModel):
    igdb_id: int
    title: str
    cover_url: str | None
    release_date: date | None
    genres: list[str]
    summary: str | None
