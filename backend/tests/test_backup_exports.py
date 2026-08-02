import csv
from datetime import date, datetime
from io import StringIO

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.models import Base, Difficulty, Mission, MissionCompletion, MissionType
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
