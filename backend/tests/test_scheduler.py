from unittest.mock import patch, MagicMock

from app.services.scheduler import add_job, remove_job, toggle_job


def test_add_job():
    job = MagicMock()
    job.id = 1
    job.cron_expr = "0 2 * * 0"

    with patch("app.services.scheduler.get_scheduler") as mock_sched:
        add_job(job)
        mock_sched.return_value.add_job.assert_called_once()


def test_remove_job():
    with patch("app.services.scheduler.get_scheduler") as mock_sched:
        remove_job(42)
        mock_sched.return_value.remove_job.assert_called_once_with("benchmark_42")


def test_toggle_job_enable():
    with patch("app.services.scheduler.get_scheduler") as mock_sched:
        toggle_job(1, True)
        mock_sched.return_value.resume_job.assert_called_once_with("benchmark_1")


def test_toggle_job_disable():
    with patch("app.services.scheduler.get_scheduler") as mock_sched:
        toggle_job(1, False)
        mock_sched.return_value.pause_job.assert_called_once_with("benchmark_1")
