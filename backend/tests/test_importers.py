import json

import pytest

from app.models.enums import GameStatus
from app.services.catalog import normalize_title
from app.services.importers import ImportFormatError, parse_import_file


def test_json_list_with_hours_and_status():
    data = [
        {"Title": "Hades", "playtime_hours": "12,5", "status": "Finished"},
        {"name": "Celeste", "playtime_minutes": 90},
    ]
    games = parse_import_file("epic.json", json.dumps(data).encode())
    assert [(g.title, g.playtime_minutes, g.status) for g in games] == [
        ("Hades", 750, GameStatus.COMPLETED),
        ("Celeste", 90, None),
    ]


def test_json_object_wrapper_and_dedup():
    data = {"games": [{"title": "Hades"}, {"title": "hades"}, {"foo": "no title"}]}
    games = parse_import_file("x.json", json.dumps(data).encode())
    assert [g.title for g in games] == ["Hades"]


def test_csv_semicolon_with_bom():
    content = "﻿title;hours;status\nDisco Elysium;30;playing\nOuter Wilds;;\n".encode()
    games = parse_import_file("gog.csv", content)
    assert games[0].title == "Disco Elysium"
    assert games[0].playtime_minutes == 1800
    assert games[0].status == GameStatus.PLAYING
    assert games[1].playtime_minutes == 0


def test_sniffs_format_without_extension():
    games = parse_import_file("export", b'[{"title": "Tunic"}]')
    assert games[0].title == "Tunic"


@pytest.mark.parametrize("content", [b"not json at all {", b"{}", b"a,b\n1,2\n"])
def test_rejects_bad_files(content):
    with pytest.raises(ImportFormatError):
        parse_import_file("bad.json" if content.startswith(b"{") else "bad.csv", content)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("DOOM®", "doom"),
        ("Tom Clancy's Rainbow Six™ Siege", "tom clancy s rainbow six siege"),
        ("  Pokémon:  Legends ", "pokemon legends"),
    ],
)
def test_normalize_title(raw, expected):
    assert normalize_title(raw) == expected


def test_igdb_pick_exact_prefers_main_and_popular_game():
    from app.services.igdb import clean_title, pick_exact

    rows = [
        {"id": 14546, "name": "Portal", "game_type": 0, "total_rating_count": 6},
        {"id": 71, "name": "Portal", "game_type": 0, "total_rating_count": 2500},
        {"id": 999, "name": "Portal", "game_type": 13, "total_rating_count": 9000},  # bundle
        {"id": 193776, "name": "Portal Maze 2", "game_type": 0},
    ]
    assert pick_exact("PORTAL", rows)["id"] == 71
    assert pick_exact("Portal 3", rows) is None  # never guess a non-exact match
    assert clean_title("Battlefield™  1") == "Battlefield 1"


def test_playnite_style_export_with_per_row_store():
    from app.models.enums import Platform

    content = (
        b"playniteId,name,sourceName,steamAppId,favorite,isInstalled\n"
        b"1,Hades,Steam,1145360,False,True\n"
        b"2,Hades,Epic,,True,False\n"
        b"3,The Witcher 3,GOG,,False,False\n"
        b"4,Diablo IV,Battle.net,,False,True\n"
        b"5,Hades,Steam,1145360,False,True\n"
    )
    games = parse_import_file("playnite-library.csv", content)
    got = [(g.title, g.platform, g.steam_appid, g.is_favorite) for g in games]
    assert got == [
        ("Hades", Platform.STEAM, 1145360, False),
        ("Hades", Platform.EPIC, None, True),
        ("The Witcher 3", Platform.GOG, None, False),
        ("Diablo IV", Platform.OTHER, None, False),
    ]


def test_playtime_in_seconds():
    games = parse_import_file("x.json", b'[{"name": "Celeste", "playtime_seconds": 7260}]')
    assert games[0].playtime_minutes == 121


def test_playnite_spanish_headers_seconds_and_statuses():
    content = (
        "\ufeffNombre,Estado de finalización,Tiempo Jugado\n"
        "A Short Hike,Completed,6830\n"
        "Age of Empires II: Definitive Edition,Played,22980\n"
        '"Aerial_Knight\'s Never Yield",Abandoned,0\n'
        '"Aerial_Knight\'s Never Yield",Abandoned,0\n'
        "Hades,Beaten,3600\n"
        "Celeste,Playing,60\n"
        "Tunic,Plan to Play,0\n"
        "Inscryption,Estado inventado,0\n"
    ).encode()
    games = {g.title: g for g in parse_import_file("amazon_games_library.csv", content)}
    assert len(games) == 7  # duplicate row collapsed
    assert games["A Short Hike"].playtime_minutes == 113  # seconds, not minutes
    assert games["A Short Hike"].status == GameStatus.COMPLETED
    assert games["Age of Empires II: Definitive Edition"].status == GameStatus.BACKLOG
    assert games["Aerial_Knight's Never Yield"].status == GameStatus.DROPPED
    assert games["Hades"].status == GameStatus.COMPLETED
    assert games["Celeste"].status == GameStatus.PLAYING
    assert games["Tunic"].status == GameStatus.BACKLOG
    assert games["Inscryption"].status is None  # unknown value: keep the default


def test_name_only_file():
    games = parse_import_file("lista.csv", b"Nombre\nHades\nCeleste\n")
    assert [(g.title, g.playtime_minutes, g.status) for g in games] == [
        ("Hades", 0, None),
        ("Celeste", 0, None),
    ]
