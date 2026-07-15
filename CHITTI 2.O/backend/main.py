import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import upload, profile, visualize, insights, explain, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
    cleanup_task = asyncio.create_task(_cleanup_loop())
    yield
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def _cleanup_loop():
    from backend.utils.cleanup import cleanup_old_sessions
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        cleanup_old_sessions(settings.UPLOAD_DIR, settings.SESSION_TTL_MINUTES)


app = FastAPI(
    title="Explain My Data API",
    description="AI-powered data analysis platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(visualize.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
app.include_router(explain.router, prefix="/api")
app.include_router(predict.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
