from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.main import create_app
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


def test_app_startup_initializes_default_sqlite_database():
    with TestClient(create_app()):
        with SessionLocal() as session:
            assert session.query(Badge).count() == 8
