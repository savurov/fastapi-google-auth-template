FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV UV_NO_DEV=1

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000

ENTRYPOINT ["uv", "run", "fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
