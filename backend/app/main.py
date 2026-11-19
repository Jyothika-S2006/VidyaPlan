"""VidyaPlan FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.settings import get_settings
from app.db.session import init_db
from app.api import routes_data, routes_plan, routes_review, routes_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialise DB on startup."""
    logger.info("Starting VidyaPlan backend...")
    await init_db()
    logger.info("Database initialised.")
    yield
    logger.info("Shutting down VidyaPlan backend.")


app = FastAPI(
    title="VidyaPlan API",
    description="Budget-constrained infrastructure planner for Karnataka schools.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_data.router, prefix="/api", tags=["data"])
app.include_router(routes_plan.router, prefix="/api", tags=["plan"])
app.include_router(routes_review.router, prefix="/api", tags=["review"])
app.include_router(routes_config.router, prefix="/api", tags=["config"])


@app.get("/health", tags=["health"])
async def health():
    """Liveness check: reports DB status and watsonx credential configuration."""
    from app.db.session import check_db_health
    db_ok = await check_db_health()
    watsonx_configured = bool(settings.watsonx_api_key and settings.watsonx_project_id)
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "watsonx_configured": watsonx_configured,
        "version": "0.1.0",
    }


@app.get("/api/version", tags=["health"])
async def version():
    """Return API version."""
    return {"version": "0.1.0", "name": "VidyaPlan"}


# ── Serve React frontend in production ───────────────────────────────────────
# In production (Docker), the React build is at /app/frontend/dist.
# In development, the Vite dev server runs separately on port 5173.
_FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes."""
        index = _FRONTEND_DIST / "index.html"
        return FileResponse(str(index))
