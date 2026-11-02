from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Platform, SyncJob, SyncJobStatus, User
from app.schemas.sync import SyncJobOut
from app.services.catalog import get_or_create_game, upsert_library_entry
from app.services.importers import ImportFormatError, parse_import_file
from app.services.queue import get_queue

router = APIRouter(prefix="/sync", tags=["sync"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MANUAL_PLATFORMS = {Platform.EPIC, Platform.GOG, Platform.AMAZON, Platform.OTHER}


@router.post("/steam", response_model=SyncJobOut, status_code=status.HTTP_202_ACCEPTED)
async def sync_steam(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not user.steam_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link your Steam account first")
    if not settings.steam_api_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Steam sync is not configured")

    running = await db.scalar(
        select(SyncJob.id).where(
            SyncJob.user_id == user.id,
            SyncJob.platform == Platform.STEAM,
            SyncJob.status.in_([SyncJobStatus.PENDING, SyncJobStatus.RUNNING]),
        )
    )
    if running:
        raise HTTPException(status.HTTP_409_CONFLICT, "A Steam sync is already in progress")

    job = SyncJob(user_id=user.id, platform=Platform.STEAM)
    db.add(job)
    await db.commit()
    await (await get_queue()).enqueue_job("sync_steam", job.id, user.steam_id)
    return job


@router.post("/import/{platform}", response_model=SyncJobOut, status_code=status.HTTP_201_CREATED)
async def import_file(
    platform: Platform,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if platform not in MANUAL_PLATFORMS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Use /sync/steam for Steam")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large (max 5 MB)")
    try:
        games = parse_import_file(file.filename or "", content)
    except ImportFormatError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from e

    job = SyncJob(user_id=user.id, platform=platform, status=SyncJobStatus.RUNNING)
    db.add(job)
    to_enrich: list[int] = []
    for g in games:
        # Files listing several stores (e.g. Playnite) set the platform per row
        game = await get_or_create_game(db, g.title, steam_appid=g.steam_appid)
        entry, _ = await upsert_library_entry(
            db,
            user_id=user.id,
            game=game,
            platform=g.platform or platform,
            playtime_minutes=g.playtime_minutes,
            last_played_at=g.last_played_at,
            status=g.status,
        )
        if g.is_favorite:
            entry.is_favorite = True
        if game.metadata_updated_at is None:
            to_enrich.append(game.id)
    job.status = SyncJobStatus.SUCCESS
    job.imported_count = len(games)
    job.finished_at = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()

    if to_enrich:
        await (await get_queue()).enqueue_job("enrich_games", to_enrich)
    return job


@router.get("/jobs", response_model=list[SyncJobOut])
async def list_jobs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(
        select(SyncJob).where(SyncJob.user_id == user.id).order_by(SyncJob.id.desc()).limit(20)
    )
    return rows.all()


@router.get("/jobs/{job_id}", response_model=SyncJobOut)
async def get_job(
    job_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    job = await db.get(SyncJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job
