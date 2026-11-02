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
