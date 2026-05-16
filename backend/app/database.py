from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _set_wal_mode(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA busy_timeout=30000")


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate: add columns if missing
        for table, col, col_type, default in [
            ("test_run", "llm_model_id", "VARCHAR(200)", None),
            ("test_run", "benchmark_name", "VARCHAR(200)", None),
            ("test_run", "progress", "VARCHAR(50)", None),
            ("scheduled_job", "llm_stream", "BOOLEAN", True),
        ]:
            try:
                sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                if default is not None:
                    sql += f" DEFAULT {1 if default else 0}"
                await conn.execute(text(sql))
            except Exception:
                pass


async def get_db():
    async with async_session() as session:
        yield session
