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
