# LLM Benchmark 测试工具设计文档（MVP）

## 1. 概述

### 1.1 目标

构建一个轻量级的大模型 Benchmark 定时测试工具，核心功能：

- 在定时任务中内联配置大模型连接（支持 Bearer Token 认证）
- 在定时任务中内联配置 Benchmark 标准与参数
- 配置定时任务自动运行 Benchmark
- 手动触发测试运行
- 查看运行状态与结果

### 1.2 设计原则

- **轻量级**：最小化外部依赖，单机即可部署
- **简洁**：只有一个定时任务页面，模型和 Benchmark 配置内联在任务表单中
- **可扩展**：Benchmark 类型和模型接入可插件化扩展

## 2. LLM Benchmark 标准调研

### 2.1 主流 Benchmark 分类

| 类别 | 代表 Benchmark | 评测内容 |
|------|---------------|---------|
| **综合知识** | MMLU, MMLU-Pro, ARC, TriviaQA | 世界知识、学科理解 |
| **数学推理** | GSM8K, MATH, MGSM | 数学计算、多步推理 |
| **通用推理** | BBH, LogiQA, HellaSwag | 逻辑推理、常识推理 |
| **代码生成** | HumanEval, MBPP, SWE-bench | 代码编写与调试 |
| **阅读理解** | RACE, LAMBADA, WinoGrande | 阅读理解、指代消解 |
| **指令遵循** | IFEval, AlpacaEval | 指令理解与执行 |
| **对话能力** | MT-Bench, Chatbot Arena | 多轮对话质量 |
| **安全对齐** | TruthfulQA, ToxiGen | 真实性、安全性 |
| **长上下文** | LongBench, Needle-in-Haystack | 长文本理解与检索 |
| **多语言** | XNLI, MGSM | 跨语言能力 |

### 2.2 主流评估框架

| 框架 | 来源 | 特点 |
|------|------|------|
| **lm-evaluation-harness** | EleutherAI | 最广泛使用的开源评测框架，支持 60+ Benchmark |
| **HELM** | Stanford CRFM | 全面评估，含公平性/效率/偏见维度 |
| **BIG-bench** | Google | 200+ 任务，社区贡献 |
| **Open LLM Leaderboard** | HuggingFace | 基于 lm-eval-harness 的排行榜 |
| **Chatbot Arena** | LMSYS | 人类偏好对比评测 |

### 2.3 MVP 实现策略

封装 lm-evaluation-harness 作为评测引擎，基于 OpenAI API 兼容协议对接各模型提供商。

## 3. 系统架构

### 3.1 技术选型

采用**前后端分离**架构，保持轻量：

| 层次 | 技术栈 | 理由 |
|------|--------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS | 轻量、响应式、生态成熟 |
| 后端 | Python + FastAPI | 异步高性能，LLM 生态最丰富 |
| 数据库 | SQLite | 零配置，单机部署友好 |
| 定时任务 | APScheduler | 纯 Python，无需消息队列 |
| 评测引擎 | lm-evaluation-harness | 社区标准，任务覆盖广 |

### 3.2 架构图

```
┌───────────────────────────────────────────┐
│            Frontend (Vue 3)                │
│  ┌───────────────────────────────────────┐ │
│  │         定时任务管理（单页面）          │ │
│  │  ┌─────────────────┐ ┌─────────────┐  │ │
│  │  │ 任务列表+表单    │ │ 运行记录     │  │ │
│  │  │ (含模型/Bench配置)│ │             │  │ │
│  │  └─────────────────┘ └─────────────┘  │ │
│  └───────────────────────────────────────┘ │
└──────────────────┬────────────────────────┘
                   │ HTTP
┌──────────────────┴────────────────────────┐
│             Backend (FastAPI)               │
│  ┌───────────────────────────────────────┐ │
│  │            Schedule Router             │ │
│  └───────────────────────────────────────┘ │
│  ┌───────────────────────────────────────┐ │
│  │           Core Services                │ │
│  │  ┌──────────┐ ┌──────────┐ ┌────────┐ │ │
│  │  │LLMClient │ │EvalEngine│ │Scheduler│ │ │
│  │  └──────────┘ └──────────┘ └────────┘ │ │
│  └───────────────────────────────────────┘ │
│  ┌───────────────────────────────────────┐ │
│  │          SQLite (data store)           │ │
│  └───────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

## 4. 数据模型

### 4.1 定时任务 (scheduled_job)

模型和 Benchmark 配置内联在任务中，不单独建表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 任务名称 |
| cron_expr | TEXT | Cron 表达式 |
| enabled | BOOLEAN | 是否启用 |
| last_run_at | DATETIME | 上次运行时间 |
| next_run_at | DATETIME | 下次运行时间 |
| created_at | DATETIME | 创建时间 |
| **模型配置** | | |
| llm_provider | TEXT | 提供商 (openai / azure / anthropic / ollama / custom) |
| llm_api_base | TEXT | API 地址 |
| llm_api_key | TEXT | API 密钥 / Bearer Token（加密存储） |
| llm_auth_type | TEXT | 认证方式 (bearer / api_key / none) |
| llm_model_id | TEXT | 模型标识 (如 gpt-4o, claude-sonnet-4-6) |
| llm_params | JSON | 默认参数 (temperature, max_tokens 等) |
| **Benchmark 配置** | | |
| benchmark_name | TEXT | Benchmark 名称 |
| benchmark_category | TEXT | 分类 (knowledge / reasoning / coding / math / safety / custom) |
| benchmark_config | JSON | 评测配置（任务列表、few-shot 数等） |
| benchmark_metrics | JSON | 评价指标定义 (accuracy, pass@k 等) |
| benchmark_params | JSON | 运行参数覆盖 |

### 4.2 运行记录 (test_run)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| scheduled_job_id | INTEGER FK | 关联定时任务（手动触发时为空） |
| status | TEXT | 状态 (pending / running / completed / failed) |
| result | JSON | 测试结果（各指标得分） |
| log_path | TEXT | 日志文件路径 |
| started_at | DATETIME | 开始时间 |
| finished_at | DATETIME | 结束时间 |
| created_at | DATETIME | 创建时间 |

## 5. API 设计

只有定时任务和运行记录两个路由组：

### 5.1 定时任务

```
GET    /api/schedules           # 列出所有定时任务
POST   /api/schedules           # 创建定时任务（含模型+Benchmark配置）
PUT    /api/schedules/:id       # 更新定时任务
DELETE /api/schedules/:id       # 删除定时任务
POST   /api/schedules/:id/toggle  # 启用/禁用定时任务
POST   /api/schedules/:id/trigger # 手动触发一次
POST   /api/schedules/test-connection  # 测试模型连通性
```

### 5.2 运行记录

```
GET    /api/runs                # 列出运行记录
GET    /api/runs/:id            # 获取运行详情（含结果）
GET    /api/runs/:id/log        # 获取运行日志（SSE 流式）
```

### 5.3 辅助

```
GET    /api/benchmarks/presets     # 获取内置 Benchmark 预设列表（用于下拉框）
GET    /api/benchmarks/categories  # 获取 Benchmark 分类列表
```

预设接口返回格式：

```json
[
  {
    "id": "mmlu-5shot",
    "name": "MMLU (5-shot)",
    "category": "knowledge",
    "config": {
      "tasks": ["mmlu"],
      "num_fewshot": {"mmlu": 5},
      "limit": null,
      "batch_size": "auto"
    },
    "metrics": {"accuracy": "acc"},
    "description": "大规模多任务语言理解，57个学科"
  }
]
```

## 6. Benchmark 评测引擎

### 6.1 评测配置格式

封装 lm-evaluation-harness，直接运行其内置任务：

```json
{
  "tasks": ["mmlu", "gsm8k", "humaneval"],
  "num_fewshot": {
    "mmlu": 5,
    "gsm8k": 8,
    "humaneval": 0
  },
  "limit": null,
  "batch_size": "auto"
}
```

### 6.2 评测执行流程

```
┌─────────┐    ┌──────────────┐    ┌────────────┐    ┌──────────┐
│ 创建任务 │───▶│ 初始化 LLM   │───▶│ 加载数据集  │───▶│ 逐条评测  │
└─────────┘    └──────────────┘    └────────────┘    └──────────┘
                                                          │
┌─────────┐    ┌──────────────┐    ┌────────────┐         │
│ 存储结果 │◀───│ 生成报告     │◀───│ 计算指标   │◀────────┘
└─────────┘    └──────────────┘    └────────────┘
```

1. 初始化 LLM Client（根据 provider、auth_type 和 api_base 创建客户端）
2. 加载数据集（从 lm-eval-harness 内置）
3. 逐条评测（调用 LLM API，收集响应）
4. 计算指标（accuracy, pass@k, F1 等）
5. 存储结果到数据库

### 6.3 内置 Benchmark 预设

| 预设名称 | 类别 | 任务数 | Few-shot | 预计耗时 |
|----------|------|--------|----------|---------|
| MMLU (5-shot) | 知识 | 14042 | 5 | ~30min |
| GSM8K (8-shot) | 数学 | 1319 | 8 | ~15min |
| HumanEval (0-shot) | 代码 | 164 | 0 | ~10min |
| MATH (4-shot) | 数学 | 5000 | 4 | ~45min |
| BBH (3-shot) | 推理 | 6511 | 3 | ~40min |
| TruthfulQA (0-shot) | 安全 | 817 | 0 | ~8min |
| HellaSwag (10-shot) | 常识 | 10042 | 10 | ~35min |
| ARC-Challenge (25-shot) | 推理 | 1172 | 25 | ~12min |

## 7. 定时任务设计

### 7.1 调度器

使用 APScheduler 的 BackgroundScheduler：

- 支持 Cron 表达式（如 `0 2 * * 0` = 每周日凌晨 2 点）
- 应用重启后自动恢复调度

### 7.2 定时任务示例

```
名称：每周 MMLU 评测
Cron：0 2 * * 0
模型：provider=openai, api_base=https://api.openai.com/v1, auth_type=api_key, model_id=gpt-4o
Benchmark：name=MMLU 5-shot, config={tasks:["mmlu"], num_fewshot:5}
```

### 7.3 并发控制

- 同一任务同一时刻只允许一个运行实例
- 后续触发跳过，避免 API 限流

## 8. 前端页面设计

### 8.1 单页面布局

```
┌──────────────────────────────────────────────────────────┐
│  LLM Benchmark                                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [+ 新建定时任务]                                         │
│                                                          │
│  ┌──────┬──────┬────────┬──────┬────────┬──────┬──────┐  │
│  │ 名称  │ 模型  │Benchmark│ Cron  │下次运行 │ 状态  │ 操作 │  │
│  ├──────┼──────┼────────┼──────┼────────┼──────┼──────┤  │
│  │每周MMLU│gpt-4o│MMLU 5s  │0 2*0 │05/18   │ ✅启用 │▶ ✏ 🗑│  │
│  │每日GSM8K│qwen  │GSM8K 8s │0 3*  │05/15   │ ⏸停用 │▶ ✏ 🗑│  │
│  └──────┴──────┴────────┴──────┴────────┴──────┴──────┘  │
│                                                          │
│  ── 运行记录 ────────────────────────────────────────────  │
│  ┌──────┬──────┬────────┬──────┬──────┬────────────────┐  │
│  │ 模型  │Bench │ 开始    │ 耗时  │ 状态  │ 结果           │  │
│  ├──────┼──────┼────────┼──────┼──────┼────────────────┤  │
│  │gpt-4o│MMLU  │05/11 02:00│28min │ ✓完成 │ acc=0.762     │  │
│  │qwen  │GSM8K │05/12 03:00│12min │ ✓完成 │ acc=0.714     │  │
│  │gpt-4o│MMLU  │05/12 02:00│—     │ ⟳运行中│ —             │  │
│  └──────┴──────┴────────┴──────┴──────┴────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 8.2 新建/编辑任务表单

模型和 Benchmark 配置内联在表单中：

```
┌─────────────────────────────────────────────┐
│ 新建定时任务                                  │
├─────────────────────────────────────────────┤
│ 任务名称：[              ]                    │
│ Cron 表达式：[0 2 * * 0]                     │
│                                             │
│ ── 模型配置 ────────────────────────────────  │
│ 提供商：    [openai      ▼]                  │
│ API 地址：  [https://api.openai.com/v1     ] │
│ 认证方式：  (●) Bearer Token  (○) API Key    │
│ 密钥/Token：[sk-*********                  ] │
│ 模型标识：  [gpt-4o                         ] │
│ 默认参数：  {"temperature":0, "max_tokens":2048}│
│                          [测试连通性]         │
│                                             │
│ ── Benchmark 配置 ──────────────────────────  │
│ 标准评测：  [MMLU 5-shot    ▼]  ← 选择后自动填充下方配置 │
│ 名称：     [MMLU 5-shot                      ]│
│ 分类：     [knowledge      ▼]                │
│ 评测配置： [{"tasks":["mmlu"],"num_fewshot":5}]│
│ 运行参数： [{"limit":null}]                  │
│                                             │
│              [取消]  [保存]                   │
└─────────────────────────────────────────────┘
```

### 8.3 UI 规范

- 使用 Tailwind CSS，页面宽度 1200px 居中
- 主色调：深灰 + 蓝色强调
- 表格使用紧凑样式，减少留白
- 状态标签颜色：绿色完成 / 蓝色运行中 / 红色失败 / 灰色待执行

## 9. 项目结构

```
llm-benchmark/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # SQLite 连接
│   │   ├── models/                 # SQLAlchemy 模型
│   │   │   ├── scheduled_job.py
│   │   │   └── test_run.py
│   │   ├── routers/                # API 路由
│   │   │   ├── schedules.py
│   │   │   └── runs.py
│   │   ├── services/               # 业务逻辑
│   │   │   ├── llm_client.py       # LLM API 客户端
│   │   │   ├── eval_engine.py      # 评测引擎
│   │   │   └── scheduler.py        # 定时调度
│   │   └── schemas/                # Pydantic 模型
│   │       ├── schedule.py
│   │       └── run.py
│   ├── presets/                    # 内置 Benchmark 预设
│   │   ├── mmlu.json
│   │   ├── gsm8k.json
│   │   └── humaneval.json
│   ├── data/                       # 数据目录
│   │   └── benchmark.db
│   ├── logs/                       # 运行日志
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── Schedules.vue       # 单页面
│   │   ├── components/
│   │   │   ├── ScheduleForm.vue    # 新建/编辑定时任务（含模型+Bench配置）
│   │   │   ├── RunHistory.vue      # 运行记录表格
│   │   │   └── StatusBadge.vue     # 状态标签
│   │   ├── api/                    # API 调用封装
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── specs/
│   └── 001-llm-benchmark-design.md  # 本文档
├── instructions.md
└── README.md
```

## 10. 关键实现细节

### 10.1 LLM 客户端

统一接口，适配不同认证方式和提供商：

```python
class LLMClient:
    """统一的 LLM API 客户端，基于 OpenAI 兼容协议"""

    def __init__(self, provider: str, api_base: str, api_key: str,
                 auth_type: str, model_id: str, params: dict):
        self.model_id = model_id
        self.default_params = params

        if auth_type == "bearer":
            self.client = OpenAI(
                api_key="not-needed",
                base_url=api_base,
                default_headers={"Authorization": f"Bearer {api_key}"},
            )
        elif auth_type == "api_key":
            self.client = OpenAI(
                api_key=api_key,
                base_url=api_base,
            )
        else:
            self.client = OpenAI(
                api_key="not-needed",
                base_url=api_base,
            )

    async def generate(self, prompt: str, **kwargs) -> str:
        params = {**self.default_params, **kwargs}
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            **params,
        )
        return response.choices[0].message.content

    async def test_connection(self) -> bool:
        try:
            await self.generate("Hello", max_tokens=5)
            return True
        except Exception:
            return False
```

认证方式说明：
- **bearer**：通过 `Authorization: Bearer <token>` 请求头传递，适用于自部署模型服务（vLLM、TGI 等）
- **api_key**：OpenAI 标准方式（SDK 默认行为）
- **none**：无认证，适用于本地服务如 Ollama

### 10.2 评测引擎

```python
class EvalEngine:
    def __init__(self, llm_client: LLMClient, benchmark_config: dict):
        self.client = llm_client
        self.config = benchmark_config

    async def run(self, params: dict, on_progress: Callable) -> dict:
        config = {**self.config, **params}
        result = await self._run_lm_eval(config, on_progress)
        return result

    async def _run_lm_eval(self, config, on_progress):
        # 调用 lm-evaluation-harness
        ...
```

### 10.3 定时调度

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def add_job(self, job_id: str, cron_expr: str, func: Callable):
        trigger = CronTrigger.from_crontab(cron_expr)
        self.scheduler.add_job(func, trigger, id=job_id)

    def remove_job(self, job_id: str):
        self.scheduler.remove_job(job_id)

    def toggle_job(self, job_id: str, enabled: bool):
        if enabled:
            self.scheduler.resume_job(job_id)
        else:
            self.scheduler.pause_job(job_id)
```

### 10.4 实时日志推送

```python
@router.get("/api/runs/{run_id}/log")
async def stream_log(run_id: int):
    async def event_generator():
        async for line in tail_log_file(run_id):
            yield f"data: {line}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

## 11. 部署方案

### 11.1 开发模式

```bash
# 后端
cd backend && uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm run dev -- --port 3000
```

### 11.2 生产部署

前端 build 后放入 FastAPI 的 static 目录，单进程运行：

```bash
cd frontend && npm run build
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 11.3 Docker（可选）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/ ./backend/
COPY frontend/dist/ ./backend/static/
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 12. 后续扩展

- **结果看板**：多模型对比表格、历史趋势图、导出功能
- **模型/Benchmark 抽取**：当任务增多时，将模型和 Benchmark 配置抽取为独立管理
- **自定义 Prompt 测试**：用户自定义 prompt 模板 + 评判标准
- **对比评测**：多模型同题对比
- **通知集成**：评测完成后 Webhook 推送至 Slack / 飞书
- **分布式**：Celery + Redis 替换 APScheduler
