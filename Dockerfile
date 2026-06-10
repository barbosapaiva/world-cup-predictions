FROM python:3.14-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv
RUN uv sync --frozen --no-dev

COPY app ./app
COPY pipelines ./pipelines
COPY sql ./sql
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
