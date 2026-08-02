# TaskGame MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the recommended TaskGame MVP: a personal gamified task dashboard with missions, routines, long-term goals, XP, levels, gold, badges, rewards, weekly reports, backups, FastAPI, MySQL in Docker, and a responsive vanilla frontend.

**Architecture:** FastAPI owns the REST API, game calculations, validation, persistence, backup exports, and static frontend hosting. SQLAlchemy maps MySQL tables to Python models, while focused service modules calculate XP, level, streaks, badges, reports, and backups. The frontend is HTML/CSS/TypeScript compiled by `tsc` without React, Vue, Angular, npm packages, or a `package.json`.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic 2.x, PyMySQL, pytest, httpx, MySQL 8, Docker Compose, HTML, CSS, TypeScript, browser `fetch`.

## Global Constraints

- Backend Python with FastAPI.
- Banco MySQL em Docker.
- Frontend em HTML, CSS, TypeScript e JavaScript puro, sem React e sem npm.
- Sem login e sem registro.
- `.env` nunca entra no git.
- CORS restrito a `http://localhost` e porta configurada.
- Validacao forte com Pydantic.
- SQLAlchemy usado com parametros, sem concatenar SQL manualmente.
- Backups ficam fora de diretorios publicos.
- MySQL nao deve expor porta publicamente fora do necessario para desenvolvimento local.
- O app inicia com `docker compose up --build`.
- O MySQL persiste dados em volume.
- Interface funciona bem em desktop e mobile.

---

## File Structure

Create these files:

```text
backend/
  app/
    __init__.py
    main.py
    config.py
    database.py
    models.py
    schemas.py
    seed.py
    routers/
      __init__.py
      backup.py
      badges.py
      dashboard.py
      missions.py
      reports.py
      rewards.py
    services/
      __init__.py
      backup.py
      badges.py
      game_rules.py
      missions.py
      reports.py
      rewards.py
  tests/
    conftest.py
    test_backup_exports.py
    test_badges.py
    test_game_rules.py
    test_missions_api.py
    test_rewards_api.py
    test_reports_dashboard.py
frontend/
  index.html
  src/
    api.ts
    app.ts
    backup.ts
    badges.ts
    dashboard.ts
    missions.ts
    rewards.ts
    reports.ts
    types.ts
  styles/
    app.css
  dist/
    .gitkeep
scripts/
  backup_mysql.sh
  build_frontend.sh
  restore_mysql.sh
.dockerignore
.env.example
.gitignore
Dockerfile
docker-compose.yml
pyproject.toml
tsconfig.json
```

Responsibilities:

- `backend/app/config.py`: loads environment variables and computes CORS/database settings.
- `backend/app/database.py`: creates the SQLAlchemy engine, sessions, and schema initialization helpers.
- `backend/app/models.py`: defines all persistent tables.
- `backend/app/schemas.py`: defines all API request/response contracts.
- `backend/app/seed.py`: inserts the single player row and default badges.
- `backend/app/services/game_rules.py`: pure XP, gold, level, and streak calculations.
- `backend/app/services/missions.py`: mission creation, update, completion, progress, and archive flows.
- `backend/app/services/badges.py`: badge unlock rules.
- `backend/app/services/rewards.py`: reward CRUD and purchase flow.
- `backend/app/services/reports.py`: dashboard and weekly report aggregation.
- `backend/app/services/backup.py`: JSON/CSV export serialization.
- `backend/app/routers/*.py`: thin FastAPI endpoints that validate input and call services.
- `frontend/src/*.ts`: browser modules that render sections, call API endpoints, and handle forms.
- `scripts/*.sh`: frontend compile, MySQL dump, and MySQL restore commands.

## Task 1: Project Base, Configuration, Docker, And Health Check

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.dockerignore`
- Create: `.env.example`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `Settings` class in `backend.app.config`
- Produces: `create_app() -> FastAPI` in `backend.app.main`
- Produces: `GET /api/health` returning `{"status": "ok", "app": "TaskGame"}`

- [ ] **Step 1: Write the failing health test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "TaskGame"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_health.py -v
```

Expected: FAIL because `backend.app.main` does not exist.

- [ ] **Step 3: Add Python project dependencies**

Create `pyproject.toml`:

```toml
[project]
name = "taskgame"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "sqlalchemy>=2.0.30",
  "pydantic>=2.8.0",
  "pydantic-settings>=2.4.0",
  "pymysql>=1.1.1",
  "python-dotenv>=1.0.1",
]

[project.optional-dependencies]
test = [
  "pytest>=8.2.0",
  "httpx>=0.27.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["backend/tests"]
```

- [ ] **Step 4: Add environment and ignore files**

Create `.env.example`:

```env
APP_NAME=TaskGame
APP_HOST=0.0.0.0
APP_PORT=8000
BACKEND_CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_DATABASE=taskgame
MYSQL_USER=taskgame
MYSQL_PASSWORD=change-me
MYSQL_ROOT_PASSWORD=change-root-me
DATABASE_URL=mysql+pymysql://taskgame:change-me@db:3306/taskgame
BACKUP_DIR=/app/backups
```

Create `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
*.pyc
backups/
frontend/dist/*.js
frontend/dist/*.js.map
```

Create `.dockerignore`:

```dockerignore
.git
.venv
__pycache__
.pytest_cache
backups
docs
```

- [ ] **Step 5: Implement settings and health app**

Create `backend/app/config.py`:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TaskGame"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    backend_cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    database_url: str = "sqlite+pysqlite:///:memory:"
    backup_dir: str = Field(default="./backups")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
```

- [ ] **Step 6: Add Docker files**

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-mysql-client node-typescript \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[test]"

COPY . .

RUN chmod +x scripts/*.sh || true

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
services:
  app:
    build: .
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backups:/app/backups

  db:
    image: mysql:8.4
    environment:
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 5s
      retries: 20
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

- [ ] **Step 7: Run tests and Docker build**

Run:

```bash
pytest backend/tests/test_health.py -v
docker compose --env-file .env.example config
```

Expected: pytest PASS and compose config prints valid services.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore .dockerignore .env.example Dockerfile docker-compose.yml backend
git commit -m "feat: add FastAPI base and Docker config"
```

## Task 2: Database Models, Session Handling, And Seed Data

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/seed.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_database_seed.py`

**Interfaces:**
- Consumes: `Settings.database_url`
- Produces: `get_engine(database_url: str | None = None) -> Engine`
- Produces: `get_session() -> Iterator[Session]`
- Produces: `init_database() -> None`
- Produces: `seed_defaults(session: Session) -> None`
- Produces SQLAlchemy models: `Mission`, `MissionCompletion`, `PlayerStats`, `Badge`, `EarnedBadge`, `Reward`, `RewardPurchase`, `WeeklySnapshot`

- [ ] **Step 1: Write failing database seed test**

Create `backend/tests/test_database_seed.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.models import Badge, Base, PlayerStats
from backend.app.seed import seed_defaults


def test_seed_defaults_creates_single_player_and_badges():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_defaults(session)
        seed_defaults(session)

        player_count = session.query(PlayerStats).count()
        badge_codes = {badge.code for badge in session.query(Badge).all()}

    assert player_count == 1
    assert badge_codes == {
        "streak_7",
        "streak_30",
        "missions_100",
        "first_goal",
        "perfect_week",
        "first_reward",
        "xp_1000",
        "xp_10000",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_database_seed.py -v
```

Expected: FAIL because database modules do not exist.

- [ ] **Step 3: Implement SQLAlchemy models**

Create `backend/app/models.py` with declarative `Base` and these exact table names:

```python
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MissionType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    LONG_TERM = "long_term"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EPIC = "epic"


class MissionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class RewardStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
```

Add mapped classes for the eight tables from the spec. Use `Text` for `repeat_days` storing comma-separated weekday numbers such as `"0,1,2,3,4"`. Use timezone-neutral `datetime.utcnow` through `server_default=func.now()` for created fields. Define relationships from completions to missions, earned badges to badges, and purchases to rewards.

- [ ] **Step 4: Implement database helpers**

Create `backend/app/database.py`:

```python
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.models import Base
from backend.app.seed import seed_defaults


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def init_database() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_defaults(session)
```

- [ ] **Step 5: Implement seed data**

Create `backend/app/seed.py` with `DEFAULT_BADGES` using the eight badge codes and thresholds from the spec. `seed_defaults(session)` must insert one `PlayerStats` row only when none exists and insert missing badges by `code` without duplicating existing rows.

- [ ] **Step 6: Initialize database on app startup**

Modify `backend/app/main.py`:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from backend.app.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield
```

Pass `lifespan=lifespan` to `FastAPI(...)`.

- [ ] **Step 7: Run tests**

Run:

```bash
pytest backend/tests/test_database_seed.py backend/tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat: add database models and seed data"
```

## Task 3: Pure Game Rules

**Files:**
- Create: `backend/app/services/game_rules.py`
- Test: `backend/tests/test_game_rules.py`

**Interfaces:**
- Produces: `base_rewards(difficulty: Difficulty | str) -> tuple[int, int]`
- Produces: `streak_bonus_percent(current_streak: int) -> int`
- Produces: `apply_xp_bonus(base_xp: int, bonus_percent: int) -> int`
- Produces: `level_from_total_xp(total_xp: int) -> tuple[int, int, int]`

- [ ] **Step 1: Write failing game rule tests**

Create `backend/tests/test_game_rules.py`:

```python
from backend.app.models import Difficulty
from backend.app.services.game_rules import (
    apply_xp_bonus,
    base_rewards,
    level_from_total_xp,
    streak_bonus_percent,
)


def test_base_rewards_follow_spec():
    assert base_rewards(Difficulty.EASY) == (10, 5)
    assert base_rewards(Difficulty.MEDIUM) == (25, 12)
    assert base_rewards(Difficulty.HARD) == (50, 25)
    assert base_rewards(Difficulty.EPIC) == (100, 60)


def test_streak_bonus_thresholds():
    assert streak_bonus_percent(0) == 0
    assert streak_bonus_percent(3) == 5
    assert streak_bonus_percent(7) == 10
    assert streak_bonus_percent(14) == 15
    assert streak_bonus_percent(30) == 25


def test_apply_xp_bonus_rounds_down_to_integer():
    assert apply_xp_bonus(25, 10) == 27
    assert apply_xp_bonus(100, 25) == 125


def test_level_from_total_xp_uses_accumulated_thresholds():
    assert level_from_total_xp(0) == (1, 0, 100)
    assert level_from_total_xp(100) == (2, 0, 200)
    assert level_from_total_xp(299) == (2, 199, 200)
    assert level_from_total_xp(300) == (3, 0, 300)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_game_rules.py -v
```

Expected: FAIL because `game_rules.py` does not exist.

- [ ] **Step 3: Implement pure functions**

Create `backend/app/services/game_rules.py`:

```python
from backend.app.models import Difficulty


REWARD_TABLE: dict[str, tuple[int, int]] = {
    Difficulty.EASY.value: (10, 5),
    Difficulty.MEDIUM.value: (25, 12),
    Difficulty.HARD.value: (50, 25),
    Difficulty.EPIC.value: (100, 60),
}


def base_rewards(difficulty: Difficulty | str) -> tuple[int, int]:
    key = difficulty.value if isinstance(difficulty, Difficulty) else difficulty
    return REWARD_TABLE[key]


def streak_bonus_percent(current_streak: int) -> int:
    if current_streak >= 30:
        return 25
    if current_streak >= 14:
        return 15
    if current_streak >= 7:
        return 10
    if current_streak >= 3:
        return 5
    return 0


def apply_xp_bonus(base_xp: int, bonus_percent: int) -> int:
    return int(base_xp * (1 + bonus_percent / 100))


def level_from_total_xp(total_xp: int) -> tuple[int, int, int]:
    level = 1
    remaining = total_xp
    while remaining >= 100 * level:
        remaining -= 100 * level
        level += 1
    return level, remaining, 100 * level
```

- [ ] **Step 4: Run tests**

Run:

```bash
pytest backend/tests/test_game_rules.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/game_rules.py backend/tests/test_game_rules.py
git commit -m "feat: add TaskGame scoring rules"
```

## Task 4: Mission Schemas, Service, And API

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/services/missions.py`
- Create: `backend/app/routers/missions.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_missions_api.py`

**Interfaces:**
- Consumes: `Mission`, `MissionCompletion`, `PlayerStats`, `Difficulty`, `MissionType`, `MissionStatus`
- Consumes: `base_rewards`, `streak_bonus_percent`, `apply_xp_bonus`
- Produces: `MissionCreate`, `MissionUpdate`, `MissionRead`, `MissionCompletionRead`, `MissionProgressUpdate`
- Produces: `create_mission(session: Session, data: MissionCreate) -> Mission`
- Produces: `complete_mission(session: Session, mission_id: int, completed_on: date | None = None) -> MissionCompletion`
- Produces routes under `/api/missions`

- [ ] **Step 1: Write failing mission API tests**

Create `backend/tests/test_missions_api.py`:

```python
from fastapi.testclient import TestClient


def test_create_list_and_complete_mission(client: TestClient):
    created = client.post(
        "/api/missions",
        json={
            "title": "Estudar Python",
            "description": "45 minutos de estudo",
            "type": "daily",
            "difficulty": "medium",
            "category": "estudo",
            "repeat_days": [0, 1, 2, 3, 4],
        },
    )
    assert created.status_code == 201
    mission = created.json()
    assert mission["title"] == "Estudar Python"
    assert mission["status"] == "active"

    listed = client.get("/api/missions")
    assert listed.status_code == 200
    assert [item["title"] for item in listed.json()] == ["Estudar Python"]

    completed = client.post(f"/api/missions/{mission['id']}/complete")
    assert completed.status_code == 200
    completion = completed.json()
    assert completion["xp_awarded"] == 25
    assert completion["gold_awarded"] == 12

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["player"]["total_xp"] == 25
    assert dashboard.json()["player"]["gold"] == 12
```

Add a second test:

```python
def test_long_term_progress_completion(client: TestClient):
    response = client.post(
        "/api/missions",
        json={
            "title": "Finalizar curso",
            "type": "long_term",
            "difficulty": "hard",
            "progress_target": 10,
        },
    )
    mission_id = response.json()["id"]

    progress = client.post(f"/api/missions/{mission_id}/progress", json={"amount": 4})

    assert progress.status_code == 200
    assert progress.json()["progress_current"] == 4
    assert progress.json()["status"] == "active"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_missions_api.py -v
```

Expected: FAIL because API schemas, test client fixture, and router do not exist.

- [ ] **Step 3: Add reusable test client fixture**

Modify `backend/tests/conftest.py` to create a temporary SQLite database per test:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import get_session
from backend.app.main import create_app
from backend.app.models import Base
from backend.app.seed import seed_defaults


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_defaults(session)

    def override_session():
        with TestingSessionLocal() as session:
            yield session

    app = create_app(init_db=False)
    app.dependency_overrides[get_session] = override_session
    return TestClient(app)
```

Modify `create_app(init_db: bool = True)` so tests can skip production initialization.

- [ ] **Step 4: Add Pydantic schemas**

Create `backend/app/schemas.py` with `ConfigDict(from_attributes=True)` response models. `MissionCreate` must require `title`, `type`, and `difficulty`, default `difficulty` to `"easy"` when omitted, default `progress_current` to `0`, and validate `progress_target >= 1` for long-term missions. `repeat_days` is `list[int]` with values `0` through `6`.

- [ ] **Step 5: Implement mission service**

Create `backend/app/services/missions.py` with:

```python
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Mission, MissionCompletion, MissionStatus, MissionType, PlayerStats
from backend.app.schemas import MissionCreate, MissionProgressUpdate, MissionUpdate
from backend.app.services.game_rules import apply_xp_bonus, base_rewards, streak_bonus_percent


def get_player(session: Session) -> PlayerStats:
    player = session.scalar(select(PlayerStats).limit(1))
    if player is None:
        player = PlayerStats(total_xp=0, gold=0, current_streak=0, best_streak=0)
        session.add(player)
        session.flush()
    return player
```

Implement:

- `list_missions(session, include_archived=False)` returning active/completed missions unless `include_archived` is true.
- `create_mission(session, data)` storing `repeat_days` as a comma-separated string.
- `update_mission(session, mission_id, data)` patching only provided fields.
- `archive_mission(session, mission_id)` setting `status` to archived.
- `advance_mission_progress(session, mission_id, amount)` adding positive progress and marking long-term mission completed when `progress_current >= progress_target`.
- `complete_mission(session, mission_id, completed_on=None)` awarding XP/gold once per mission per calendar date for daily/weekly missions.

Streak rule in `complete_mission`: if `player.last_active_date == completed_on - timedelta(days=1)`, increment; if it equals `completed_on`, keep current streak; otherwise set streak to 1. Update `best_streak`, then calculate bonus from the updated streak.

- [ ] **Step 6: Implement mission router**

Create `backend/app/routers/missions.py` with:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import MissionCreate, MissionProgressUpdate, MissionRead, MissionUpdate
from backend.app.services import missions as mission_service

router = APIRouter(prefix="/api/missions", tags=["missions"])
```

Add endpoints matching the spec and raise `HTTPException(status_code=404, detail="Mission not found")` when the service cannot find a mission.

- [ ] **Step 7: Add temporary dashboard route for mission test**

If Task 7 is not implemented yet, add a minimal `/api/dashboard` endpoint in `main.py` that reads `PlayerStats` and returns `{"player": {"total_xp": ..., "gold": ...}}`. Task 7 will replace it with the full dashboard router.

- [ ] **Step 8: Run tests**

Run:

```bash
pytest backend/tests/test_missions_api.py backend/tests/test_game_rules.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat: add mission API and completion flow"
```

## Task 5: Badge Unlocking

**Files:**
- Create: `backend/app/services/badges.py`
- Create: `backend/app/routers/badges.py`
- Modify: `backend/app/services/missions.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_badges.py`

**Interfaces:**
- Consumes: `Badge`, `EarnedBadge`, `MissionCompletion`, `Mission`, `PlayerStats`
- Produces: `evaluate_badges(session: Session) -> list[EarnedBadge]`
- Produces: `list_badges_with_status(session: Session) -> list[BadgeStatusRead]`
- Produces: `GET /api/badges`

- [ ] **Step 1: Write failing badge tests**

Create `backend/tests/test_badges.py`:

```python
from fastapi.testclient import TestClient


def test_xp_badge_unlocks_after_threshold(client: TestClient):
    for _ in range(10):
        mission = client.post(
            "/api/missions",
            json={"title": "Projeto epico", "type": "weekly", "difficulty": "epic"},
        ).json()
        client.post(f"/api/missions/{mission['id']}/complete")

    badges = client.get("/api/badges").json()
    earned_codes = {badge["code"] for badge in badges if badge["earned"]}

    assert "xp_1000" in earned_codes


def test_first_goal_badge_unlocks_when_long_term_goal_completes(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Ler livro", "type": "long_term", "difficulty": "medium", "progress_target": 2},
    ).json()

    client.post(f"/api/missions/{mission['id']}/progress", json={"amount": 2})

    badges = client.get("/api/badges").json()
    earned_codes = {badge["code"] for badge in badges if badge["earned"]}
    assert "first_goal" in earned_codes
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_badges.py -v
```

Expected: FAIL because badge service and router do not exist.

- [ ] **Step 3: Add badge response schema**

Add to `backend/app/schemas.py`:

```python
class BadgeStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    condition_type: str
    threshold: int
    earned: bool
    earned_at: datetime | None
```

- [ ] **Step 4: Implement badge service**

Create `backend/app/services/badges.py`. `evaluate_badges(session)` must unlock:

- `streak_7` when `PlayerStats.current_streak >= 7`.
- `streak_30` when `PlayerStats.current_streak >= 30`.
- `missions_100` when `MissionCompletion` count is at least 100.
- `first_goal` when at least one long-term `Mission.status == completed`.
- `first_reward` when at least one `RewardPurchase` exists.
- `xp_1000` when `PlayerStats.total_xp >= 1000`.
- `xp_10000` when `PlayerStats.total_xp >= 10000`.

Keep `perfect_week` for Task 7 because it depends on weekly reporting.

- [ ] **Step 5: Call badge evaluation after relevant events**

Modify `complete_mission` and `advance_mission_progress` in `backend/app/services/missions.py` to call `evaluate_badges(session)` before commit/return.

- [ ] **Step 6: Add badge router**

Create `backend/app/routers/badges.py` and include it from `create_app()`:

```python
@router.get("", response_model=list[BadgeStatusRead])
def list_badges(session: Session = Depends(get_session)):
    evaluate_badges(session)
    session.commit()
    return list_badges_with_status(session)
```

- [ ] **Step 7: Run tests**

Run:

```bash
pytest backend/tests/test_badges.py backend/tests/test_missions_api.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app backend/tests/test_badges.py
git commit -m "feat: unlock progress badges"
```

## Task 6: Personal Reward Shop

**Files:**
- Create: `backend/app/services/rewards.py`
- Create: `backend/app/routers/rewards.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/badges.py`
- Test: `backend/tests/test_rewards_api.py`

**Interfaces:**
- Consumes: `Reward`, `RewardPurchase`, `PlayerStats`
- Produces: `RewardCreate`, `RewardUpdate`, `RewardRead`, `RewardPurchaseRead`
- Produces: `create_reward(session, data) -> Reward`
- Produces: `purchase_reward(session, reward_id: int) -> RewardPurchase`
- Produces routes under `/api/rewards`

- [ ] **Step 1: Write failing reward API tests**

Create `backend/tests/test_rewards_api.py`:

```python
from fastapi.testclient import TestClient


def earn_gold(client: TestClient, times: int = 1) -> None:
    for _ in range(times):
        mission = client.post(
            "/api/missions",
            json={"title": "Ganhar ouro", "type": "weekly", "difficulty": "epic"},
        ).json()
        client.post(f"/api/missions/{mission['id']}/complete")


def test_create_and_purchase_reward(client: TestClient):
    earn_gold(client, times=1)
    reward = client.post("/api/rewards", json={"name": "Pizza", "description": "Sexta a noite", "cost": 40})
    assert reward.status_code == 201

    purchase = client.post(f"/api/rewards/{reward.json()['id']}/purchase")
    assert purchase.status_code == 200
    assert purchase.json()["cost_paid"] == 40

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["player"]["gold"] == 20


def test_purchase_requires_enough_gold(client: TestClient):
    reward = client.post("/api/rewards", json={"name": "Filme", "cost": 20}).json()

    purchase = client.post(f"/api/rewards/{reward['id']}/purchase")

    assert purchase.status_code == 400
    assert purchase.json()["detail"] == "Not enough gold"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_rewards_api.py -v
```

Expected: FAIL because reward schemas, service, and router do not exist.

- [ ] **Step 3: Add reward schemas**

In `backend/app/schemas.py`, add:

```python
class RewardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    cost: int = Field(ge=1)


class RewardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    cost: int | None = Field(default=None, ge=1)


class RewardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    cost: int
    status: str


class RewardPurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reward_id: int
    cost_paid: int
    purchased_at: datetime
```

- [ ] **Step 4: Implement reward service**

Create `backend/app/services/rewards.py` with create/list/update/archive/purchase. `purchase_reward` must lock in `cost_paid`, reject archived rewards, reject insufficient gold with `ValueError("Not enough gold")`, subtract gold, create `RewardPurchase`, call `evaluate_badges(session)`, and commit.

- [ ] **Step 5: Add reward router**

Create `backend/app/routers/rewards.py` with endpoints:

- `GET /api/rewards`
- `POST /api/rewards`
- `PATCH /api/rewards/{reward_id}`
- `POST /api/rewards/{reward_id}/purchase`
- `POST /api/rewards/{reward_id}/archive`

Map `ValueError("Not enough gold")` to HTTP 400 with detail `"Not enough gold"`.

- [ ] **Step 6: Run tests**

Run:

```bash
pytest backend/tests/test_rewards_api.py backend/tests/test_badges.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app backend/tests/test_rewards_api.py
git commit -m "feat: add personal reward shop"
```

## Task 7: Dashboard, Goals, Weekly Reports, And Perfect Week Badge

**Files:**
- Create: `backend/app/services/reports.py`
- Create: `backend/app/routers/dashboard.py`
- Create: `backend/app/routers/reports.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/badges.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_reports_dashboard.py`

**Interfaces:**
- Consumes: missions, completions, player stats, badges, rewards
- Produces: `build_dashboard(session: Session, today: date | None = None) -> DashboardRead`
- Produces: `build_weekly_report(session: Session, week_start: date | None = None) -> WeeklyReportRead`
- Produces: `GET /api/dashboard`
- Produces: `GET /api/goals`
- Produces: `GET /api/reports/weekly`
- Produces: `GET /api/reports/weekly/{week_start}`

- [ ] **Step 1: Write failing dashboard/report tests**

Create `backend/tests/test_reports_dashboard.py`:

```python
from fastapi.testclient import TestClient


def test_dashboard_contains_player_progress_and_recent_badge(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Treino", "type": "daily", "difficulty": "easy", "repeat_days": [0, 1, 2, 3, 4, 5, 6]},
    ).json()
    client.post(f"/api/missions/{mission['id']}/complete")

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data["player"]["level"] == 1
    assert data["player"]["total_xp"] == 10
    assert data["today"]["completed"] == 1
    assert data["weekly"]["xp_gained"] == 10


def test_goals_returns_long_term_missions(client: TestClient):
    client.post(
        "/api/missions",
        json={"title": "Publicar portfolio", "type": "long_term", "difficulty": "hard", "progress_target": 5},
    )

    response = client.get("/api/goals")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Publicar portfolio"
    assert response.json()[0]["progress_percent"] == 0


def test_weekly_report_counts_completed_missions(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Leitura", "type": "weekly", "difficulty": "medium"},
    ).json()
    client.post(f"/api/missions/{mission['id']}/complete")

    response = client.get("/api/reports/weekly")

    assert response.status_code == 200
    assert response.json()["missions_completed"] == 1
    assert response.json()["xp_gained"] == 25
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_reports_dashboard.py -v
```

Expected: FAIL because full dashboard/report routers do not exist.

- [ ] **Step 3: Add report schemas**

In `backend/app/schemas.py`, add response models for:

- `PlayerSummaryRead`: `total_xp`, `gold`, `level`, `xp_into_level`, `xp_for_next_level`, `current_streak`, `best_streak`.
- `DashboardTodayRead`: `completed`, `active`, `overdue`.
- `DashboardWeeklyRead`: `missions_completed`, `xp_gained`, `gold_gained`, `best_day`.
- `DashboardRead`: `player`, `today`, `weekly`, `upcoming_missions`, `recent_badge`.
- `GoalRead`: all mission fields plus `progress_percent`.
- `WeeklyReportRead`: `week_start`, `week_end`, `missions_completed`, `missions_failed`, `xp_gained`, `gold_gained`, `best_day`, `current_streak`, `best_streak`.

- [ ] **Step 4: Implement report service**

Create `backend/app/services/reports.py`. Use Monday as `week_start`. `build_weekly_report` must aggregate `MissionCompletion.completed_at` between `week_start 00:00:00` and `week_end 23:59:59`, sum XP/gold, count completions, set `best_day` to the weekday name with most completions, and set `missions_failed` to active daily/weekly missions whose target period has passed without completion.

- [ ] **Step 5: Finish perfect week badge**

Modify `evaluate_badges(session)` so `perfect_week` unlocks when the current weekly report has `missions_failed == 0` and `missions_completed >= 7`.

- [ ] **Step 6: Add routers and remove temporary dashboard**

Create `backend/app/routers/dashboard.py` with `/api/dashboard` and `/api/goals`. Create `backend/app/routers/reports.py` with `/api/reports/weekly` and `/api/reports/weekly/{week_start}`. Remove the temporary dashboard endpoint from `main.py` and include the new routers.

- [ ] **Step 7: Run tests**

Run:

```bash
pytest backend/tests/test_reports_dashboard.py backend/tests/test_missions_api.py backend/tests/test_badges.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app backend/tests/test_reports_dashboard.py
git commit -m "feat: add dashboard goals and weekly reports"
```

## Task 8: Backup Exports And MySQL Dump Scripts

**Files:**
- Create: `backend/app/services/backup.py`
- Create: `backend/app/routers/backup.py`
- Create: `scripts/backup_mysql.sh`
- Create: `scripts/restore_mysql.sh`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_backup_exports.py`

**Interfaces:**
- Consumes: all SQLAlchemy models
- Produces: `export_all_json(session: Session) -> dict[str, object]`
- Produces: `missions_csv(session: Session) -> str`
- Produces: `completions_csv(session: Session) -> str`
- Produces: `GET /api/backup/export.json`
- Produces: `GET /api/backup/missions.csv`
- Produces: `GET /api/backup/completions.csv`

- [ ] **Step 1: Write failing backup tests**

Create `backend/tests/test_backup_exports.py`:

```python
from fastapi.testclient import TestClient


def test_json_backup_exports_created_mission(client: TestClient):
    client.post("/api/missions", json={"title": "Backup test", "type": "daily", "difficulty": "easy"})

    response = client.get("/api/backup/export.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["missions"][0]["title"] == "Backup test"


def test_missions_csv_contains_header_and_row(client: TestClient):
    client.post("/api/missions", json={"title": "CSV test", "type": "weekly", "difficulty": "medium"})

    response = client.get("/api/backup/missions.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "id,title,type,difficulty,status" in response.text
    assert "CSV test" in response.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_backup_exports.py -v
```

Expected: FAIL because backup router does not exist.

- [ ] **Step 3: Implement backup service**

Create `backend/app/services/backup.py`. Use `csv.DictWriter` and `io.StringIO` for CSV. JSON export must include keys `missions`, `mission_completions`, `player_stats`, `badges`, `earned_badges`, `rewards`, `reward_purchases`, and `weekly_snapshots`. Convert `date` and `datetime` values to ISO strings.

- [ ] **Step 4: Implement backup router**

Create `backend/app/routers/backup.py` using `JSONResponse` and `Response(media_type="text/csv")`. Add `Content-Disposition` headers:

```python
headers={"Content-Disposition": 'attachment; filename="taskgame-backup.json"'}
```

Use filenames `taskgame-missions.csv` and `taskgame-completions.csv` for CSV endpoints.

- [ ] **Step 5: Add MySQL backup script**

Create `scripts/backup_mysql.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

: "${MYSQL_HOST:=db}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_DATABASE:=taskgame}"
: "${MYSQL_USER:=taskgame}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"

BACKUP_ROOT="${BACKUP_DIR:-./backups}/mysql"
mkdir -p "$BACKUP_ROOT"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_ROOT/taskgame-$STAMP.sql.gz"

mysqldump \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  --password="$MYSQL_PASSWORD" \
  "$MYSQL_DATABASE" | gzip > "$OUT"

echo "$OUT"
```

- [ ] **Step 6: Add MySQL restore script**

Create `scripts/restore_mysql.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_mysql.sh backups/mysql/taskgame-YYYYMMDD-HHMMSS.sql.gz" >&2
  exit 2
fi

if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

: "${MYSQL_HOST:=db}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_DATABASE:=taskgame}"
: "${MYSQL_USER:=taskgame}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"

gzip -dc "$1" | mysql \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  --password="$MYSQL_PASSWORD" \
  "$MYSQL_DATABASE"
```

- [ ] **Step 7: Run tests and shell syntax checks**

Run:

```bash
chmod +x scripts/backup_mysql.sh scripts/restore_mysql.sh
bash -n scripts/backup_mysql.sh
bash -n scripts/restore_mysql.sh
pytest backend/tests/test_backup_exports.py -v
```

Expected: shell syntax checks PASS and pytest PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app backend/tests/test_backup_exports.py scripts
git commit -m "feat: add backup exports and mysql dump scripts"
```

## Task 9: Frontend Shell, API Client, And Dashboard Rendering

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/styles/app.css`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/app.ts`
- Create: `frontend/src/dashboard.ts`
- Create: `frontend/dist/.gitkeep`
- Create: `scripts/build_frontend.sh`
- Create: `tsconfig.json`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `GET /api/dashboard`, `GET /api/missions`, `POST /api/missions/{id}/complete`
- Produces: `apiGet<T>(path: string) -> Promise<T>`
- Produces: `apiPost<T>(path: string, body?: unknown) -> Promise<T>`
- Produces: `renderDashboard(root: HTMLElement) -> Promise<void>`
- Produces: browser entrypoint `frontend/dist/app.js`

- [ ] **Step 1: Add frontend build config**

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "node",
    "rootDir": "frontend/src",
    "outDir": "frontend/dist",
    "strict": true,
    "noImplicitAny": true,
    "sourceMap": true
  },
  "include": ["frontend/src/**/*.ts"]
}
```

Create `scripts/build_frontend.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

if ! command -v tsc >/dev/null 2>&1; then
  echo "TypeScript compiler 'tsc' is required. In Docker it is installed from the OS package node-typescript." >&2
  exit 127
fi

tsc --project tsconfig.json
```

- [ ] **Step 2: Add static HTML shell**

Create `frontend/index.html` with a single app root:

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>TaskGame</title>
    <link rel="stylesheet" href="/styles/app.css">
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar" aria-label="Navegacao principal">
        <div class="brand">TaskGame</div>
        <nav>
          <button class="nav-button active" data-view="dashboard">Dashboard</button>
          <button class="nav-button" data-view="missions">Missoes</button>
          <button class="nav-button" data-view="goals">Objetivos</button>
          <button class="nav-button" data-view="badges">Medalhas</button>
          <button class="nav-button" data-view="rewards">Loja</button>
          <button class="nav-button" data-view="reports">Relatorio</button>
          <button class="nav-button" data-view="backup">Backup</button>
        </nav>
      </aside>
      <main id="app" class="content" tabindex="-1"></main>
    </div>
    <script type="module" src="/dist/app.js"></script>
  </body>
</html>
```

- [ ] **Step 3: Add CSS foundation**

Create `frontend/styles/app.css` with CSS variables:

```css
:root {
  color-scheme: dark;
  --bg: #05070d;
  --surface: #0b1020;
  --surface-2: #11182c;
  --border: #22304d;
  --text: #f3f7ff;
  --muted: #95a3ba;
  --blue: #1687ff;
  --blue-soft: #193b71;
  --gold: #d7a928;
  --gold-soft: #3f3212;
  --green: #3ddc84;
  --red: #ff5d5d;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
```

Add responsive rules: `.app-shell` is a two-column grid above `800px`; below `799px`, sidebar becomes a sticky top navigation with horizontal buttons and content stacks vertically.

- [ ] **Step 4: Add frontend types and API client**

Create `frontend/src/types.ts` with exact interfaces matching API response fields used by the UI:

```ts
export interface PlayerSummary {
  total_xp: number;
  gold: number;
  level: number;
  xp_into_level: number;
  xp_for_next_level: number;
  current_streak: number;
  best_streak: number;
}

export interface Dashboard {
  player: PlayerSummary;
  today: { completed: number; active: number; overdue: number };
  weekly: { missions_completed: number; xp_gained: number; gold_gained: number; best_day: string | null };
  upcoming_missions: Mission[];
  recent_badge: BadgeStatus | null;
}
```

Create `frontend/src/api.ts`:

```ts
const API_BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
}
```

- [ ] **Step 5: Render dashboard**

Create `frontend/src/dashboard.ts` with `renderDashboard(root)`. It must fetch `/dashboard`, render player level/XP/gold/streak summary, upcoming missions, and an error panel if the request fails.

- [ ] **Step 6: Add app router**

Create `frontend/src/app.ts` that listens for nav button clicks and calls `renderDashboard` for the default view. For not-yet-built views in this task, render a panel with the view title and no instructional copy.

- [ ] **Step 7: Serve static frontend**

Modify `backend/app/main.py` after API routes:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

Ensure this mount is added after all `/api` routers.

- [ ] **Step 8: Build and test**

Run:

```bash
chmod +x scripts/build_frontend.sh
scripts/build_frontend.sh
pytest backend/tests -v
```

Expected: `frontend/dist/app.js` exists and pytest PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend scripts/build_frontend.sh tsconfig.json backend/app/main.py
git commit -m "feat: add vanilla TypeScript dashboard shell"
```

## Task 10: Frontend Missions, Goals, Badges, Rewards, Reports, And Backup Views

**Files:**
- Create: `frontend/src/missions.ts`
- Create: `frontend/src/badges.ts`
- Create: `frontend/src/rewards.ts`
- Create: `frontend/src/reports.ts`
- Create: `frontend/src/backup.ts`
- Modify: `frontend/src/app.ts`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/styles/app.css`

**Interfaces:**
- Consumes: all MVP API endpoints
- Produces: mission create/complete UI
- Produces: goals progress UI
- Produces: badge gallery UI
- Produces: reward create/purchase UI
- Produces: weekly report UI
- Produces: backup download UI

- [ ] **Step 1: Extend frontend types**

Add interfaces in `frontend/src/types.ts` for `Mission`, `MissionCreate`, `BadgeStatus`, `Reward`, `RewardCreate`, `WeeklyReport`, and `BackupExport`. Use string unions:

```ts
export type MissionType = "daily" | "weekly" | "long_term";
export type Difficulty = "easy" | "medium" | "hard" | "epic";
export type MissionStatus = "active" | "completed" | "archived";
```

- [ ] **Step 2: Implement mission view**

Create `frontend/src/missions.ts` with:

- `renderMissions(root: HTMLElement): Promise<void>`
- A form for `title`, `type`, `difficulty`, `category`, `progress_target`, and `repeat_days`.
- A list of active missions.
- A complete button calling `POST /missions/{id}/complete`.
- A progress button for long-term goals calling `POST /missions/{id}/progress` with amount `1`.

After successful create/complete/progress, re-render the mission view.

- [ ] **Step 3: Implement goals view**

In `frontend/src/missions.ts`, export `renderGoals(root)`. Fetch `/goals` and render each long-term mission with a CSS progress bar using `progress_percent`.

- [ ] **Step 4: Implement badges view**

Create `frontend/src/badges.ts`. Fetch `/badges` and render a responsive badge grid. Earned badges use gold border and full opacity; locked badges use muted border and `opacity: 0.55`.

- [ ] **Step 5: Implement rewards view**

Create `frontend/src/rewards.ts` with a reward creation form and active reward list. Purchase buttons call `POST /rewards/{id}/purchase`; insufficient gold errors render in a visible `.alert.error` panel.

- [ ] **Step 6: Implement reports view**

Create `frontend/src/reports.ts`. Fetch `/reports/weekly` and render numeric cards plus a simple seven-bar chart for weekly completions. If the backend response has no per-day list, build the MVP chart from `missions_completed` as one filled total bar and six neutral bars, then revise only when backend adds day-level data.

- [ ] **Step 7: Implement backup view**

Create `frontend/src/backup.ts` with three anchor buttons:

```html
<a class="button" href="/api/backup/export.json">JSON</a>
<a class="button" href="/api/backup/missions.csv">Missoes CSV</a>
<a class="button" href="/api/backup/completions.csv">Conclusoes CSV</a>
```

- [ ] **Step 8: Wire views in app router**

Modify `frontend/src/app.ts` to map:

- `dashboard` -> `renderDashboard`
- `missions` -> `renderMissions`
- `goals` -> `renderGoals`
- `badges` -> `renderBadges`
- `rewards` -> `renderRewards`
- `reports` -> `renderReports`
- `backup` -> `renderBackup`

- [ ] **Step 9: Polish responsive CSS**

In `frontend/styles/app.css`, add stable dimensions for stat cards, mission rows, buttons, progress bars, forms, badge tiles, and reward tiles. Ensure text wraps inside buttons and cards on mobile. Avoid gradients and decorative orbs. Keep border radius at `8px` or less.

- [ ] **Step 10: Build frontend and run backend tests**

Run:

```bash
scripts/build_frontend.sh
pytest backend/tests -v
```

Expected: TypeScript compilation PASS and backend tests PASS.

- [ ] **Step 11: Commit**

```bash
git add frontend
git commit -m "feat: complete TaskGame frontend views"
```

## Task 11: End-To-End Docker Verification And Documentation

**Files:**
- Create: `README.md`
- Modify: `docs/superpowers/specs/2026-08-02-taskgame-design.md` only if implementation decisions changed during tasks

**Interfaces:**
- Consumes: complete MVP app
- Produces: documented local setup and verification commands

- [ ] **Step 1: Create local `.env` from example**

Run:

```bash
cp .env.example .env
```

Keep `.env` untracked.

- [ ] **Step 2: Build frontend**

Run:

```bash
scripts/build_frontend.sh
```

Expected: `frontend/dist/app.js` exists.

- [ ] **Step 3: Start app and database**

Run:

```bash
docker compose up --build
```

Expected: FastAPI starts on `http://localhost:8000` and MySQL health check passes.

- [ ] **Step 4: Verify API from another terminal**

Run:

```bash
curl -s http://localhost:8000/api/health
```

Expected:

```json
{"status":"ok","app":"TaskGame"}
```

- [ ] **Step 5: Verify persistence**

Create a mission through the UI, stop containers with `Ctrl+C`, start again with `docker compose up`, open `http://localhost:8000`, and confirm the mission still appears.

- [ ] **Step 6: Verify backup scripts inside app container**

Run:

```bash
docker compose exec app scripts/backup_mysql.sh
```

Expected: command prints a path under `/app/backups/mysql/taskgame-<timestamp>.sql.gz`.

- [ ] **Step 7: Write README**

Create `README.md` with sections:

- `TaskGame`
- `Stack`
- `Como rodar`
- `Como testar`
- `Backup`
- `Seguranca local`
- `Proximos passos`

Include these commands exactly:

```bash
cp .env.example .env
scripts/build_frontend.sh
docker compose up --build
pytest backend/tests -v
docker compose exec app scripts/backup_mysql.sh
```

- [ ] **Step 8: Run final checks**

Run:

```bash
git diff --check
scripts/build_frontend.sh
pytest backend/tests -v
docker compose --env-file .env.example config
```

Expected: all commands PASS.

- [ ] **Step 9: Commit**

```bash
git add README.md docs/superpowers/specs/2026-08-02-taskgame-design.md
git commit -m "docs: add TaskGame setup guide"
```

Skip the commit if only `.env`, generated JS, or backup files changed.

## Self-Review

Spec coverage:

- Docker, FastAPI, MySQL, `.env`, CORS, health check: Task 1.
- Tables and default badge/player data: Task 2.
- XP, gold, level, and streak rules: Task 3.
- Daily, weekly, and long-term missions: Task 4.
- Medalhas por marcos: Task 5 and Task 7 for perfect week.
- Loja pessoal and gold purchases: Task 6.
- Dashboard, goals, and weekly reports: Task 7.
- JSON/CSV export and MySQL dump/restore: Task 8.
- Responsive black/blue/gold frontend without React/npm packages: Task 9 and Task 10.
- End-to-end Docker verification and setup docs: Task 11.

Placeholder scan:

- The plan has no intentionally unfinished implementation steps.

Type consistency:

- Backend services consume SQLAlchemy `Session` and return SQLAlchemy models or Pydantic response-compatible objects.
- Frontend API paths omit `/api` because `api.ts` prefixes requests with `API_BASE = "/api"`.
- `MissionType`, `Difficulty`, and status string values match the database enum values from `models.py`.
