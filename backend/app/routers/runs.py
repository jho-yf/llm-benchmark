import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import TestRun
from ..schemas.run import RunResponse

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _run_to_response(run: TestRun) -> RunResponse:
    return RunResponse(
        id=run.id,
        scheduled_job_id=run.scheduled_job_id,
        llm_model_id=run.llm_model_id,
        benchmark_name=run.benchmark_name,
        status=run.status,
        progress=run.progress,
        result=json.loads(run.result) if run.result else None,
        log_path=run.log_path,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )


@router.get("", response_model=list[RunResponse])
async def list_runs(
    model: str | None = None,
    benchmark: str | None = None,
    status: str | None = None,
    job_id: int | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TestRun).order_by(TestRun.id.desc())
    if model:
        stmt = stmt.where(TestRun.llm_model_id.ilike(f"%{model}%"))
    if benchmark:
        stmt = stmt.where(TestRun.benchmark_name.ilike(f"%{benchmark}%"))
    if status:
        stmt = stmt.where(TestRun.status == status)
    if job_id:
        stmt = stmt.where(TestRun.scheduled_job_id == job_id)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return [_run_to_response(r) for r in result.scalars().all()]


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return _run_to_response(run)


@router.get("/{run_id}/log")
async def stream_log(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if not run.log_path:
        return StreamingResponse(iter(["data: No log file\n\n"]), media_type="text/event-stream")

    log_path_str = run.log_path

    async def tail():
        import asyncio
        from pathlib import Path

        path = Path(log_path_str)
        # Wait for file to appear (subprocess may not have started writing yet)
        for _ in range(20):
            if path.exists():
                break
            await asyncio.sleep(0.5)

        if not path.exists():
            yield "data: Log file not found\n\n"
            return

        with open(path) as f:
            # Seek to last 500 lines for large log files
            try:
                f.seek(0, 2)
                file_size = f.tell()
                chunk = min(file_size, 128 * 1024)
                f.seek(max(0, file_size - chunk))
                tail_lines = f.read().splitlines()[-500:]
                for l in tail_lines:
                    if l:
                        yield f"data: {l}\n\n"
            except Exception:
                f.seek(0)

            while True:
                line = f.readline()
                if line:
                    yield f"data: {line.rstrip()}\n\n"
                else:
                    # Check run status from DB (survives hot reload)
                    from sqlalchemy import select
                    stmt = select(TestRun.status).where(TestRun.id == run_id)
                    r = await db.execute(stmt)
                    row = r.scalar_one_or_none()
                    if row and row != "running":
                        # Read any remaining content
                        remaining = f.read()
                        for l in remaining.splitlines():
                            if l:
                                yield f"data: {l}\n\n"
                        break
                    await asyncio.sleep(0.5)

    return StreamingResponse(tail(), media_type="text/event-stream")


class DeleteRunsRequest(BaseModel):
    ids: list[int]


@router.post("/delete", status_code=200)
async def delete_runs(body: DeleteRunsRequest, db: AsyncSession = Depends(get_db)):
    if not body.ids:
        return {"deleted": 0}
    stmt = delete(TestRun).where(TestRun.id.in_(body.ids), TestRun.status != "running")
    result = await db.execute(stmt)
    await db.commit()
    return {"deleted": result.rowcount}


@router.post("/{run_id}/cancel", status_code=200)
async def cancel_run(run_id: int, db: AsyncSession = Depends(get_db)):
    from ..services.eval_engine import cancel_run as do_cancel

    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status != "running":
        raise HTTPException(400, "Run is not running")

    cancelled = do_cancel(run_id)
    if not cancelled:
        run.status = "cancelled"
        await db.commit()

    return {"cancelled": True}
