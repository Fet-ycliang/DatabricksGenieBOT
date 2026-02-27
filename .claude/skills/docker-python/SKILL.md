---
name: docker-python
description: Best practices for containerizing Python applications using Docker and uv.
---

# Dockerizing Python Applications

This skill provides guidelines and patterns for creating efficient, secure, and production-ready Docker images for Python applications.

## Key Principles

- **Use `uv` for dependency management**: significantly faster builds and smaller images.
- **Multi-stage builds**: separate build and runtime environments if necessary (though `uv` makes single-stage quite efficient too).
- **Non-root user**: verify security by running as a non-root user.
- **Layer caching**: copy `pyproject.toml` and lock files first to leverage Docker layer caching.

## Recommended `Dockerfile` Pattern (with `uv`)

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

## `.dockerignore` Best Practices

Always include a `.dockerignore` to prevent unnecessary files from invalidating the cache or bloating the image.

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

## Running the Container

```bash
# Build
docker build -t my-app .

# Run
docker run -p 8000:8000 --env-file .env my-app
```
