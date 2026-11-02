"""Parse manual JSON/CSV exports (Epic, GOG, Amazon, ...) into a common shape.

Accepted shapes (keys are case-insensitive):
- JSON: a list of objects, or {"games": [...]}
- CSV: a header row
Recognised columns: title|name|game, playtime_minutes|playtime|minutes,
playtime_hours|hours, status, last_played.
"""

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime

from app.models.enums import GameStatus

MAX_ROWS = 10_000

_TITLE_KEYS = ("title", "name", "game", "game_name", "product_title")
_MINUTES_KEYS = ("playtime_minutes", "playtime", "minutes", "playtime_forever")
_HOURS_KEYS = ("playtime_hours", "hours", "hours_played")
_STATUS_ALIASES = {
    "backlog": GameStatus.BACKLOG,
    "pending": GameStatus.BACKLOG,
    "playing": GameStatus.PLAYING,
    "in progress": GameStatus.PLAYING,
    "completed": GameStatus.COMPLETED,
    "finished": GameStatus.COMPLETED,
    "beaten": GameStatus.COMPLETED,
    "dropped": GameStatus.DROPPED,
    "abandoned": GameStatus.DROPPED,
    "wishlist": GameStatus.WISHLIST,
    "other": GameStatus.OTHER,
}


class ImportFormatError(ValueError):
    pass


@dataclass
class ImportedGame:
    title: str
    playtime_minutes: int = 0
    status: GameStatus | None = None
    last_played_at: datetime | None = None


def _first(row: dict, keys: tuple[str, ...]):
    for k in keys:
        value = row.get(k)
        if value not in (None, ""):
            return value
    return None


def _to_number(value) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _parse_dt(value) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)
    except ValueError:
        return None


def _row_to_game(raw: dict) -> ImportedGame | None:
    row = {str(k).strip().lower(): v for k, v in raw.items()}
    title = _first(row, _TITLE_KEYS)
    if not title or not str(title).strip():
        return None

    minutes = _first(row, _MINUTES_KEYS)
    hours = _first(row, _HOURS_KEYS)
    playtime = (
        int(_to_number(minutes))
        if minutes is not None
        else int(round(_to_number(hours) * 60))
        if hours is not None
        else 0
    )

    status_raw = row.get("status")
    status = _STATUS_ALIASES.get(str(status_raw).strip().lower()) if status_raw else None

    return ImportedGame(
        title=str(title).strip()[:255],
        playtime_minutes=max(playtime, 0),
        status=status,
        last_played_at=_parse_dt(row.get("last_played")),
    )


def _parse_json(text: str) -> list[dict]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ImportFormatError(f"Invalid JSON: {e.msg}") from e
    if isinstance(data, dict):
        data = data.get("games") or data.get("library") or data.get("items")
    if not isinstance(data, list):
        raise ImportFormatError("JSON must be a list of games or an object with a 'games' list")
    return [r for r in data if isinstance(r, dict)]


def _parse_csv(text: str) -> list[dict]:
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(text), dialect=dialect))


def parse_import_file(filename: str, content: bytes) -> list[ImportedGame]:
    text = content.decode("utf-8-sig", errors="replace")
    name = filename.lower()
    if name.endswith(".json"):
        rows = _parse_json(text)
    elif name.endswith(".csv") or name.endswith(".tsv"):
        rows = _parse_csv(text)
    else:
        rows = _parse_json(text) if text.lstrip().startswith(("[", "{")) else _parse_csv(text)

    if len(rows) > MAX_ROWS:
        raise ImportFormatError(f"Too many rows (max {MAX_ROWS})")

    games: dict[str, ImportedGame] = {}
    for raw in rows:
        game = _row_to_game(raw)
        if game:
            games.setdefault(game.title.lower(), game)  # de-duplicate within the file
    if not games:
        raise ImportFormatError("No games found. Expected a 'title' or 'name' column.")
    return list(games.values())
