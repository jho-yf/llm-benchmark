# LLM Benchmark

LLM Benchmark 是一个面向大模型 API 的基准评测管理工具。项目提供 Web 界面创建和管理定时评测任务，后端通过 `lm-eval` 调用兼容 OpenAI Chat Completions 的模型服务执行评测，并记录运行进度、日志、结果报告和 token/延迟统计。

## 功能特性

- 定时评测任务管理：创建、编辑、复制、启停、手动触发和批量删除任务。
- 运行记录管理：查看运行状态、进度、耗时、报告、错误详情和实时日志。
- 评测计划导入导出：支持将任务配置导出为 JSON，并重新导入。
- 预置 Benchmark：内置 MMLU、C-Eval、GSM8K、HumanEval、LongBench 等评测预设。
- Chat API 兼容：基于 `lm-eval` 的 `local-chat-completions` 模型入口，自动拼接 `/chat/completions`。
- 流式响应支持：可为评测请求启用 `stream: true`，并在后端聚合 SSE 输出。
- 并发和参数配置：支持 `num_concurrent`、`batch_size`、`limit`、`generation_kwargs` 等评测参数。
- 离线数据集支持：可提前下载 Hugging Face 数据集并打包进镜像，在容器或 Kubernetes 中离线运行。

## 技术栈

- 后端：Python 3.11、FastAPI、SQLAlchemy Async、SQLite、APScheduler、OpenAI SDK、lm-eval
- 前端：Vue 3、Vite、Tailwind CSS、Axios
- 部署：Docker / Podman、Docker Compose、Kubernetes

## 目录结构

```text
.
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # API 路由：任务、运行记录、Benchmark 预设
│   │   ├── services/        # 调度、评测执行、LLM 连接测试
│   │   ├── models/          # SQLAlchemy 模型
│   │   └── schemas/         # Pydantic 数据结构
│   ├── presets/             # Benchmark 预设配置
│   ├── tasks/               # lm-eval 自定义任务
│   ├── tests/               # 后端测试
│   └── preload_datasets.py  # 数据集预下载脚本
├── frontend/                # Vue 前端
├── k8s/                     # Kubernetes 部署配置
├── specs/                   # 设计和任务说明
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## 环境要求

- Python 3.11+
- Node.js 22+，npm
- Docker 或 Podman（可选，用于容器部署）
- 可访问的 OpenAI Chat Completions 兼容模型 API

## 本地开发

### 1. 初始化依赖

```bash
make setup
```

该命令会：

- 在 `backend/.venv` 创建 Python 虚拟环境并安装后端依赖。
- 在 `frontend/` 安装 npm 依赖。

### 2. 下载评测数据集

```bash
make download-datasets
```

数据集会下载到项目根目录的 `datasets/`，供本地和容器离线评测使用。该目录已按项目用途作为运行时数据目录处理，不建议提交到 Git。

### 3. 启动开发服务

```bash
make dev
```

默认服务地址：

- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:8000`
- 健康检查：`http://localhost:8000/api/health`

停止本地服务：

```bash
make stop
```

## 使用说明

### 创建评测任务

在 Web 页面点击“新建定时任务”，填写：

1. 任务名称和 Cron 表达式。
2. LLM API 配置：
   - `api_base`：模型服务地址，可填写基础地址或完整 `/chat/completions` 地址。
   - `api_key`：API 密钥。
   - `auth_type`：鉴权方式，支持 Bearer、API Key 或无鉴权。
   - `model_id`：模型 ID。
   - `stream`：是否启用流式响应。
   - `params`：模型调用参数，例如 `temperature`、`max_tokens`、`num_concurrent`。
3. Benchmark 配置：选择预设或自定义任务、few-shot、样本限制、batch size 等参数。

Cron 表达式使用标准 5 段格式，例如：

```text
0 2 * * *     # 每天 02:00 执行
*/30 * * * *  # 每 30 分钟执行一次
0 9 * * 1-5   # 工作日 09:00 执行
```

### 手动触发和查看结果

任务创建后，可以在任务列表中点击“触发”立即执行一次。运行记录中可查看：

- `running`：运行中，显示当前 Benchmark 和样本进度。
- `completed`：执行完成，可查看报告。
- `failed`：执行失败，可查看错误详情。
- `cancelled`：手动终止。

运行中任务支持查看实时日志和终止执行。

### 导入导出任务

页面右上角提供导入和导出按钮：

- 导出：将全部或选中的计划任务保存为 JSON。
- 导入：选择导出的 JSON 文件批量创建任务。

注意：导出的任务配置包含 API Key，请妥善保管导出文件。

## Benchmark 预设

预设位于 `backend/presets/`，当前包含：

- `mmlu.json`：MMLU 生成式评测。
- `ceval.json`：C-Eval 生成式评测。
- `gsm8k.json`：数学推理评测。
- `humaneval.json`：代码生成评测。
- `longbench.json`：长上下文评测。

后端还在 `backend/tasks/` 中提供 C-Eval 和 HumanEval 的自定义 `lm-eval` 任务定义。对于部分与 Chat API 不兼容的 multiple choice / loglikelihood 任务，评测 worker 会自动映射到生成式任务或跳过不兼容任务。

## 数据与日志

默认运行时文件：

- SQLite 数据库：`backend/data/benchmark.db`
- 运行日志：`backend/logs/*.log`
- Hugging Face 数据集缓存：`datasets/`
- Hugging Face Hub 缓存：`hf_cache/`

后端启动时会自动初始化数据库，并恢复数据库中处于启用状态的定时任务。

## API 概览

- `GET /api/health`：健康检查。
- `GET /api/benchmarks/presets`：获取 Benchmark 预设。
- `GET /api/benchmarks/categories`：获取 Benchmark 分类。
- `GET /api/schedules`：获取计划任务列表。
- `POST /api/schedules`：创建计划任务。
- `PUT /api/schedules/{id}`：更新计划任务。
- `DELETE /api/schedules/{id}`：删除计划任务。
- `POST /api/schedules/{id}/toggle`：启用或停用任务。
- `POST /api/schedules/{id}/trigger`：手动触发任务。
- `POST /api/schedules/import`：导入任务。
- `GET /api/schedules/export`：导出任务。
- `POST /api/schedules/test-connection`：测试模型 API 连接。
- `GET /api/runs`：获取运行记录。
- `GET /api/runs/{id}`：获取单次运行详情。
- `GET /api/runs/{id}/log`：以 SSE 方式读取运行日志。
- `POST /api/runs/{id}/cancel`：终止运行。
- `POST /api/runs/delete`：批量删除非运行中的记录。

## 测试

运行后端测试：

```bash
make test
```

或直接执行：

```bash
cd backend
.venv/bin/pytest tests/ -v
```

## 构建前端

```bash
make build-frontend
```

构建产物位于 `frontend/dist/`。

## 容器部署

### Docker Compose / Podman Compose

```bash
make up
```

服务默认暴露在：

```text
http://localhost:8080
```

查看日志：

```bash
make logs
```

停止服务：

```bash
make down
```

Compose 会挂载以下命名卷：

- `benchmark-data`：持久化数据库。
- `benchmark-logs`：持久化运行日志。

### 构建镜像

```bash
make compose-build
```

或：

```bash
docker build -t llm-benchmark:latest .
```

Dockerfile 会先构建前端，再将前端静态文件复制到后端镜像中，由 FastAPI 在生产模式下统一提供页面和 API。

## Kubernetes 部署

项目提供基础配置：

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

部署前请根据实际环境确认镜像地址、存储卷、服务类型和网络访问策略。

## 离线运行说明

镜像运行时默认设置：

```text
HF_DATASETS_OFFLINE=1
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
HF_ALLOW_CODE_EVAL=1
```

因此容器内评测依赖镜像中已经存在的 `datasets/` 和 `hf_cache/`。如果需要完全离线运行，请先在联网环境执行数据集预下载，并确保构建镜像时项目根目录存在对应缓存目录。

```bash
make download-datasets
# 如需完整离线加载 Hugging Face Hub 脚本，也需要准备 hf_cache/
docker build -t llm-benchmark:latest .
```

## 清理

```bash
make clean
```

该命令会删除前端构建和依赖目录、数据集缓存、数据库、日志以及 Python 缓存文件。执行前请确认不再需要本地运行数据。

## 注意事项

- 当前 API Key 保存在本地 SQLite 数据库中，接口返回时会做掩码处理，但导出任务会包含原始 Key。
- 评测任务会调用外部模型 API，可能产生推理费用，请合理设置 `limit` 和并发参数。
- HumanEval 等代码类评测需要允许执行代码，项目默认设置了 `HF_ALLOW_CODE_EVAL=1`。
- SQLite 适合单实例部署；如果需要多副本或高并发部署，应先评估数据库和任务调度的一致性方案。
