# Librachieve

Librachieve is a full-stack web application for personal video game library management with external platform integration.

## Tech Stack
- **Frontend:** React 18 + TypeScript + Vite + TailwindCSS v4 + TanStack Query + React Router 6
- **Backend:** Python 3.12 + FastAPI (async SQLAlchemy 2 + asyncpg)
- **Database:** PostgreSQL 16 (via SQLAlchemy + Alembic for migrations)
- **Cache / Queue:** Redis (IGDB cache, refresh tokens, ARQ job queue)
- **API Layer:** REST (primary) + GraphQL via Strawberry (secondary, for complex list queries)
- **Auth:** JWT access token + revocable refresh token; Steam sign-in via OpenID 2.0
- **Containerization:** Docker + Docker Compose (dev) / Kubernetes via Minikube (staging)
- **CI/CD:** GitHub Actions → deploy to AWS (EC2 + S3 for assets)

## Core Features
1. **Platform sync:** Steam library import via Steam Web API (OpenID sign-in + GetOwnedGames with our server API key). Epic Games, GOG and Amazon Games via manual JSON/CSV import.
2. **Game metadata:** enriched automatically from IGDB API (cover art, genres, release date, description). Results cached in Redis.
3. **Library management:** games are categorized into — Backlog, Playing, Completed, Dropped, Wishlist, Other (free-form folder, `custom_folder`).
4. **User stats:** playtime tracking, completion ratio, most played genres, games per platform, achievements (unlocked/total, 100% games).
6. **Achievements:** Steam achievements via the official Web API (`app/services/achievements.py`): schema in Spanish (`l=spanish`) + global % refreshed weekly per game, player unlocks on every Steam sync (played games only). Counters are denormalised on `library_entries`.
5. **User profiles:** public/private toggle. JWT-based auth with role support (user / admin).

## Project Structure
- `frontend/` — React app (`src/api` typed client, `src/pages`, `src/components`, UI strings in Spanish, enum labels in `src/lib/labels.ts`)
- `backend/` — FastAPI app with routers: auth, games, library, users, sync
  - `app/models` SQLAlchemy models · `app/schemas` Pydantic · `app/services` (steam, igdb, importers, catalog, stats, queue) · `app/graphql` Strawberry schema · `app/worker.py` ARQ worker · `app/cli.py` management commands
- `infra/` — Docker Compose (dev + prod), Kubernetes manifests (`infra/k8s`)
- `.github/workflows/` — CI and deploy workflows (GitHub only reads them from here, not from `infra/`)
- `migrations/` + root `alembic.ini` — Alembic migration files

## Development Rules
- All API communication between frontend and backend goes through REST endpoints under `/api`. GraphQL endpoint is `/graphql` and is used only for library list queries with complex filtering.
- The browser only talks to one origin: Vite proxies `/api` and `/graphql` in dev; the ingress/CloudFront does it in staging/prod. Keep it that way — the refresh cookie (`httpOnly`, path `/api/auth`) depends on it.
- Redis is used for: IGDB API response caching (TTL 24h), refresh tokens / Steam link state, and the ARQ job queue. Never primary storage.
- Steam sync and IGDB enrichment run in the ARQ worker (`arq app.worker.WorkerSettings`), not FastAPI BackgroundTasks, so jobs survive API restarts. Job state the user sees lives in Postgres (`sync_jobs`).
- All endpoints are typed (Pydantic models on backend, TypeScript interfaces in `frontend/src/api/types.ts` — keep them in sync).
- PostgreSQL is the single source of truth. Redis is cache only, never primary storage.
- Epic/GOG account login (unofficial launcher APIs) was requested but is on hold pending the user's decision; Amazon stays file-import only.
- Postgres enum types are created/dropped explicitly in migrations (autogenerate doesn't handle shared enums or drop them on downgrade).

## Commands
```bash
# Full dev stack (frontend :5173, API :8000, Postgres, Redis, worker)
docker compose -f infra/docker-compose.yml up -d --build

# Backend checks (run inside the container; uses a separate test DB + Redis DB 1)
docker compose -f infra/docker-compose.yml exec postgres psql -U librachieve -c "CREATE DATABASE librachieve_test"   # once
docker compose -f infra/docker-compose.yml run --rm -e DATABASE_URL=postgresql+asyncpg://librachieve:librachieve@postgres:5432/librachieve_test -e REDIS_URL=redis://redis:6379/1 backend sh -c "ruff check . && ruff format --check . && pytest -q"

# New migration after changing models
docker compose -f infra/docker-compose.yml run --rm backend alembic revision --autogenerate -m "describe change"

# Re-run IGDB matching (--all resets every game's metadata first)
docker compose -f infra/docker-compose.yml exec backend python -m app.cli reenrich [--all]

# Make a user admin
docker compose -f infra/docker-compose.yml exec backend python -m app.cli make-admin <username>

# Frontend checks
cd frontend && npm run lint && npm run build
```
