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
- **CI/CD:** GitHub Actions builds amd64+arm64 images to GHCR, then SSH deploy (pull, no build on the server) to a single Oracle Cloud Always Free VM (Caddy + Docker Compose, `infra/docker-compose.prod.yml`). Target is the A1 ARM VM; the 1 GB E2.1.Micro is the stopgap while Madrid has no A1 capacity. The user chose Oracle over AWS to keep hosting free.

## Core Features
1. **Platform sync:** Steam library import via Steam Web API (OpenID sign-in + GetOwnedGames with our server API key). Epic Games, GOG and Amazon Games via manual JSON/CSV import.
2. **Game metadata:** enriched automatically from IGDB API (cover art, genres, release date, description). Results cached in Redis.
3. **Library management:** games are categorized into — Backlog, Playing, Completed, Dropped, Wishlist, Other (free-form folder, `custom_folder`).
4. **User stats:** playtime tracking, completion ratio, most played genres, games per platform, achievements (unlocked/total, 100% games).
6. **Achievements:** Steam achievements via the official Web API (`app/services/achievements.py`): schema in Spanish (`l=spanish`) + global % refreshed weekly per game, player unlocks on every Steam sync (played games only). Counters are denormalised on `library_entries`.
7. **Ratings (like Playnite):** your 0-100 score per game (`game_ratings`, one per game across stores), Librachieve users average (`games.community_rating`, recomputed on every vote), IGDB community (`igdb_rating`) and critics (`critic_rating`, IGDB aggregated). Filter/sort by any of them; filter by genre.
5. **User profiles:** public/private toggle. JWT-based auth with role support (user / admin); password change in Settings (Steam-only accounts can set a first one). No password reset yet (needs outgoing email).
8. **Friends:** `friendships` table, one row per pair (pending → accepted; crossed requests auto-accept). User search shows public profiles by partial name and private ones only by exact name. Steam friends who use Librachieve (`GetFriendList`, needs a public friends list) can be added in one click, already accepted: the friendship is mutual on Steam and checked server-side. Friends do NOT see private profiles (yet); the list is the base for future social features.
9. **Admin panel** (`/admin`, `app/routers/admin.py`): overview counters, user list (search, promote/demote, delete; never your own account) and re-run IGDB matching for games without metadata.
10. **Daily Steam sync:** ARQ cron `schedule_steam_syncs` at 04:00 UTC for users with Steam linked and `last_seen_at` in the last 30 days (set on login/refresh); jobs flagged `automatic`, only the newest is listed and older than 7 days are pruned.

## Project Structure
- `frontend/` — React app (`src/api` typed client, `src/pages`, `src/components`, UI strings in Spanish, enum labels in `src/lib/labels.ts`)
- `backend/` — FastAPI app with routers: auth, games, library, users, friends, sync, admin
  - `app/models` SQLAlchemy models · `app/schemas` Pydantic · `app/services` (steam, igdb, importers, catalog, stats, queue, friends) · `app/graphql` Strawberry schema · `app/worker.py` ARQ worker · `app/cli.py` management commands
- `infra/` — Docker Compose (dev + prod), `Caddyfile` (prod HTTPS entry point), `server-setup.sh` (VM bootstrap), Kubernetes manifests (`infra/k8s`, Minikube staging)
- `.github/workflows/` — CI and deploy workflows (GitHub only reads them from here, not from `infra/`)
- `migrations/` + root `alembic.ini` — Alembic migration files

## Development Rules
- All API communication between frontend and backend goes through REST endpoints under `/api`. GraphQL endpoint is `/graphql` and is used only for library list queries with complex filtering.
- The browser only talks to one origin: Vite proxies `/api` and `/graphql` in dev; the ingress/CloudFront does it in staging/prod. Keep it that way — the refresh cookie (`httpOnly`, path `/api/auth`) depends on it.
- Redis is used for: IGDB API response caching (TTL 24h), refresh tokens / Steam link state, and the ARQ job queue. Never primary storage.
- Steam sync and IGDB enrichment run in the ARQ worker (`arq app.worker.WorkerSettings`), not FastAPI BackgroundTasks, so jobs survive API restarts. Job state the user sees lives in Postgres (`sync_jobs`).
- All endpoints are typed (Pydantic models on backend, TypeScript interfaces in `frontend/src/api/types.ts` — keep them in sync).
- PostgreSQL is the single source of truth. Redis is cache only, never primary storage.
- Epic/GOG/Amazon: file import only (JSON/CSV). Playnite exports use UI-language headers (e.g. `Nombre,Estado de finalización,Tiempo Jugado` — playtime in **seconds**) and English status values; only the title is required. A status in the file is applied on re-import; Steam syncs never change statuses.
- File imports can be undone (newest first, like a stack): `sync_job_changes` logs created entries and previous values; imports from before the log existed fall back to deleting that platform's entries added during the import window. Logging into them via unofficial launcher APIs was rejected (ToS + storing third-party tokens server-side). A local desktop companion is a possible future idea.
- Auth endpoints (plus password change and friend requests) are rate limited in Redis (`app/core/ratelimit.py`); tests reset `ratelimit:*` keys.
- Never log or store raw httpx errors: Steam Web API URLs carry our API key in the query string. Use `app.core.http.describe_error`. Secrets go in headers or request bodies, never in URLs we control.
- Legal pages (`/privacidad`, `/aviso-legal`) are required (Spain/GDPR); owner data lives in `frontend/src/lib/site.ts`.
- Installable PWA (`public/site.webmanifest`, `public/sw.js`, `src/lib/pwa.ts`); the worker registers only in production builds. It must never cache `/api` or `/graphql` (user data, cookie flows); bump `VERSION` in `sw.js` to drop old caches. Mobile layout: bottom tab bar below `md`, header nav from `md` up. Native wrappers (Tauri/Capacitor) are deferred until there is a server; Play Store and code signing cost money.
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

# Re-download IGDB metadata (covers, ratings…) keeping existing matches
docker compose -f infra/docker-compose.yml exec backend python -m app.cli refresh-metadata

# Make a user admin
docker compose -f infra/docker-compose.yml exec backend python -m app.cli make-admin <username>

# Frontend checks
cd frontend && npm run lint && npm run build
```
