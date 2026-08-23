from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, inspect, select
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, ensure_mission_completion_schema
from backend.app.main import create_app
from backend.app.models import Badge, Base, MissionCompletion, PlayerStats
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
        "class_warrior",
        "class_mage",
        "class_archer",
        "class_guardian",
    }


def test_seed_defaults_refreshes_existing_default_badge_copy():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            Badge(
                code="missions_100",
                name="100 missoes concluidas",
                description="Conclua 100 missoes.",
                condition_type="missions_completed",
                threshold=100,
            )
        )
        session.commit()

        seed_defaults(session)

        badge = session.scalar(select(Badge).where(Badge.code == "missions_100"))

    assert badge is not None
    assert badge.name == "100 missões concluídas"
    assert badge.description == "Conclua 100 missões."


def test_app_startup_initializes_default_sqlite_database():
    with TestClient(create_app()):
        with SessionLocal() as session:
            assert session.query(Badge).count() == 12


def test_mission_completion_schema_migration_adds_unique_key():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata = MetaData()
    missions = Table(
        "missions",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("type", String(16), nullable=False),
    )
    completions = Table(
        "mission_completions",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("mission_id", Integer, nullable=False),
        Column("completed_at", DateTime, nullable=False),
        Column("xp_awarded", Integer, nullable=False),
        Column("gold_awarded", Integer, nullable=False),
        Column("streak_bonus_percent", Integer, nullable=False),
        Column("note", String),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(missions.insert(), {"id": 1, "type": "daily"})
        connection.execute(
            completions.insert(),
            [
                {
                    "id": 1,
                    "mission_id": 1,
                    "completed_at": datetime(2026, 8, 2, 9),
                    "xp_awarded": 10,
                    "gold_awarded": 5,
                    "streak_bonus_percent": 0,
                },
                {
                    "id": 2,
                    "mission_id": 1,
                    "completed_at": datetime(2026, 8, 2, 10),
                    "xp_awarded": 10,
                    "gold_awarded": 5,
                    "streak_bonus_percent": 0,
                },
            ],
        )

    ensure_mission_completion_schema(engine)

    inspector = inspect(engine)
    assert "completion_key" in {
        column["name"] for column in inspector.get_columns("mission_completions")
    }
    assert any(
        index["name"] == "uq_mission_completion_key" and index["unique"]
        for index in inspector.get_indexes("mission_completions")
    )
    with Session(engine) as session:
        assert session.scalars(
            select(MissionCompletion.completion_key).order_by(MissionCompletion.id)
        ).all() == ["2026-08-02", "legacy-2"]


def test_mission_schema_migration_adds_deleted_at():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata = MetaData()
    Table(
        "missions",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(120), nullable=False),
    )
    metadata.create_all(engine)

    ensure_mission_completion_schema(engine)

    inspector = inspect(engine)
    assert "deleted_at" in {
        column["name"] for column in inspector.get_columns("missions")
    }
