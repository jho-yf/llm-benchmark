import json
import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import settings
from ..models import ScheduledJob
from .eval_engine import EvalEngine

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
    return _scheduler


def build_eval_func(job: ScheduledJob) -> Callable:
    """Build the callable that runs when a scheduled job fires."""

    def func():
        llm_params = json.loads(job.llm_params) if job.llm_params else {}
        bench_config = json.loads(job.benchmark_config) if isinstance(job.benchmark_config, str) else job.benchmark_config

        engine = EvalEngine(bench_config, {
            "provider": job.llm_provider,
            "api_base": job.llm_api_base,
            "api_key": job.llm_api_key,
            "auth_type": job.llm_auth_type,
            "model_id": job.llm_model_id,
            "params": llm_params,
        })

        run_id, log_path = EvalEngine.create_run_record(job, settings.database_url)
        try:
            engine.run_sync(run_id, settings.database_url, log_path)
        except Exception:
            logger.exception("Scheduled job %d failed", job.id)

        # Update last_run_at
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from datetime import datetime, timezone

        sync_url = settings.database_url.replace("+aiosqlite", "")
        eng = create_engine(sync_url)
        with Session(eng) as session:
            session.execute(
                text("UPDATE scheduled_job SET last_run_at=:t WHERE id=:id"),
                {"t": datetime.now(timezone.utc), "id": job.id},
            )
            session.commit()

    return func


def add_job(job: ScheduledJob):
    sched = get_scheduler()
    job_id = f"benchmark_{job.id}"
    sched.add_job(
        build_eval_func(job),
        CronTrigger.from_crontab(job.cron_expr),
        id=job_id,
        replace_existing=True,
    )
    logger.info("Scheduled job %s: %s", job_id, job.cron_expr)


def remove_job(job_db_id: int):
    sched = get_scheduler()
    job_id = f"benchmark_{job_db_id}"
    try:
        sched.remove_job(job_id)
    except Exception:
        pass
    logger.info("Removed job %s", job_id)


def toggle_job(job_db_id: int, enabled: bool):
    sched = get_scheduler()
    job_id = f"benchmark_{job_db_id}"
    if enabled:
        sched.resume_job(job_id)
    else:
        sched.pause_job(job_id)


def restore_jobs(jobs: list[ScheduledJob]):
    """Restore all enabled jobs from DB on startup."""
    for job in jobs:
        if job.enabled:
            add_job(job)
