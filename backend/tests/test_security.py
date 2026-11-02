import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services import steam


def test_password_roundtrip():
    hashed = hash_password("correct horse")
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    payload = decode_access_token(create_access_token(42, "admin"))
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_tampered_token_rejected():
    token = create_access_token(1, "user")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token[:-2] + ("aa" if not token.endswith("aa") else "bb"))


async def test_openid_rejects_forged_claimed_id():
    params = {
        "openid.mode": "id_res",
        "openid.return_to": steam.callback_url(),
        "openid.op_endpoint": steam.OPENID_URL,
        "openid.claimed_id": "https://evil.example/openid/id/76561197960287930",
    }
    with pytest.raises(steam.SteamError):
        await steam.verify_openid_response(params)


async def test_openid_rejects_foreign_return_to():
    params = {
        "openid.mode": "id_res",
        "openid.return_to": "https://evil.example/callback",
        "openid.op_endpoint": steam.OPENID_URL,
        "openid.claimed_id": "https://steamcommunity.com/openid/id/76561197960287930",
    }
    with pytest.raises(steam.SteamError):
        await steam.verify_openid_response(params)
