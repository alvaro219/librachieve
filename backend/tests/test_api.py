"""Integration tests against real Postgres + Redis (docker compose or CI services).

Skipped automatically when the database is unreachable.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def _schema():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        pytest.skip("Postgres not reachable", allow_module_level=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _register(client: AsyncClient) -> dict:
    name = f"u{uuid.uuid4().hex[:10]}"
    resp = await client.post(
        "/api/auth/register",
        json={"username": name, "email": f"{name}@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}", "username": name}


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.json() == {"status": "ok"}


async def test_auth_flow(client):
    headers = await _register(client)
    username = headers.pop("username")

    me = await client.get("/api/users/me", headers=headers)
    assert me.json()["username"] == username

    login = await client.post(
        "/api/auth/login", json={"login": username.upper(), "password": "supersecret"}
    )
    assert login.status_code == 200

    # refresh cookie rotates: second use of the same cookie fails
    old_cookie = client.cookies.get("librachieve_refresh")
    assert (await client.post("/api/auth/refresh")).status_code == 200
    client.cookies.set("librachieve_refresh", old_cookie, path="/api/auth")
    assert (await client.post("/api/auth/refresh")).status_code == 401


async def test_library_import_stats_and_graphql(client):
    headers = await _register(client)
    username = headers.pop("username")

    csv = b"title,hours,status\nHades,20,completed\nCeleste,5,playing\nTunic,0,wishlist\n"
    resp = await client.post(
        "/api/sync/import/epic", headers=headers, files={"file": ("lib.csv", csv, "text/csv")}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["imported_count"] == 3

    resp = await client.post(
        "/api/library",
        headers=headers,
        json={"title": "Outer Wilds", "status": "other", "custom_folder": "Space"},
    )
    assert resp.status_code == 201, resp.text
    entry_id = resp.json()["id"]
    assert resp.json()["custom_folder"] == "Space"

    resp = await client.patch(
        f"/api/library/{entry_id}", headers=headers, json={"status": "dropped"}
    )
    assert resp.json()["status"] == "dropped" and resp.json()["custom_folder"] is None

    stats = (await client.get("/api/users/me/stats", headers=headers)).json()
    assert stats["total_games"] == 4
    assert stats["total_playtime_minutes"] == 1500
    assert stats["completion_ratio"] == pytest.approx(1 / 3, abs=1e-3)

    query = """
      query($f: LibraryFilter, $s: LibrarySort) {
        library(filter: $f, sort: $s) { total items { status game { title } } }
      }
    """
    variables = {
        "f": {"statuses": ["COMPLETED", "PLAYING"], "search": "e"},
        "s": {"field": "PLAYTIME", "direction": "DESC"},
    }
    resp = await client.post(
        "/graphql", headers=headers, json={"query": query, "variables": variables}
    )
    data = resp.json()
    assert "errors" not in data, data
    assert [i["game"]["title"] for i in data["data"]["library"]["items"]] == ["Hades", "Celeste"]

    # Private profile is invisible to anonymous users
    assert (await client.get(f"/api/users/{username}")).status_code == 404
    await client.patch("/api/users/me", headers=headers, json={"is_public": True})
    assert (await client.get(f"/api/users/{username}/stats")).status_code == 200


async def test_other_users_entries_are_hidden(client):
    a = await _register(client)
    a.pop("username")
    b = await _register(client)
    b.pop("username")
    resp = await client.post("/api/library", headers=a, json={"title": "Hollow Knight"})
    entry_id = resp.json()["id"]
    assert (await client.delete(f"/api/library/{entry_id}", headers=b)).status_code == 404


async def test_achievements_flow(client):
    from app.db.session import SessionLocal
    from app.models import LibraryEntry, User
    from app.services.achievements import (
        _refresh_counters,
        _SteamGameData,
        _store_player,
        _store_schema,
    )

    headers = await _register(client)
    username = headers.pop("username")
    resp = await client.post(
        "/api/library", headers=headers, json={"title": "Portal", "platform": "steam"}
    )
    entry_id = resp.json()["id"]

    schema = [
        {"name": "A1", "displayName": "Primero", "description": "Haz algo", "icon": "i1"},
        {"name": "A2", "displayName": "Segundo", "hidden": 1, "icon": "i2"},
        {"name": "A3", "displayName": "Tercero", "icon": "i3"},
    ]
    async with SessionLocal() as db:
        entry = await db.get(LibraryEntry, entry_id)
        data = _SteamGameData(schema=schema, global_percent={"A1": 80.5, "A2": 3.2})
        await _store_schema(db, entry.game_id, data)
        await _store_player(db, entry.user_id, entry.game_id, {"A1": 1700000000, "A2": 1})
        await _refresh_counters(db, entry)
        await db.commit()
        # Re-sync with an achievement removed from the schema: it disappears everywhere
        await _store_schema(db, entry.game_id, _SteamGameData(schema=schema[:2]))
        await _refresh_counters(db, entry)
        await db.commit()
        user = await db.get(User, entry.user_id)

    resp = await client.get(f"/api/library/{entry_id}/achievements", headers=headers)
    achs = resp.json()
    assert [(a["name"], a["unlocked"]) for a in achs] == [("Primero", True), ("Segundo", True)]
    assert achs[0]["global_percent"] == 80.5 and achs[0]["unlocked_at"].startswith("2023-11-14")
    assert achs[1]["hidden"] is True and achs[1]["unlocked_at"] is None

    stats = (await client.get("/api/users/me/stats", headers=headers)).json()
    assert (stats["achievements_unlocked"], stats["achievements_total"]) == (2, 2)
    assert stats["perfect_games"] == 1

    # Private profile: anonymous viewers can't see the achievements
    assert user.is_public is False
    assert (await client.get(f"/api/library/{entry_id}/achievements")).status_code == 404

    query = (
        "{ library(sort:{field:ACHIEVEMENTS,direction:DESC})"
        " { items { achievementsUnlocked achievementsTotal } } }"
    )
    data = (await client.post("/graphql", headers=headers, json={"query": query})).json()
    assert data["data"]["library"]["items"][0] == {
        "achievementsUnlocked": 2,
        "achievementsTotal": 2,
    }
    assert username


async def test_favorites(client):
    headers = await _register(client)
    headers.pop("username")
    ids = []
    for title in ("Hades", "Celeste", "Tunic"):
        resp = await client.post("/api/library", headers=headers, json={"title": title})
        ids.append(resp.json()["id"])
        assert resp.json()["is_favorite"] is False

    resp = await client.patch(f"/api/library/{ids[1]}", headers=headers, json={"is_favorite": True})
    assert resp.json()["is_favorite"] is True
    # An explicit null must not wipe non-nullable fields
    resp = await client.patch(
        f"/api/library/{ids[1]}", headers=headers, json={"is_favorite": None, "status": None}
    )
    assert resp.status_code == 200 and resp.json()["is_favorite"] is True

    query = "{ library(filter:{favoritesOnly:true}) { total items { isFavorite game { title } } } }"
    data = (await client.post("/graphql", headers=headers, json={"query": query})).json()
    assert data["data"]["library"] == {
        "total": 1,
        "items": [{"isFavorite": True, "game": {"title": "Celeste"}}],
    }
