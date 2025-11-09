from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.base import Base
# Import model modules to ensure tables are registered before create_all
from app.models import core as _models_core  # noqa: F401
from app.models import git_models as _models_git  # noqa: F401
from app.core.config import settings
from app.database.neo4j import get_neo4j_driver, close_neo4j_driver
from app.database.redis import get_redis, close_redis
from app.core.auth import RateLimitMiddleware

try:
    from app.api.routes.git_analysis import router as git_router
except Exception:
    git_router = None  # Router may not be ready during initial scaffolding

try:
    from app.api.routes.auth import router as auth_router
except Exception:
    auth_router = None

# New JWT auth router with refresh at /api/auth
try:
    from app.api.auth import router as api_auth_router
except Exception:
    api_auth_router = None

try:
    from app.api.routes.users import router as users_router
except Exception:
    users_router = None

try:
    from app.api.routes.projects import router as projects_router
except Exception:
    projects_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm shared clients
    get_neo4j_driver()
    get_redis()
    # Rate limit window epoch key (per-minute bucket)
    now = datetime.now(timezone.utc)
    app.state.startup_epoch_min = int(now.timestamp() // 60)
    yield
    # Shutdown: close shared clients
    await close_neo4j_driver()
    await close_redis()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

# Rate limit middleware (uses Redis and per-minute epoch state)
app.add_middleware(RateLimitMiddleware)

origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


if git_router is not None:
    app.include_router(git_router)
if auth_router is not None:
    app.include_router(auth_router)
if users_router is not None:
    app.include_router(users_router)
if projects_router is not None:
    app.include_router(projects_router)
if api_auth_router is not None:
    app.include_router(api_auth_router)
