import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Game, User
from app.schemas.game import GameOut, IgdbSearchResult
from app.services import igdb
from app.services.queue import get_queue

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/search", response_model=list[IgdbSearchResult])
async def search_games(
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    _: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    try:
        return await igdb.search(redis, q, limit)
    except igdb.IgdbNotConfigured as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e
    except httpx.HTTPError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "IGDB request failed") from e


@router.get("/{game_id}", response_model=GameOut)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    game = await db.get(Game, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    return game


@router.post("/{game_id}/refresh-metadata", status_code=status.HTTP_202_ACCEPTED)
async def refresh_metadata(
    game_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if await db.get(Game, game_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    await (await get_queue()).enqueue_job("enrich_games", [game_id])
    return {"queued": True}
