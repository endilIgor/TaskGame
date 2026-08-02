from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import get_settings
from backend.app.models import Base
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


def init_database() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_defaults(session)
