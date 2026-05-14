# LLM Benchmark 开发任务清单

基于 [001-llm-benchmark-design.md](001-llm-benchmark-design.md)

## Phase 1: 后端基础

- [ ] **P1-1** 初始化后端项目结构
  - 创建 `backend/` 目录及 `pyproject.toml`、`requirements.txt`
  - 依赖：fastapi, uvicorn, sqlalchemy, aiosqlite, apscheduler, openai, lm-eval-harness, cryptography

- [ ] **P1-2** 数据库与模型
  - `app/database.py`：SQLite 连接、会话管理
  - `app/models/scheduled_job.py`：定时任务表（含内联模型/Benchmark 字段）
  - `app/models/test_run.py`：运行记录表
  - 启动时自动建表

- [ ] **P1-3** Pydantic Schemas
  - `app/schemas/schedule.py`：定时任务 CRUD 的请求/响应模型
  - `app/schemas/run.py`：运行记录的响应模型

- [ ] **P1-4** LLM 客户端
  - `app/services/llm_client.py`：统一 LLM Client
  - 支持 bearer / api_key / none 三种认证
  - `test_connection()` 连通性测试

- [ ] **P1-5** 评测引擎
  - `app/services/eval_engine.py`：封装 lm-evaluation-harness
  - 接收 benchmark_config + 运行参数，执行评测，返回结果
  - 写日志文件

- [ ] **P1-6** 定时调度
  - `app/services/scheduler.py`：APScheduler 封装
  - add / remove / toggle / trigger 操作
  - 应用启动时从数据库恢复已启用的定时任务

- [ ] **P1-7** API 路由
  - `app/routers/schedules.py`：定时任务 CRUD + toggle + trigger + test-connection
  - `app/routers/runs.py`：运行记录列表 + 详情 + SSE 日志流
  - `app/routers/benchmarks.py`：预设列表 + 分类列表

- [ ] **P1-8** 内置 Benchmark 预设
  - `presets/mmlu.json`、`presets/gsm8k.json`、`presets/humaneval.json` 等 8 个预设文件
  - 启动时加载到内存，通过 API 返回

- [ ] **P1-9** FastAPI 入口
  - `app/main.py`：注册路由、初始化调度器、静态文件服务
  - `app/config.py`：配置项（数据目录、日志目录等）

## Phase 2: 前端

- [ ] **P2-1** 初始化前端项目
  - Vue 3 + Vite + Tailwind CSS
  - `frontend/` 目录，`package.json`，`vite.config.js`，`tailwind.config.js`

- [ ] **P2-2** API 封装
  - `src/api/` 目录，封装所有后端 API 调用

- [ ] **P2-3** 单页面主体
  - `src/views/Schedules.vue`：定时任务列表 + 运行记录列表
  - 顶部标题 + 新建按钮
  - 定时任务表格（名称、模型、Benchmark、Cron、下次运行、状态、操作）
  - 运行记录表格（模型、Benchmark、开始、耗时、状态、结果）

- [ ] **P2-4** 任务表单组件
  - `src/components/ScheduleForm.vue`：新建/编辑定时任务
  - 模型配置区域：提供商、API 地址、认证方式、密钥/Token、模型标识、默认参数、测试连通性
  - Benchmark 配置区域：标准评测下拉框（选择后自动填充）、名称、分类、评测配置、运行参数

- [ ] **P2-5** 状态标签组件
  - `src/components/StatusBadge.vue`：颜色区分的运行状态标签

- [ ] **P2-6** App 壳
  - `src/App.vue`：引入 Schedules 视图

## Phase 3: 测试

- [ ] **P3-1** 后端单元测试
  - 测试框架：pytest + pytest-asyncio + httpx
  - `tests/test_llm_client.py`：LLM Client 各认证方式初始化、generate、test_connection（mock OpenAI SDK）
  - `tests/test_eval_engine.py`：EvalEngine 执行流程（mock lm-eval-harness）
  - `tests/test_scheduler.py`：定时任务增删、toggle、trigger
  - `tests/test_schemas.py`：Pydantic 模型校验（必填字段、类型校验）

- [ ] **P3-2** 后端 API 集成测试
  - `tests/test_api_schedules.py`：定时任务 CRUD + toggle + trigger + test-connection
  - `tests/test_api_runs.py`：运行记录列表 + 详情
  - `tests/test_api_benchmarks.py`：预设列表 + 分类列表
  - 使用 TestClient + 内存 SQLite，每个测试独立数据库

- [ ] **P3-3** 前端组件测试
  - 测试框架：Vitest + Vue Test Utils
  - `tests/ScheduleForm.spec.ts`：表单校验、预设下拉框自动填充、认证方式切换
  - `tests/StatusBadge.spec.ts`：各状态渲染正确颜色
  - `tests/Schedules.spec.ts`：任务列表渲染、运行记录展示

- [ ] **P3-4** 端到端测试
  - 启动完整前后端
  - 创建定时任务 → 测试连通性 → 手动触发 → 查看运行记录 → 验证状态流转

## Phase 4: 部署

- [ ] **P4-1** Dockerfile
  - 多阶段构建：前端 build → Python 运行镜像

- [ ] **P4-2** docker-compose.yml
  - 自动构建镜像，映射端口，持久化 data 和 logs 目录

- [ ] **P4-3** k8s/deployment.yaml
  - Deployment + Service 资源
  - PVC 持久化数据

## 任务依赖

```
P1-1 → P1-2 → P1-3 → P1-7
P1-1 → P1-4 → P1-5 → P1-7
P1-1 → P1-6 → P1-7
P1-7 → P1-9
P1-8 → P1-9

P2-1 → P2-2 → P2-3
P2-1 → P2-4
P2-3 → P2-5 → P2-6

P1-9 + P2-6 → P3-1 + P3-2 + P3-3 → P3-4

P3-4 → P4-1 → P4-2 → P4-3
```
