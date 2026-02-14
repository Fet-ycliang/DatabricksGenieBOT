---
name: docker-python
description: 使用 Docker 和 uv 將 Python 應用程式容器化的最佳實踐。
---

# Dockerizing Python Applications

此技能提供建立高效、安全且生產級 Python 應用程式 Docker 映像檔的指引和模式。

## 關鍵原則

- **使用 `uv` 進行依賴管理**：顯著加快建置速度並縮小映像檔體積。
- **多階段建置 (Multi-stage builds)**：必要時分離建置和執行環境 (雖然 `uv` 讓單階段建置也相當高效)。
- **非 root 使用者**：透過以非 root 使用者身份執行來驗證安全性。
- **層快取 (Layer caching)**：先複製 `pyproject.toml` 和鎖定檔案以利用 Docker 層快取。

## 推薦的 `Dockerfile` 模式 (搭配 `uv`)

```dockerfile
# Use a specific version of python
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: ensure lockfile is respected
# --no-dev: do not install dev dependencies
# --no-install-project: only install dependencies, not the project itself yet
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
```

## `.dockerignore` 最佳實踐

務必包含 `.dockerignore` 以防止不必要的檔案使快取失效或讓映像檔臃腫。

```text
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesize
.antigravity
logs/
.env
```

## 執行容器

```bash
# Build
docker build -t my-app .

# Run
docker run -p 8000:8000 --env-file .env my-app
```
