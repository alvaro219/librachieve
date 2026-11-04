import re
import secrets
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.ratelimit import hit, limit_by_ip
from app.core.redis import get_redis
from app.core.security import (
    REFRESH_COOKIE_NAME,
    consume_refresh_token,
    create_access_token,
    create_refresh_token,
    hash_password,
    revoke_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import steam

router = APIRouter(prefix="/auth", tags=["auth"])

_STEAM_STATE_PREFIX = "steam-link:"


async def _issue_tokens(
    response: Response, redis: Redis, db: AsyncSession, user: User
) -> TokenResponse:
    user.last_seen_at = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    refresh = await create_refresh_token(redis, user.id)
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/api/auth",
    )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[limit_by_ip("register", limit=5, window_seconds=3600)],
)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    exists = await db.scalar(
        select(User.id).where(
            or_(
                func.lower(User.username) == body.username.lower(),
                func.lower(User.email) == body.email.lower(),
            )
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already in use")

    user = User(
        username=body.username,
        email=body.email.lower(),
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    return await _issue_tokens(response, redis, db, user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[limit_by_ip("login", limit=20, window_seconds=900)],
)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    login_value = body.login.strip().lower()
    # Also per account, so one password can't be brute-forced from many IPs
    await hit(redis, f"login:account:{login_value}", limit=10, window_seconds=900)
    user = await db.scalar(
        select(User).where(or_(func.lower(User.username) == login_value, User.email == login_value))
    )
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return await _issue_tokens(response, redis, db, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[limit_by_ip("refresh", limit=120, window_seconds=60)],
)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    user_id = await consume_refresh_token(redis, token) if token else None
    user = await db.get(User, user_id) if user_id else None
    if user is None:
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    return await _issue_tokens(response, redis, db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, redis: Redis = Depends(get_redis)):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if token:
        await revoke_refresh_token(redis, token)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")


# --- Steam OpenID -------------------------------------------------------------------------


@router.get("/steam/login")
async def steam_login():
    return RedirectResponse(steam.build_login_url())


@router.post("/steam/link-url")
async def steam_link_url(user: User = Depends(get_current_user), redis: Redis = Depends(get_redis)):
    """Browser redirects can't carry the bearer token, so linking uses a short-lived state."""
    state = secrets.token_urlsafe(24)
    await redis.set(f"{_STEAM_STATE_PREFIX}{state}", str(user.id), ex=600)
    return {"url": steam.build_login_url(state)}


async def _unique_username(db: AsyncSession, base: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_\-]", "", base)[:24] or "player"
    if len(base) < 3:
        base = f"{base}player"
    candidate = base
    while await db.scalar(select(User.id).where(func.lower(User.username) == candidate.lower())):
        candidate = f"{base}{secrets.randbelow(10_000)}"
    return candidate


async def _player_summary(steam_id: str) -> steam.PlayerSummary | None:
    """Best effort: a Steam API hiccup must not block signing in."""
    try:
        return await steam.get_player_summary(steam_id)
    except httpx.HTTPError:
        return None


@router.get("/steam/callback")
async def steam_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    params = dict(request.query_params)
    try:
        steam_id = await steam.verify_openid_response(params)
    except steam.SteamError as e:
        return RedirectResponse(f"{settings.frontend_url}/login?error={type(e).__name__}")

    owner = await db.scalar(select(User).where(User.steam_id == steam_id))
    state = params.get("state")

    if state:  # linking Steam to an existing account
        user_id = await redis.getdel(f"{_STEAM_STATE_PREFIX}{state}")
        user = await db.get(User, int(user_id)) if user_id else None
        if user is None:
            return RedirectResponse(f"{settings.frontend_url}/settings?steam=expired")
        if owner and owner.id != user.id:
            return RedirectResponse(f"{settings.frontend_url}/settings?steam=taken")
        user.steam_id = steam_id
        summary = await _player_summary(steam_id)
        if summary and summary.avatar_url and not user.avatar_url:
            user.avatar_url = summary.avatar_url
        await db.commit()
        return RedirectResponse(f"{settings.frontend_url}/settings?steam=linked")

    summary = await _player_summary(steam_id)
    user = owner
    if user is None:
        user = User(
            username=await _unique_username(db, summary.persona_name if summary else "player"),
            steam_id=steam_id,
        )
        db.add(user)
    if summary and summary.avatar_url:
        user.avatar_url = summary.avatar_url  # keep the Steam avatar fresh on every login
    await db.commit()

    redirect = RedirectResponse(f"{settings.frontend_url}/auth/callback")
    await _issue_tokens(redirect, redis, db, user)
    return redirect
