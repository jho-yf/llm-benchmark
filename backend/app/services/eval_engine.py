import json
import logging
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import LOGS_DIR
from ..models import ScheduledJob, TestRun

logger = logging.getLogger(__name__)

_running: dict[int, subprocess.Popen] = {}


def cancel_run(run_id: int) -> bool:
    """Kill a running eval subprocess. Returns True if it was running."""
    proc = _running.get(run_id)
    if proc and proc.poll() is None:
        proc.terminate()
        return True
    return False


class EvalEngine:
    def __init__(self, benchmark_config: dict, llm_config: dict):
        self.config = benchmark_config
        self.llm_config = llm_config

    def run_sync(
        self,
        run_id: int,
        db_url: str,
        log_path: str | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> dict:
        """Run evaluation in a subprocess (called from scheduler thread)."""
        import re
        import select as sel
        import tempfile
        import time

        payload = {
            "benchmark_config": self.config,
            "llm_config": self.llm_config,
        }
        payload_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="eval_"
        )
        json.dump(payload, payload_file)
        payload_file.close()

        worker_script = str(Path(__file__).parent / "eval_worker.py")
        proc = subprocess.Popen(
            [sys.executable, "-u", worker_script, payload_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        _running[run_id] = proc

        progress_re = re.compile(r"(\d+)/(\d+)")
        benchmark_re = re.compile(r"\[benchmark (\d+)/(\d+)\]\s+(\S+)(?:\s+(\S+))?")
        last_progress = ""
        last_progress_update = 0
        current_benchmark = ""
        benchmark_total = ""
        benchmark_idx = ""
        current_stage = ""

        STALL_TIMEOUT = 600  # 10 minutes with no output = stuck

        try:
            log_file = open(log_path, "w") if log_path else None
            stderr_chunks = []
            current_line = ""
            last_output_time = time.time()

            while True:
                # Use select to avoid blocking forever if subprocess is stuck
                if hasattr(proc.stderr, 'fileno') and proc.poll() is None:
                    ready, _, _ = sel.select([proc.stderr], [], [], 30)
                    if not ready:
                        # No data for 30s, check if stalled
                        if time.time() - last_output_time > STALL_TIMEOUT:
                            logger.error("Eval subprocess stalled for %ds, killing", STALL_TIMEOUT)
                            proc.terminate()
                            try:
                                proc.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                proc.kill()
                                proc.wait()
                            self._update_run_status(
                                db_url, run_id, "failed",
                                json.dumps({"error": f"Evaluation stalled (no output for {STALL_TIMEOUT}s)"}),
                            )
                            return {}
                        continue
                chunk = proc.stderr.read1(4096) if hasattr(proc.stderr, 'read1') else proc.stderr.read(4096)
                if not chunk:
                    break
                last_output_time = time.time()
                text = chunk.decode(errors="replace")
                stderr_chunks.append(text)
                sys.stderr.write(text)
                sys.stderr.flush()

                if log_file:
                    log_file.write(text)
                    log_file.flush()

                current_line += text
                if '\r' in current_line or '\n' in current_line:
                    # Detect current benchmark from [benchmark 1/3] task_name stage
                    if "[partial_result]" in current_line:
                        try:
                            partial_json = current_line[current_line.index("[partial_result]") + len("[partial_result]"):].strip()
                            self._update_partial_result(db_url, run_id, partial_json)
                        except Exception:
                            pass

                    bm = benchmark_re.search(current_line)
                    if bm:
                        benchmark_idx = bm.group(1)
                        benchmark_total = bm.group(2)
                        current_benchmark = bm.group(3)
                        current_stage = bm.group(4) or ""

                    m = progress_re.search(current_line)
                    if m:
                        progress = f"{m.group(1)}/{m.group(2)}"
                        now = time.time()
                        if progress != last_progress and now - last_progress_update >= 2:
                            last_progress = progress
                            last_progress_update = now
                            if current_benchmark:
                                display = f"{current_benchmark}: {progress}"
                                if benchmark_total and benchmark_total != "1":
                                    display = f"({benchmark_idx}/{benchmark_total}) {display}"
                            else:
                                display = progress
                            self._update_progress(db_url, run_id, display)
                    elif bm and current_stage:
                        # Stage change without numeric progress
                        display = f"{current_benchmark} {current_stage}"
                        if benchmark_total and benchmark_total != "1":
                            display = f"({benchmark_idx}/{benchmark_total}) {display}"
                        now = time.time()
                        if now - last_progress_update >= 2:
                            last_progress_update = now
                            self._update_progress(db_url, run_id, display)
                    current_line = current_line.split('\r')[-1].split('\n')[-1]

            if log_file:
                log_file.close()

            proc.wait()

            if proc.returncode == -15 or proc.returncode == -9:
                self._update_run_status(
                    db_url, run_id, "cancelled",
                    json.dumps({"error": "cancelled by user"}),
                )
                return {}
            if proc.returncode != 0:
                error_msg = "".join(stderr_chunks)[-2000:]
                logger.error("Eval subprocess failed for run %d: %s", run_id, error_msg)
                self._update_run_status(
                    db_url, run_id, "failed",
                    json.dumps({"error": error_msg}),
                )
                return {}

            stdout = proc.stdout.read()
            result = json.loads(stdout.decode())
            if result.get("error"):
                logger.warning("Eval returned error for run %d: %s", run_id, result["error"])
                self._update_run_status(
                    db_url, run_id, "failed", json.dumps(result)
                )
                return result
            self._update_run_status(
                db_url, run_id, "completed", json.dumps(result)
            )
            return result
        except Exception as e:
            logger.exception("Eval failed for run %d", run_id)
            self._update_run_status(
                db_url, run_id, "failed", json.dumps({"error": str(e)})
            )
            raise
        finally:
            _running.pop(run_id, None)
            Path(payload_file.name).unlink(missing_ok=True)

    def _sync_engine(self, db_url: str):
        from sqlalchemy import create_engine, event
        sync_url = db_url.replace("+aiosqlite", "")
        eng = create_engine(sync_url, connect_args={"timeout": 30})

        @event.listens_for(eng, "connect")
        def _set_wal(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA busy_timeout=30000")

        return eng

    def _update_progress(self, db_url: str, run_id: int, progress: str):
        """Update progress field in DB."""
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        with Session(self._sync_engine(db_url)) as session:
            session.execute(
                text("UPDATE test_run SET progress=:progress WHERE id=:id"),
                {"progress": progress, "id": run_id},
            )
            session.commit()

    def _update_partial_result(self, db_url: str, run_id: int, result_json: str):
        """Write partial result to DB while run is still in progress."""
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        with Session(self._sync_engine(db_url)) as session:
            session.execute(
                text("UPDATE test_run SET result=:result WHERE id=:id"),
                {"result": result_json, "id": run_id},
            )
            session.commit()

    def _update_run_status(
        self, db_url: str, run_id: int, status: str, result: str
    ):
        """Update test run status in a separate sync session."""
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        with Session(self._sync_engine(db_url)) as session:
            session.execute(
                text(
                    "UPDATE test_run SET status=:status, result=:result, "
                    "finished_at=:finished_at WHERE id=:id"
                ),
                {
                    "status": status,
                    "result": result,
                    "finished_at": datetime.now(timezone.utc),
                    "id": run_id,
                },
            )
            session.commit()

    @staticmethod
    def create_run_record(
        job: ScheduledJob, db_url: str, run_type: str = "scheduled"
    ) -> tuple[int, str]:
        """Create a test_run record and return (run_id, log_path)."""
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session

        log_file = LOGS_DIR / f"run_{uuid.uuid4().hex[:8]}.log"
        sync_url = db_url.replace("+aiosqlite", "")
        from sqlalchemy import event as sa_event
        engine = create_engine(sync_url, connect_args={"timeout": 30})

        @sa_event.listens_for(engine, "connect")
        def _set_wal(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA busy_timeout=30000")
        with Session(engine) as session:
            result = session.execute(
                text(
                    "INSERT INTO test_run (scheduled_job_id, llm_model_id, benchmark_name, "
                    "status, log_path, started_at, created_at) "
                    "VALUES (:jid, :model, :bench, :status, :log, :started, :created)"
                ),
                {
                    "jid": job.id,
                    "model": job.llm_model_id,
                    "bench": job.benchmark_name,
                    "status": "running",
                    "log": str(log_file),
                    "started": datetime.now(timezone.utc),
                    "created": datetime.now(timezone.utc),
                },
            )
            session.commit()
            return result.lastrowid, str(log_file)
