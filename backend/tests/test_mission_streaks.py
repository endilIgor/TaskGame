from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.models import Base, Difficulty, Mission, MissionType
from backend.app.seed import seed_defaults
from backend.app.services.missions import complete_mission, get_player
from backend.app.services.reports import build_dashboard


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    seed_defaults(session)
    return session


def test_missed_required_daily_resets_streak_before_today():
    today = date.today()
    with _session() as session:
        mission = Mission(
            title="Rotina diaria",
            type=MissionType.DAILY,
            difficulty=Difficulty.EASY,
            start_date=today - timedelta(days=2),
        )
        session.add(mission)
        session.commit()

        complete_mission(session, mission.id, today - timedelta(days=2))
        complete_mission(session, mission.id, today)

        player = get_player(session)
        assert player.current_streak == 1
        assert player.best_streak == 1


def test_historical_daily_completion_recalculates_contiguous_streak():
    today = date.today()
    with _session() as session:
        mission = Mission(
            title="Rotina recuperada",
            type=MissionType.DAILY,
            difficulty=Difficulty.EASY,
            start_date=today - timedelta(days=2),
        )
        session.add(mission)
        session.commit()

        complete_mission(session, mission.id, today - timedelta(days=2))
        complete_mission(session, mission.id, today)
        complete_mission(session, mission.id, today - timedelta(days=1))

        player = get_player(session)
        assert player.current_streak == 3
        assert player.best_streak == 3


def test_all_prior_scheduled_daily_obligations_are_required():
    today = date.today()
    with _session() as session:
        first = Mission(
            title="Primeira rotina",
            type=MissionType.DAILY,
            difficulty=Difficulty.EASY,
            start_date=today - timedelta(days=1),
        )
        second = Mission(
            title="Segunda rotina",
            type=MissionType.DAILY,
            difficulty=Difficulty.EASY,
            start_date=today - timedelta(days=1),
        )
        session.add_all([first, second])
        session.commit()

        complete_mission(session, first.id, today - timedelta(days=1))
        complete_mission(session, first.id, today)

        assert get_player(session).current_streak == 1


def test_dashboard_recalculates_stale_streak_after_missed_daily():
    today = date.today()
    with _session() as session:
        player = get_player(session)
        player.current_streak = 5
        player.best_streak = 5
        player.last_active_date = today - timedelta(days=1)
        session.add(
            Mission(
                title="Rotina perdida",
                type=MissionType.DAILY,
                difficulty=Difficulty.EASY,
                start_date=today - timedelta(days=1),
            )
        )
        session.commit()

        dashboard = build_dashboard(session, today=today)

        assert dashboard.player.current_streak == 0
        assert dashboard.player.best_streak == 5
