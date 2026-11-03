from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.deps import get_current_user
from app.models import LibraryEntry, Platform, SyncJob, SyncJobChange, SyncJobStatus, User
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
    await db.flush()  # job.id is needed for the change log
    to_enrich: list[int] = []
    for g in games:
        # Files listing several stores (e.g. Playnite) set the platform per row
        game = await get_or_create_game(db, g.title, steam_appid=g.steam_appid)
        entry, created, previous = await upsert_library_entry(
            db,
            user_id=user.id,
            game=game,
            platform=g.platform or platform,
            playtime_minutes=g.playtime_minutes,
            last_played_at=g.last_played_at,
            status=g.status,
        )
        db.add(_change_record(job.id, entry.id, created, previous))
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
    return _out(job, job.id)  # the newest import is always the undoable one


def _change_record(job_id: int, entry_id: int, created: bool, prev: dict | None) -> SyncJobChange:
    prev = prev or {}
    return SyncJobChange(
        job_id=job_id,
        entry_id=entry_id,
        created=created,
        prev_status=prev.get("status"),
        prev_playtime_minutes=prev.get("playtime_minutes"),
        prev_last_played_at=prev.get("last_played_at"),
        prev_is_favorite=prev.get("is_favorite"),
        prev_custom_folder=prev.get("custom_folder"),
    )


async def _latest_undoable_id(db: AsyncSession, user_id: int) -> int | None:
    """Undo works like a stack: only the newest completed file import can be reverted."""
    return await db.scalar(
        select(SyncJob.id)
        .where(
            SyncJob.user_id == user_id,
            SyncJob.platform != Platform.STEAM,
            SyncJob.status == SyncJobStatus.SUCCESS,
        )
        .order_by(SyncJob.id.desc())
        .limit(1)
    )


def _out(job: SyncJob, undoable_id: int | None) -> SyncJobOut:
    return SyncJobOut.model_validate(job).model_copy(update={"undoable": job.id == undoable_id})


@router.get("/jobs", response_model=list[SyncJobOut])
async def list_jobs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(
        select(SyncJob).where(SyncJob.user_id == user.id).order_by(SyncJob.id.desc()).limit(20)
    )
    undoable_id = await _latest_undoable_id(db, user.id)
    return [_out(job, undoable_id) for job in rows.all()]


@router.post("/jobs/{job_id}/undo", response_model=SyncJobOut)
async def undo_import(
    job_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Revert a file import: delete the entries it created, restore the ones it changed."""
    job = await db.get(SyncJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    if job.id != await _latest_undoable_id(db, user.id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se puede deshacer la última importación de fichero completada.",
        )

    changes = (
        await db.scalars(
            select(SyncJobChange)
            .where(SyncJobChange.job_id == job.id)
            .order_by(SyncJobChange.id.desc())  # newest first, in case a row was touched twice
        )
    ).all()
    if changes:
        for c in changes:
            entry = await db.get(LibraryEntry, c.entry_id)
            if entry is None or entry.user_id != user.id:
                continue  # deleted by the user in the meantime
            if c.created:
                await db.delete(entry)
            else:
                entry.status = c.prev_status or entry.status
                entry.playtime_minutes = c.prev_playtime_minutes or 0
                entry.last_played_at = c.prev_last_played_at
                entry.is_favorite = bool(c.prev_is_favorite)
                entry.custom_folder = c.prev_custom_folder
        await db.execute(delete(SyncJobChange).where(SyncJobChange.job_id == job.id))
    else:
        # Imports made before the change log existed: remove what was added during the import.
        until = (job.finished_at or job.created_at) + timedelta(seconds=2)
        await db.execute(
            delete(LibraryEntry).where(
                LibraryEntry.user_id == user.id,
                LibraryEntry.platform == job.platform,
                LibraryEntry.added_at >= job.created_at - timedelta(seconds=2),
                LibraryEntry.added_at <= until,
            )
        )

    job.status = SyncJobStatus.REVERTED
    await db.commit()
    return _out(job, await _latest_undoable_id(db, user.id))


@router.get("/jobs/{job_id}", response_model=SyncJobOut)
async def get_job(
    job_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    job = await db.get(SyncJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job
