from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate: add columns if missing
        for col, col_type in [
            ("llm_model_id", "VARCHAR(200)"),
            ("benchmark_name", "VARCHAR(200)"),
            ("progress", "VARCHAR(50)"),
        ]:
            try:
                await conn.execute(
                    text(f"ALTER TABLE test_run ADD COLUMN {col} {col_type}")
                )
            except Exception:
                pass


async def get_db():
    async with async_session() as session:
        yield session
