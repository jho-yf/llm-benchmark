import json
from pathlib import Path

from fastapi import APIRouter

from ..config import PRESETS_DIR

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])

_presets_cache: list[dict] | None = None

CATEGORIES = [
    {"id": "knowledge", "name": "综合知识"},
    {"id": "math", "name": "数学推理"},
    {"id": "reasoning", "name": "通用推理"},
    {"id": "coding", "name": "代码生成"},
    {"id": "reading", "name": "阅读理解"},
    {"id": "instruction", "name": "指令遵循"},
    {"id": "chat", "name": "对话能力"},
    {"id": "safety", "name": "安全对齐"},
    {"id": "long_context", "name": "长上下文"},
    {"id": "multilingual", "name": "多语言"},
]


def _load_presets() -> list[dict]:
    global _presets_cache
    if _presets_cache is not None:
        return _presets_cache

    presets = []
    for f in sorted(PRESETS_DIR.glob("*.json")):
        with open(f) as fh:
            presets.append(json.load(fh))
    _presets_cache = presets
    return presets


@router.get("/presets")
async def list_presets():
    return _load_presets()


@router.get("/categories")
async def list_categories():
    return CATEGORIES
