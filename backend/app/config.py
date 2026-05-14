import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
PRESETS_DIR = BASE_DIR / "presets"
DATASETS_DIR = Path(os.environ.get("HF_DATASETS_CACHE", str(BASE_DIR.parent / "datasets")))


class Settings:
    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'benchmark.db'}"

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
