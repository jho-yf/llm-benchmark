import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .models import ScheduledJob
from .routers import benchmarks, runs, schedules
from .services.scheduler import restore_jobs
from sqlalchemy import select
from .database import async_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as db:
        result = await db.execute(select(ScheduledJob).where(ScheduledJob.enabled))
        jobs = result.scalars().all()
    restore_jobs(list(jobs))
    logger.info("Restored %d scheduled jobs", len(jobs))
    yield


app = FastAPI(title="LLM Benchmark", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schedules.router)
app.include_router(runs.router)
app.include_router(benchmarks.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files (production only)
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
