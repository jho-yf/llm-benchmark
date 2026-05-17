# Stage 1: Build frontend
FROM node:22-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime with frontend static files
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy pre-downloaded benchmark datasets into image
ENV HF_DATASETS_CACHE=/app/datasets
COPY datasets/ /app/datasets/

# Copy HF hub cache (dataset loading scripts) for fully offline use
ENV HF_HUB_CACHE=/app/hf_cache
COPY hf_cache/ /app/hf_cache/

# Copy frontend build output
COPY --from=frontend-build /build/dist ./static/

# Data and logs directories
RUN mkdir -p /app/data /app/logs

# Run offline - datasets are baked into the image
ENV HF_DATASETS_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
ENV HF_ALLOW_CODE_EVAL=1

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
