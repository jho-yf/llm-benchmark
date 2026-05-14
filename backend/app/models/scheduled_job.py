from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ScheduledJob(AsyncAttrs, Base):
    __tablename__ = "scheduled_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cron_expr: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # LLM config
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_api_base: Mapped[str] = mapped_column(String(500), nullable=False)
    llm_api_key: Mapped[str] = mapped_column(Text, nullable=True)
    llm_auth_type: Mapped[str] = mapped_column(String(20), nullable=False, default="bearer")
    llm_model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    llm_params: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Benchmark config
    benchmark_name: Mapped[str] = mapped_column(String(200), nullable=False)
    benchmark_category: Mapped[str] = mapped_column(String(50), nullable=False)
    benchmark_config: Mapped[str] = mapped_column(Text, nullable=False)
    benchmark_metrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    benchmark_params: Mapped[str | None] = mapped_column(Text, nullable=True)
