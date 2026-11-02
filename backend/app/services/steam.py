"""Steam OpenID 2.0 sign-in and Steam Web API calls.

Steam does not offer OAuth for this: OpenID only proves which SteamID the user owns, and
GetOwnedGames is then called with our server-side Web API key.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from app.core.config import settings

OPENID_URL = "https://steamcommunity.com/openid/login"
API_URL = "https://api.steampowered.com"
_CLAIMED_ID = re.compile(r"^https://steamcommunity\.com/openid/id/(\d{17})$")
_NS = "http://specs.openid.net/auth/2.0"


class SteamError(RuntimeError):
    pass


class SteamProfilePrivate(SteamError):
    pass


@dataclass
class OwnedGame:
    appid: int
    name: str
    playtime_minutes: int
    last_played_at: datetime | None


@dataclass
class PlayerSummary:
    steam_id: str
    persona_name: str
    avatar_url: str | None


def callback_url() -> str:
    return f"{settings.frontend_url}/api/auth/steam/callback"


def build_login_url(state: str | None = None) -> str:
    return_to = callback_url() + (f"?{urlencode({'state': state})}" if state else "")
    params = {
        "openid.ns": _NS,
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": settings.frontend_url,
        "openid.identity": f"{_NS}/identifier_select",
        "openid.claimed_id": f"{_NS}/identifier_select",
    }
    return f"{OPENID_URL}?{urlencode(params)}"


async def verify_openid_response(params: dict[str, str]) -> str:
    """Validate the OpenID assertion with Steam and return the 64-bit SteamID."""
    if params.get("openid.mode") != "id_res":
        raise SteamError("Steam login was cancelled")
    if not params.get("openid.return_to", "").startswith(callback_url()):
        raise SteamError("Unexpected return_to")
    if params.get("openid.op_endpoint") != OPENID_URL:
        raise SteamError("Unexpected OpenID provider")
    match = _CLAIMED_ID.match(params.get("openid.claimed_id", ""))
    if not match:
        raise SteamError("Invalid claimed_id")

    check = {k: v for k, v in params.items() if k.startswith("openid.")}
    check["openid.mode"] = "check_authentication"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(OPENID_URL, data=check)
    if "is_valid:true" not in resp.text:
        raise SteamError("Steam rejected the login assertion")
    return match.group(1)


def _require_key() -> str:
    if not settings.steam_api_key:
        raise SteamError("STEAM_API_KEY is not set")
    return settings.steam_api_key


async def get_player_summary(steam_id: str) -> PlayerSummary | None:
    if not settings.steam_api_key:
        return None
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{API_URL}/ISteamUser/GetPlayerSummaries/v2/",
            params={"key": settings.steam_api_key, "steamids": steam_id},
        )
    resp.raise_for_status()
    players = resp.json().get("response", {}).get("players", [])
    if not players:
        return None
    p = players[0]
    return PlayerSummary(steam_id, p.get("personaname", ""), p.get("avatarfull"))


async def get_owned_games(steam_id: str) -> list[OwnedGame]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_URL}/IPlayerService/GetOwnedGames/v1/",
            params={
                "key": _require_key(),
                "steamid": steam_id,
                "include_appinfo": 1,
                "include_played_free_games": 1,
                "format": "json",
            },
        )
    resp.raise_for_status()
    data = resp.json().get("response", {})
    # A private "Game details" setting returns an empty response object instead of an error.
    if "games" not in data:
        if data.get("game_count") == 0:
            return []
        raise SteamProfilePrivate(
            "Steam returned no games. Set 'Game details' to Public in your Steam privacy settings."
        )

    return [
        OwnedGame(
            appid=g["appid"],
            name=g.get("name") or f"Steam app {g['appid']}",
            playtime_minutes=int(g.get("playtime_forever", 0)),
            last_played_at=(
                datetime.fromtimestamp(g["rtime_last_played"], UTC).replace(tzinfo=None)
                if g.get("rtime_last_played")
                else None
            ),
        )
        for g in data["games"]
    ]
