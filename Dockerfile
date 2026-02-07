FROM python:3.11-slim

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the lockfile and pyproject.toml to install dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: sync from the lockfile
# --no-dev: do not install development dependencies
# --no-install-project: do not install the project itself yet
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application code
COPY . .

# Place the virtual environment in the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
