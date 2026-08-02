from collections.abc import Iterator

from sqlalchemy import Engine, Index, create_engine, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import get_settings
from backend.app.models import Base, Mission, MissionCompletion, MissionType
from backend.app.seed import seed_defaults


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    poolclass = StaticPool if url.startswith("sqlite") and ":memory:" in url else None
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        poolclass=poolclass,
    )


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def ensure_mission_completion_schema(target_engine: Engine) -> None:
    inspector = inspect(target_engine)
    if "mission_completions" not in inspector.get_table_names():
        return

    column_names = {
        column["name"] for column in inspector.get_columns("mission_completions")
    }
    if "completion_key" not in column_names:
        with target_engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE mission_completions ADD COLUMN completion_key VARCHAR(64)")
            )

    with Session(target_engine) as session:
        completions = session.execute(
            select(MissionCompletion, Mission.type)
            .join(Mission, Mission.id == MissionCompletion.mission_id)
            .where(MissionCompletion.completion_key.is_(None))
            .order_by(MissionCompletion.mission_id, MissionCompletion.completed_at, MissionCompletion.id)
        )
        seen_keys: set[tuple[int, str]] = set()
        for completion, mission_type in completions:
            if mission_type in (MissionType.DAILY, MissionType.WEEKLY):
                completion_key = completion.completed_at.date().isoformat()
            else:
                completion_key = "long_term"
            key = (completion.mission_id, completion_key)
            if key in seen_keys:
                completion_key = f"legacy-{completion.id}"
            seen_keys.add(key)
            completion.completion_key = completion_key
        session.commit()

    inspector = inspect(target_engine)
    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("mission_completions")
    }
    unique_names.update(
        index["name"]
        for index in inspector.get_indexes("mission_completions")
        if index["unique"]
    )
    if "uq_mission_completion_key" not in unique_names:
        Index(
            "uq_mission_completion_key",
            MissionCompletion.__table__.c.mission_id,
            MissionCompletion.__table__.c.completion_key,
            unique=True,
        ).create(target_engine)


def init_database() -> None:
    Base.metadata.create_all(engine)
    ensure_mission_completion_schema(engine)
    with SessionLocal() as session:
        seed_defaults(session)
