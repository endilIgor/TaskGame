import csv
from datetime import date, datetime
from io import StringIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.models import Base, Difficulty, Mission, MissionCompletion, MissionType
from backend.app.config import Settings, get_settings
from backend.app.services.backup import completions_csv, missions_csv


def test_json_backup_exports_created_mission(client: TestClient):
    client.post("/api/missions", json={"title": "Backup test", "type": "daily", "difficulty": "easy"})

    response = client.get("/api/backup/export.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"] == 'attachment; filename="taskgame-backup.json"'
    backup = response.json()
    assert set(backup) == {
        "missions",
        "mission_completions",
        "player_stats",
        "badges",
        "earned_badges",
        "rewards",
        "reward_purchases",
        "weekly_snapshots",
    }
    mission = backup["missions"][0]
    assert mission["title"] == "Backup test"
    assert mission["type"] == "daily"
    assert mission["difficulty"] == "easy"
    assert mission["status"] == "active"
    assert mission["start_date"] == date.today().isoformat()
    assert datetime.fromisoformat(mission["created_at"])


def test_missions_csv_contains_header_and_row(client: TestClient):
    client.post("/api/missions", json={"title": "CSV test", "type": "weekly", "difficulty": "medium"})

    response = client.get("/api/backup/missions.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.headers["content-disposition"] == 'attachment; filename="taskgame-missions.csv"'
    assert "id,title,type,difficulty,status" in response.text
    assert "CSV test" in response.text


def test_completions_csv_contains_header_row_and_attachment(client: TestClient):
    created = client.post(
        "/api/missions",
        json={"title": "Completion CSV", "type": "daily", "difficulty": "easy"},
    )
    client.post(f"/api/missions/{created.json()['id']}/complete")

    response = client.get("/api/backup/completions.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.headers["content-disposition"] == 'attachment; filename="taskgame-completions.csv"'
    assert "id,mission_id,completion_key,completed_at,xp_awarded,gold_awarded,streak_bonus_percent,note" in response.text
    assert f",{created.json()['id']}," in response.text


def test_missions_csv_escapes_formula_title():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            Mission(
                title="=HYPERLINK(\"https://example.com\")",
                type=MissionType.DAILY,
                difficulty=Difficulty.EASY,
            )
        )
        session.commit()

        row = next(csv.DictReader(StringIO(missions_csv(session))))

    assert row["title"] == "'=HYPERLINK(\"https://example.com\")"


def test_completions_csv_escapes_formula_note():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        mission = Mission(
            title="Completion note",
            type=MissionType.DAILY,
            difficulty=Difficulty.EASY,
        )
        session.add(mission)
        session.flush()
        session.add(
            MissionCompletion(
                mission_id=mission.id,
                completion_key="2026-08-02",
                xp_awarded=10,
                gold_awarded=5,
                note="@SUM(1,1)",
            )
        )
        session.commit()

        row = next(csv.DictReader(StringIO(completions_csv(session))))

    assert row["note"] == "'@SUM(1,1)"


@pytest.mark.parametrize(
    "title",
    [
        "\t=SUM(1,1)",
        "\r+1+1",
        "\n-2+3",
        "  @SUM(1,1)",
        "\x1f =SUM(1,1)",
        "\ufeff=SUM(1,1)",
        "\u200b+1+1",
    ],
)
def test_missions_csv_escapes_formula_after_leading_whitespace_or_control(title: str):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            Mission(
                title=title,
                type=MissionType.DAILY,
                difficulty=Difficulty.EASY,
            )
        )
        session.commit()

        row = next(csv.DictReader(StringIO(missions_csv(session))))

    assert row["title"] == f"'{title}"


def test_backup_status_reports_latest_mysql_dump(client: TestClient, tmp_path):
    mysql_dir = tmp_path / "mysql"
    mysql_dir.mkdir()
    older = mysql_dir / "taskgame-20260801-100000.sql.gz"
    latest = mysql_dir / "taskgame-20260802-100000.sql.gz"
    older.write_bytes(b"older")
    latest.write_bytes(b"latest")
    older.touch()
    latest.touch()
    client.app.dependency_overrides[get_settings] = lambda: Settings(backup_dir=str(tmp_path))
    try:
        response = client.get("/api/backup/status")
    finally:
        client.app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 200
    assert response.json()["last_mysql_dump_filename"] == latest.name
    assert response.json()["last_mysql_dump_at"] is not None
