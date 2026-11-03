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


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def _reset_rate_limits():
    from app.core.redis import redis_client

    keys = [k async for k in redis_client.scan_iter("ratelimit:*")]
    if keys:
        await redis_client.delete(*keys)


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


async def test_login_is_rate_limited_per_account(client):
    headers = await _register(client)
    username = headers.pop("username")
    bad = {"login": username, "password": "wrong-password"}
    codes = [(await client.post("/api/auth/login", json=bad)).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
    # Still blocked even with the right password until the window expires
    ok = {"login": username, "password": "supersecret"}
    resp = await client.post("/api/auth/login", json=ok)
    assert resp.status_code == 429 and "Retry-After" in resp.headers


async def test_reimport_applies_file_status_but_keeps_it_when_absent(client):
    headers = await _register(client)
    headers.pop("username")

    async def upload(content: bytes):
        resp = await client.post(
            "/api/sync/import/epic",
            headers=headers,
            files={"file": ("lib.csv", content, "text/csv")},
        )
        assert resp.status_code == 201, resp.text

    async def status_of(title: str) -> dict:
        q = "query($s: String) { library(filter:{search:$s}) { items { status playtimeMinutes } } }"
        body = {"query": q, "variables": {"s": title}}
        data = (await client.post("/graphql", headers=headers, json=body)).json()
        return data["data"]["library"]["items"][0]

    await upload("Nombre,Estado de finalización,Tiempo Jugado\nHades,Not Played,0\n".encode())
    assert (await status_of("hades"))["status"] == "BACKLOG"

    await upload("Nombre,Estado de finalización,Tiempo Jugado\nHades,Beaten,7200\n".encode())
    assert await status_of("hades") == {"status": "COMPLETED", "playtimeMinutes": 120}

    await upload(b"Nombre\nHades\n")  # no status column: keep what we have
    assert (await status_of("hades"))["status"] == "COMPLETED"


async def test_undo_imports_like_a_stack(client):
    headers = await _register(client)
    headers.pop("username")

    async def upload(content: str) -> dict:
        resp = await client.post(
            "/api/sync/import/gog",
            headers=headers,
            files={"file": ("lib.csv", content.encode(), "text/csv")},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def library() -> dict:
        q = "{ library { items { status playtimeMinutes isFavorite game { title } } } }"
        data = (await client.post("/graphql", headers=headers, json={"query": q})).json()
        return {i["game"]["title"]: i for i in data["data"]["library"]["items"]}

    # A game added by hand must survive every undo
    await client.post("/api/library", headers=headers, json={"title": "Celeste", "platform": "gog"})

    first = await upload("Nombre,Estado de finalización,Tiempo Jugado\nHades,Not Played,0\n")
    assert first["undoable"] is True
    second = await upload(
        "Nombre,Estado de finalización,Tiempo Jugado,Favorito\n"
        "Hades,Beaten,7200,Sí\nTunic,Playing,60,No\nCeleste,Completed,600,No\n"
    )
    assert set(await library()) == {"Celeste", "Hades", "Tunic"}

    jobs = (await client.get("/api/sync/jobs", headers=headers)).json()
    assert [j["undoable"] for j in jobs] == [True, False]
    # Only the newest import can be undone
    resp = await client.post(f"/api/sync/jobs/{first['id']}/undo", headers=headers)
    assert resp.status_code == 409

    resp = await client.post(f"/api/sync/jobs/{second['id']}/undo", headers=headers)
    assert resp.status_code == 200 and resp.json()["status"] == "reverted"
    lib = await library()
    assert set(lib) == {"Celeste", "Hades"}  # Tunic was created by the undone import
    assert lib["Hades"] == {
        "status": "BACKLOG",
        "playtimeMinutes": 0,
        "isFavorite": False,
        "game": {"title": "Hades"},
    }
    assert lib["Celeste"]["status"] == "BACKLOG"  # restored to its manual value

    # Now the first import is the undoable one
    jobs = (await client.get("/api/sync/jobs", headers=headers)).json()
    assert [(j["status"], j["undoable"]) for j in jobs] == [("reverted", False), ("success", True)]
    assert (
        await client.post(f"/api/sync/jobs/{first['id']}/undo", headers=headers)
    ).status_code == 200
    assert set(await library()) == {"Celeste"}
    assert (
        await client.post(f"/api/sync/jobs/{first['id']}/undo", headers=headers)
    ).status_code == 409


async def test_ratings_and_community_average(client):
    alice = await _register(client)
    alice.pop("username")
    bob = await _register(client)
    bob.pop("username")
    carol = await _register(client)
    carol.pop("username")

    hades = (await client.post("/api/library", headers=alice, json={"title": "Hades"})).json()
    game_id = hades["game"]["id"]
    await client.post("/api/library", headers=alice, json={"title": "Celeste"})
    await client.post("/api/library", headers=bob, json={"game_id": game_id, "platform": "epic"})

    # Range is enforced, and you can only rate games in your library
    bad = await client.put(f"/api/games/{game_id}/rating", headers=alice, json={"score": 101})
    assert bad.status_code == 422
    resp = await client.put(f"/api/games/{game_id}/rating", headers=carol, json={"score": 50})
    assert resp.status_code == 404

    resp = await client.put(f"/api/games/{game_id}/rating", headers=alice, json={"score": 90})
    assert resp.json() == {"score": 90, "community_rating": 90.0, "community_rating_count": 1}
    resp = await client.put(f"/api/games/{game_id}/rating", headers=bob, json={"score": 75})
    assert resp.json()["community_rating"] == 82.5
    resp = await client.put(f"/api/games/{game_id}/rating", headers=alice, json={"score": 80})
    assert resp.json()["community_rating"] == 77.5  # re-rating replaces, not adds

    q = """{ library(sort:{field:USER_RATING,direction:DESC}) {
              items { userRating game { title communityRating communityRatingCount } } } }"""
    data = (await client.post("/graphql", headers=alice, json={"query": q})).json()
    items = data["data"]["library"]["items"]
    assert items[0] == {
        "userRating": 80,
        "game": {"title": "Hades", "communityRating": 77.5, "communityRatingCount": 2},
    }
    assert items[1]["userRating"] is None  # Celeste, unrated, sorts last

    resp = await client.delete(f"/api/games/{game_id}/rating", headers=bob)
    assert resp.json() == {"score": None, "community_rating": 80.0, "community_rating_count": 1}


async def test_filter_by_scores_and_genre(client):
    from sqlalchemy import update

    from app.db.session import SessionLocal
    from app.models import Game

    headers = await _register(client)
    headers.pop("username")
    ids = {}
    for title in ("Zelda Test", "Mario Test", "Doom Test"):
        resp = await client.post("/api/library", headers=headers, json={"title": title})
        ids[title] = resp.json()["game"]["id"]

    async with SessionLocal() as db:
        meta = {
            "Zelda Test": (["Adventure", "RPG"], 95, 97),
            "Mario Test": (["Platform", "Adventure"], 80, 70),
            "Doom Test": (["Shooter"], None, 88),
        }
        for title, (genres, igdb, critic) in meta.items():
            await db.execute(
                update(Game)
                .where(Game.id == ids[title])
                .values(genres=genres, igdb_rating=igdb, critic_rating=critic)
            )
        await db.commit()
    await client.put(f"/api/games/{ids['Mario Test']}/rating", headers=headers, json={"score": 60})

    async def titles(filter_: dict) -> list[str]:
        q = "query($f: LibraryFilter) { library(filter: $f) { items { game { title } } } }"
        resp = await client.post(
            "/graphql", headers=headers, json={"query": q, "variables": {"f": filter_}}
        )
        data = resp.json()
        assert "errors" not in data, data
        return sorted(i["game"]["title"] for i in data["data"]["library"]["items"])

    assert await titles({"minIgdbRating": 90}) == ["Zelda Test"]
    assert await titles({"minCriticRating": 80}) == ["Doom Test", "Zelda Test"]
    assert await titles({"minUserRating": 50}) == ["Mario Test"]
    assert await titles({"genres": ["Adventure"]}) == ["Mario Test", "Zelda Test"]
    assert await titles({"genres": ["Adventure"], "minCriticRating": 90}) == ["Zelda Test"]

    q = "{ genres { genre games } }"
    data = (await client.post("/graphql", headers=headers, json={"query": q})).json()
    assert data["data"]["genres"][0] == {"genre": "Adventure", "games": 2}
    assert {g["genre"] for g in data["data"]["genres"]} == {
        "Adventure",
        "RPG",
        "Platform",
        "Shooter",
    }
