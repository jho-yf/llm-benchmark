# Stage 1: Build frontend
FROM node:22-slim AS frontend-build
WORKDIR /build
# Override any inherited .npmrc (private registries, auth tokens)
RUN echo "registry=https://registry.npmjs.org" > ~/.npmrc
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime with frontend static files
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Pre-download all benchmark datasets into image
ENV HF_DATASETS_CACHE=/app/datasets
RUN python preload_datasets.py

# Copy frontend build output
COPY --from=frontend-build /build/dist ./static/

# Data and logs directories
RUN mkdir -p /app/data /app/logs

# Run offline - datasets are baked into the image
ENV HF_DATASETS_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
