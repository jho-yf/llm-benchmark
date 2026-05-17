VENV := backend/.venv
PYTHON_BIN := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
PYTEST := $(VENV)/bin/pytest
DATASETS_DIR := $(CURDIR)/datasets

# Auto-detect container runtime (docker or podman)
CONTAINER_RUNTIME := $(shell command -v docker 2>/dev/null || command -v podman 2>/dev/null)
CONTAINER_COMPOSE := $(shell command -v docker-compose 2>/dev/null || command -v podman-compose 2>/dev/null)
# podman >= 3 has built-in compose via "podman compose"
ifeq ($(findstring podman,$(CONTAINER_RUNTIME)),podman)
  ifeq ($(CONTAINER_COMPOSE),)
    CONTAINER_COMPOSE := podman compose
  endif
endif
# docker also has "docker compose" plugin
ifeq ($(findstring docker,$(CONTAINER_RUNTIME)),docker)
  ifeq ($(CONTAINER_COMPOSE),)
    CONTAINER_COMPOSE := docker compose
  endif
endif

.PHONY: setup dev dev-backend dev-frontend stop build build-frontend test test-backend \
        download-datasets up down compose-build logs clean

# 初始化环境
setup:
	cd backend && $(PYTHON_BIN) -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install pytest pytest-asyncio httpx
	cd frontend && npm install

# 本地开发
dev:
	@cd backend && HF_DATASETS_CACHE=$(DATASETS_DIR) .venv/bin/uvicorn app.main:app --reload --port 8000 & \
	cd frontend && npm run dev -- --port 3000 & \
	wait

# 停止本地服务
stop:
	@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@pkill -f "vite.*port 3000" 2>/dev/null || true
	@echo "Stopped backend and frontend"

# 构建
build: build-frontend

build-frontend:
	cd frontend && npm install && npm run build

# 测试
test: test-backend

test-backend:
	cd backend && .venv/bin/pytest tests/ -v

# 下载测试数据集到项目目录 (~170MB)
download-datasets:
	@mkdir -p $(DATASETS_DIR)
	cd backend && HF_DATASETS_CACHE=$(DATASETS_DIR) .venv/bin/python preload_datasets.py

# Container (docker / podman)
up:
	$(CONTAINER_COMPOSE) up -d --build

down:
	$(CONTAINER_COMPOSE) down

compose-build:
	$(CONTAINER_COMPOSE) build

logs:
	$(CONTAINER_COMPOSE) logs -f

# 兼容旧命令名
docker-up: up
docker-down: down
docker-build: compose-build
docker-logs: logs

# 清理
clean:
	rm -rf frontend/dist frontend/node_modules
	rm -rf datasets/ hf_cache/
	rm -rf backend/data/benchmark.db
	rm -rf backend/logs/*.log
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
