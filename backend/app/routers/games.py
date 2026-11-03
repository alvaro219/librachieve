import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Game, GameRating, LibraryEntry, User
from app.schemas.game import GameOut, IgdbSearchResult, RatingIn, RatingOut
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


async def _rateable_game(db: AsyncSession, game_id: int, user: User) -> Game:
    """You can only rate games that are in your library."""
    game = await db.get(Game, game_id)
    owned = game and await db.scalar(
        select(LibraryEntry.id)
        .where(LibraryEntry.user_id == user.id, LibraryEntry.game_id == game_id)
        .limit(1)
    )
    if not owned:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not in your library")
    return game


async def _refresh_community_rating(db: AsyncSession, game: Game) -> None:
    avg, count = (
        await db.execute(
            select(func.avg(GameRating.score), func.count()).where(GameRating.game_id == game.id)
        )
    ).one()
    game.community_rating = round(float(avg), 1) if avg is not None else None
    game.community_rating_count = count


@router.put("/{game_id}/rating", response_model=RatingOut)
async def rate_game(
    game_id: int,
    body: RatingIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    game = await _rateable_game(db, game_id, user)
    stmt = insert(GameRating).values(user_id=user.id, game_id=game.id, score=body.score)
    await db.execute(
        stmt.on_conflict_do_update(
            index_elements=["user_id", "game_id"],
            set_={"score": stmt.excluded.score, "updated_at": func.now()},
        )
    )
    await _refresh_community_rating(db, game)
    await db.commit()
    return RatingOut(
        score=body.score,
        community_rating=game.community_rating,
        community_rating_count=game.community_rating_count,
    )


@router.delete("/{game_id}/rating", response_model=RatingOut)
async def unrate_game(
    game_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    game = await _rateable_game(db, game_id, user)
    rating = await db.get(GameRating, (user.id, game.id))
    if rating:
        await db.delete(rating)
        await db.flush()
    await _refresh_community_rating(db, game)
    await db.commit()
    return RatingOut(
        score=None,
        community_rating=game.community_rating,
        community_rating_count=game.community_rating_count,
    )
