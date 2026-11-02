from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.redis import redis_client
from app.db.session import SessionLocal, engine
from app.graphql.schema import graphql_router
from app.routers import auth, games, library, sync, users
from app.services.queue import close_queue


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_queue()
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="Librachieve API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, games, library, users, sync):
    app.include_router(r.router, prefix="/api")
app.include_router(graphql_router, prefix="/graphql")


@app.get("/api/health", tags=["health"])
async def health():
    async with SessionLocal() as db:
        await db.execute(text("SELECT 1"))
    await redis_client.ping()
    return {"status": "ok"}
