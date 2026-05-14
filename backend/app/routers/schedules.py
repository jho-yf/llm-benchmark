import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import ScheduledJob, TestRun
from ..schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleTestConnection,
    ScheduleUpdate,
)
from ..services import scheduler as sched
from ..services.llm_client import LLMClient  # noqa: F401 — used by test-connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/schedules", tags=["schedules"])


def _mask_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _job_to_response(job: ScheduledJob) -> ScheduleResponse:
    return ScheduleResponse(
        id=job.id,
        name=job.name,
        cron_expr=job.cron_expr,
        enabled=job.enabled,
        last_run_at=job.last_run_at,
        next_run_at=job.next_run_at,
        created_at=job.created_at,
        llm_provider=job.llm_provider,
        llm_api_base=job.llm_api_base,
        llm_api_key=_mask_key(job.llm_api_key),
        llm_auth_type=job.llm_auth_type,
        llm_model_id=job.llm_model_id,
        llm_params=json.loads(job.llm_params) if job.llm_params else None,
        benchmark_name=job.benchmark_name,
        benchmark_category=job.benchmark_category,
        benchmark_config=json.loads(job.benchmark_config),
        benchmark_metrics=json.loads(job.benchmark_metrics) if job.benchmark_metrics else None,
        benchmark_params=json.loads(job.benchmark_params) if job.benchmark_params else None,
    )


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledJob).order_by(ScheduledJob.id))
    return [_job_to_response(j) for j in result.scalars().all()]


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(body: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    job = ScheduledJob(
        name=body.name,
        cron_expr=body.cron_expr,
        llm_provider=body.llm.provider,
        llm_api_base=body.llm.api_base,
        llm_api_key=body.llm.api_key,
        llm_auth_type=body.llm.auth_type,
        llm_model_id=body.llm.model_id,
        llm_params=json.dumps(body.llm.params) if body.llm.params else None,
        benchmark_name=body.benchmark.name,
        benchmark_category=body.benchmark.category,
        benchmark_config=json.dumps(body.benchmark.config),
        benchmark_metrics=json.dumps(body.benchmark.metrics) if body.benchmark.metrics else None,
        benchmark_params=json.dumps(body.benchmark.params) if body.benchmark.params else None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    sched.add_job(job)
    return _job_to_response(job)


@router.put("/{job_id}", response_model=ScheduleResponse)
async def update_schedule(
    job_id: int, body: ScheduleUpdate, db: AsyncSession = Depends(get_db)
):
    job = await db.get(ScheduledJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    if body.name is not None:
        job.name = body.name
    if body.cron_expr is not None:
        job.cron_expr = body.cron_expr
    if body.enabled is not None:
        job.enabled = body.enabled
    if body.llm is not None:
        job.llm_provider = body.llm.provider
        job.llm_api_base = body.llm.api_base
        # Only update key if user actually changed it (not the masked value)
        new_key = body.llm.api_key
        if new_key and "****" not in new_key:
            job.llm_api_key = new_key
        job.llm_auth_type = body.llm.auth_type
        job.llm_model_id = body.llm.model_id
        job.llm_params = json.dumps(body.llm.params) if body.llm.params else None
    if body.benchmark is not None:
        job.benchmark_name = body.benchmark.name
        job.benchmark_category = body.benchmark.category
        job.benchmark_config = json.dumps(body.benchmark.config)
        job.benchmark_metrics = json.dumps(body.benchmark.metrics) if body.benchmark.metrics else None
        job.benchmark_params = json.dumps(body.benchmark.params) if body.benchmark.params else None

    await db.commit()
    await db.refresh(job)

    sched.remove_job(job.id)
    if job.enabled:
        sched.add_job(job)

    return _job_to_response(job)


@router.delete("/{job_id}", status_code=204)
async def delete_schedule(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(ScheduledJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    sched.remove_job(job.id)
    await db.delete(job)
    await db.commit()


@router.post("/{job_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(ScheduledJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.enabled = not job.enabled
    await db.commit()
    await db.refresh(job)
    sched.toggle_job(job.id, job.enabled)
    return _job_to_response(job)


@router.post("/{job_id}/trigger", status_code=202)
async def trigger_schedule(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(ScheduledJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    from ..services.eval_engine import EvalEngine

    llm_params = json.loads(job.llm_params) if job.llm_params else {}
    bench_config = json.loads(job.benchmark_config)
    engine = EvalEngine(bench_config, {
        "provider": job.llm_provider,
        "api_base": job.llm_api_base,
        "api_key": job.llm_api_key,
        "auth_type": job.llm_auth_type,
        "model_id": job.llm_model_id,
        "params": llm_params,
    })

    from ..config import settings

    run_id, log_path = EvalEngine.create_run_record(job, settings.database_url, run_type="manual")

    import threading

    thread = threading.Thread(
        target=engine.run_sync,
        args=(run_id, settings.database_url, log_path),
        daemon=True,
    )
    thread.start()

    return {"run_id": run_id, "status": "started"}


@router.post("/test-connection")
async def test_connection(body: ScheduleTestConnection, db: AsyncSession = Depends(get_db)):
    api_key = body.api_key
    if api_key and "****" in api_key and body.schedule_id:
        job = await db.get(ScheduledJob, body.schedule_id)
        if job:
            api_key = job.llm_api_key
    client = LLMClient(
        provider=body.provider,
        api_base=body.api_base,
        api_key=api_key,
        auth_type=body.auth_type,
        model_id=body.model_id,
        params=body.params,
    )
    ok = client.test_connection()
    if ok:
        return {"success": True, "message": "Connection successful"}
    return {"success": False, "message": "Connection failed"}
