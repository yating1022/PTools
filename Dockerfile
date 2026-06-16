# ── Stage 1: Build frontend ──────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npx vite build

# ── Stage 2: Python backend + serve frontend ─────────────
FROM python:3.12-slim

WORKDIR /app

# 系统依赖（pymysql 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（先 COPY pyproject.toml 利用缓存）
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.34" \
    "httpx>=0.28" \
    "pydantic>=2.10" \
    "pydantic-settings>=2.7" \
    "pyyaml>=6.0" \
    "sqlalchemy>=2.0" \
    "pymysql>=1.1" \
    "openpyxl>=3.1" \
    "xlrd>=2.0" \
    "PyJWT>=2.10" \
    "python-multipart>=0.0.18"

# 后端代码
COPY backend/ ./

# 前端构建产物
COPY --from=frontend-build /app/frontend/dist ./static

EXPOSE 7679

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7679"]
