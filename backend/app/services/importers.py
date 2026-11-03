"""Parse manual JSON/CSV exports (Epic, GOG, Amazon, ...) into a common shape.

Accepted shapes (keys are case-insensitive):
- JSON: a list of objects, or {"games": [...]}
- CSV: a header row
Only a title column is required; every other column is optional and applied when present.
Column names are matched in English and Spanish (Playnite exports use the UI language):
- title: title | name | game | nombre | título | juego
- playtime: playtime_minutes | playtime | minutes  (minutes)
            playtime_seconds | seconds | tiempo jugado | time played  (seconds, as Playnite)
            playtime_hours | hours | horas  (hours)
- status: status | estado | completion status | estado de finalización
- store per row: source | sourcename | store | platform | fuente | origen | plataforma | tienda
- last_played | last activity | última actividad, favorite | favorito, steamappid
"""

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime

from app.models.enums import GameStatus, Platform

MAX_ROWS = 10_000

_TITLE_KEYS = (
    "title",
    "name",
    "game",
    "game_name",
    "product_title",
    "nombre",
    "título",
    "titulo",
    "juego",
)
_MINUTES_KEYS = ("playtime_minutes", "playtime", "minutes", "playtime_forever", "minutos")
_HOURS_KEYS = ("playtime_hours", "hours", "hours_played", "horas", "horas jugadas")
# Playnite stores playtime in seconds; its CSV header is "Tiempo Jugado" / "Time Played"
_SECONDS_KEYS = ("playtime_seconds", "seconds", "segundos", "tiempo jugado", "time played")
_STATUS_KEYS = (
    "status",
    "estado",
    "completion status",
    "completionstatus",
    "estado de finalización",
    "estado de finalizacion",
)
_LAST_PLAYED_KEYS = (
    "last_played",
    "last played",
    "last activity",
    "lastactivity",
    "última actividad",
    "ultima actividad",
)
_FAVORITE_KEYS = ("favorite", "favourite", "favorito", "is_favorite")
_SOURCE_KEYS = (
    "source",
    "sourcename",
    "source_name",
    "store",
    "platform",
    "launcher",
    "fuente",
    "origen",
    "plataforma",
    "tienda",
)
_STEAM_ID_KEYS = ("steamappid", "steam_appid", "steam_app_id", "appid")
_TRUE = {"true", "1", "yes", "y", "si", "sí", "x"}
# Store names as written by Playnite, Heroic and the launchers themselves
_PLATFORM_ALIASES = {
    "steam": Platform.STEAM,
    "epic": Platform.EPIC,
    "epic games": Platform.EPIC,
    "epic games store": Platform.EPIC,
    "legendary": Platform.EPIC,
    "gog": Platform.GOG,
    "gog.com": Platform.GOG,
    "gog galaxy": Platform.GOG,
    "amazon": Platform.AMAZON,
    "amazon games": Platform.AMAZON,
    "prime gaming": Platform.AMAZON,
    "nile": Platform.AMAZON,
}
# Includes Playnite's default completion statuses in English and Spanish.
# "Played" / "On Hold" = started but unfinished, so they stay in the backlog.
_STATUS_ALIASES = {
    "backlog": GameStatus.BACKLOG,
    "pending": GameStatus.BACKLOG,
    "pendiente": GameStatus.BACKLOG,
    "not played": GameStatus.BACKLOG,
    "sin jugar": GameStatus.BACKLOG,
    "no jugado": GameStatus.BACKLOG,
    "plan to play": GameStatus.BACKLOG,
    "planeado": GameStatus.BACKLOG,
    "por jugar": GameStatus.BACKLOG,
    "played": GameStatus.BACKLOG,
    "jugado": GameStatus.BACKLOG,
    "on hold": GameStatus.BACKLOG,
    "en espera": GameStatus.BACKLOG,
    "en pausa": GameStatus.BACKLOG,
    "playing": GameStatus.PLAYING,
    "jugando": GameStatus.PLAYING,
    "in progress": GameStatus.PLAYING,
    "en progreso": GameStatus.PLAYING,
    "completed": GameStatus.COMPLETED,
    "completado": GameStatus.COMPLETED,
    "finished": GameStatus.COMPLETED,
    "terminado": GameStatus.COMPLETED,
    "beaten": GameStatus.COMPLETED,
    "superado": GameStatus.COMPLETED,
    "dropped": GameStatus.DROPPED,
    "abandoned": GameStatus.DROPPED,
    "abandonado": GameStatus.DROPPED,
    "wishlist": GameStatus.WISHLIST,
    "deseado": GameStatus.WISHLIST,
    "other": GameStatus.OTHER,
    "otro": GameStatus.OTHER,
}


class ImportFormatError(ValueError):
    pass


@dataclass
class ImportedGame:
    title: str
    playtime_minutes: int = 0
    status: GameStatus | None = None
    last_played_at: datetime | None = None
    # Per-row store; None means "use the platform chosen for the whole import"
    platform: Platform | None = None
    is_favorite: bool = False
    steam_appid: int | None = None


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
    seconds = _first(row, _SECONDS_KEYS)
    hours = _first(row, _HOURS_KEYS)
    if minutes is not None:
        playtime = int(_to_number(minutes))
    elif seconds is not None:
        playtime = int(_to_number(seconds) // 60)
    elif hours is not None:
        playtime = int(round(_to_number(hours) * 60))
    else:
        playtime = 0

    source = _first(row, _SOURCE_KEYS)
    platform = None
    if source is not None:
        platform = _PLATFORM_ALIASES.get(str(source).strip().lower(), Platform.OTHER)

    steam_raw = _first(row, _STEAM_ID_KEYS)
    steam_appid = int(_to_number(steam_raw)) if steam_raw is not None else None
    if steam_appid is not None and steam_appid <= 0:
        steam_appid = None

    status_raw = _first(row, _STATUS_KEYS)
    status = _STATUS_ALIASES.get(str(status_raw).strip().lower()) if status_raw else None

    return ImportedGame(
        title=str(title).strip()[:255],
        playtime_minutes=max(playtime, 0),
        status=status,
        last_played_at=_parse_dt(_first(row, _LAST_PLAYED_KEYS)),
        platform=platform,
        is_favorite=str(_first(row, _FAVORITE_KEYS) or "").strip().lower() in _TRUE,
        steam_appid=steam_appid if platform in (None, Platform.STEAM) else None,
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

    games: dict[tuple[str, Platform | None], ImportedGame] = {}
    for raw in rows:
        game = _row_to_game(raw)
        if game:
            # de-duplicate within the file (the same game may be owned on several stores)
            games.setdefault((game.title.lower(), game.platform), game)
    if not games:
        raise ImportFormatError("No games found. Expected a 'title' or 'name' column.")
    return list(games.values())
