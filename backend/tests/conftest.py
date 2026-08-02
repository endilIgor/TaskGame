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
    with TestClient(app) as test_client:
        yield test_client
