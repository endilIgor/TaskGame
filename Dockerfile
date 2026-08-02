FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-mysql-client node-typescript \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[test]"

COPY . .

RUN chmod +x scripts/*.sh
RUN scripts/build_frontend.sh

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host \"${APP_HOST:-0.0.0.0}\" --port \"${APP_PORT:-8000}\""]
