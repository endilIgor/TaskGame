FROM python:3.12-slim

WORKDIR /app

COPY vendor/wheels /wheels

COPY pyproject.toml ./
COPY backend ./backend

RUN pip install --no-index --find-links=/wheels ".[test]"

COPY frontend ./frontend
COPY scripts ./scripts

RUN chmod +x scripts/*.sh
RUN scripts/build_frontend.sh

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host \"${APP_HOST:-0.0.0.0}\" --port \"${APP_PORT:-8000}\""]
