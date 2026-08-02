from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import UniqueConstraint

from backend.app.models import MissionCompletion


def test_create_list_and_complete_mission(client: TestClient):
    created = client.post(
        "/api/missions",
        json={
            "title": "Estudar Python",
            "description": "45 minutos de estudo",
            "type": "daily",
            "difficulty": "medium",
            "category": "estudo",
            "repeat_days": [date.today().weekday()],
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


def test_long_term_progress_target_completes_and_awards_atomically(client: TestClient):
    response = client.post(
        "/api/missions",
        json={
            "title": "Finalizar curso",
            "type": "long_term",
            "difficulty": "hard",
            "progress_target": 5,
        },
    )
    mission_id = response.json()["id"]

    progress = client.post(f"/api/missions/{mission_id}/progress", json={"amount": 5})

    assert progress.status_code == 200
    assert progress.json()["status"] == "completed"
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["player"]["total_xp"] == 50
    assert dashboard["player"]["gold"] == 25
    backup = client.get("/api/backup/export.json").json()
    assert len(backup["mission_completions"]) == 1
    assert backup["mission_completions"][0]["mission_id"] == mission_id


def test_completion_rejects_ineligible_missions(client: TestClient):
    tomorrow = date.today() + timedelta(days=1)
    off_schedule_day = (date.today().weekday() + 1) % 7
    payloads = [
        {
            "title": "Ainda nao iniciou",
            "type": "daily",
            "difficulty": "easy",
            "start_date": tomorrow.isoformat(),
        },
        {
            "title": "Fora da escala",
            "type": "daily",
            "difficulty": "easy",
            "repeat_days": [off_schedule_day],
        },
        {
            "title": "Objetivo incompleto",
            "type": "long_term",
            "difficulty": "hard",
            "progress_target": 10,
        },
    ]

    for payload in payloads:
        mission = client.post("/api/missions", json=payload).json()
        response = client.post(f"/api/missions/{mission['id']}/complete")
        assert response.status_code == 422

    archived = client.post(
        "/api/missions",
        json={"title": "Arquivada", "type": "weekly", "difficulty": "easy"},
    ).json()
    client.post(f"/api/missions/{archived['id']}/archive")
    response = client.post(f"/api/missions/{archived['id']}/complete")
    assert response.status_code == 422
    assert client.get("/api/dashboard").json()["player"]["total_xp"] == 0


def test_public_completion_does_not_accept_date_override(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Hoje", "type": "daily", "difficulty": "easy"},
    ).json()
    requested_date = date.today() - timedelta(days=30)

    response = client.post(
        f"/api/missions/{mission['id']}/complete",
        params={"completed_on": requested_date.isoformat()},
    )

    assert response.status_code == 200
    assert date.fromisoformat(response.json()["completed_at"][:10]) == date.today()


def test_weekly_completion_awards_only_once_per_week(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Revisao semanal", "type": "weekly", "difficulty": "easy"},
    ).json()

    first = client.post(f"/api/missions/{mission['id']}/complete")
    second = client.post(f"/api/missions/{mission['id']}/complete")

    assert second.json()["id"] == first.json()["id"]
    assert client.get("/api/dashboard").json()["player"]["total_xp"] == 10
    assert client.get("/api/dashboard").json()["player"]["current_streak"] == 0


def test_update_rejects_changing_mission_to_long_term_without_target(client: TestClient):
    created = client.post(
        "/api/missions",
        json={"title": "Planejar semana", "type": "daily", "difficulty": "easy"},
    )
    mission_id = created.json()["id"]

    updated = client.patch(f"/api/missions/{mission_id}", json={"type": "long_term"})

    assert updated.status_code == 422
    mission = client.get("/api/missions").json()[0]
    assert mission["type"] == "daily"
    assert mission["progress_target"] is None


def test_update_rejects_clearing_long_term_progress_target(client: TestClient):
    created = client.post(
        "/api/missions",
        json={
            "title": "Concluir curso",
            "type": "long_term",
            "difficulty": "medium",
            "progress_target": 8,
        },
    )
    mission_id = created.json()["id"]

    updated = client.patch(f"/api/missions/{mission_id}", json={"progress_target": None})

    assert updated.status_code == 422
    mission = client.get("/api/missions").json()[0]
    assert mission["type"] == "long_term"
    assert mission["progress_target"] == 8


def test_same_day_completion_returns_existing_completion_without_double_award(client: TestClient):
    created = client.post(
        "/api/missions",
        json={"title": "Revisar notas", "type": "daily", "difficulty": "easy"},
    )
    mission_id = created.json()["id"]

    first_completion = client.post(f"/api/missions/{mission_id}/complete")
    repeated_completion = client.post(f"/api/missions/{mission_id}/complete")

    assert first_completion.status_code == 200
    assert repeated_completion.status_code == 200
    assert repeated_completion.json()["id"] == first_completion.json()["id"]
    player = client.get("/api/dashboard").json()["player"]
    assert player["total_xp"] == 10
    assert player["gold"] == 5


def test_mission_completion_has_unique_mission_completion_key_constraint():
    constraints = MissionCompletion.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_mission_completion_key"
        and set(constraint.columns.keys()) == {"mission_id", "completion_key"}
        for constraint in constraints
    )
