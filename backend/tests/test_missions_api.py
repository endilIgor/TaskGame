from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import UniqueConstraint

from backend.app.models import MissionCompletion


def campaign_target_date(days: int = 31) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


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


def test_create_mission_with_skill_replaces_category(client: TestClient):
    response = client.post(
        "/api/missions",
        json={
            "title": "Ler livro técnico",
            "type": "daily",
            "difficulty": "easy",
            "skill": "knowledge",
        },
    )

    assert response.status_code == 201
    mission = response.json()
    assert mission["skill"] == "knowledge"
    assert mission["category"] == "knowledge"


def test_long_term_progress_completion(client: TestClient):
    response = client.post(
        "/api/missions",
        json={
            "title": "Finalizar curso",
            "type": "long_term",
            "difficulty": "hard",
            "progress_target": 10,
            "target_date": campaign_target_date(),
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
            "target_date": campaign_target_date(),
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
            "target_date": campaign_target_date(),
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


def test_archived_mission_can_be_restored(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Organizar backlog", "type": "weekly", "difficulty": "easy"},
    ).json()
    client.post(f"/api/missions/{mission['id']}/archive")

    restored = client.post(f"/api/missions/{mission['id']}/restore")

    assert restored.status_code == 200
    assert restored.json()["status"] == "active"
    listed = client.get("/api/missions").json()
    assert [item["title"] for item in listed] == ["Organizar backlog"]


def test_delete_mission_removes_it_from_lists(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Missao descartavel", "type": "daily", "difficulty": "easy"},
    ).json()
    completed = client.post(f"/api/missions/{mission['id']}/complete")
    assert completed.status_code == 200
    player_before = client.get("/api/dashboard").json()["player"]

    deleted = client.delete(f"/api/missions/{mission['id']}")

    assert deleted.status_code == 204
    assert client.get("/api/missions?include_archived=true").json() == []
    assert client.delete(f"/api/missions/{mission['id']}").status_code == 404
    assert client.post(f"/api/missions/{mission['id']}/complete").status_code == 404
    player_after = client.get("/api/dashboard").json()["player"]
    assert player_after["total_xp"] == player_before["total_xp"]
    assert player_after["gold"] == player_before["gold"]
    weekly = client.get("/api/reports/weekly").json()
    assert weekly["missions_completed"] == 1
    assert weekly["xp_gained"] == completed.json()["xp_awarded"]
    assert weekly["gold_gained"] == completed.json()["gold_awarded"]
    backup = client.get("/api/backup/export.json").json()
    assert len(backup["mission_completions"]) == 1


def test_create_long_term_requires_target_date_on_or_after_start_date(client: TestClient):
    base_payload = {
        "title": "Escrever livro",
        "type": "long_term",
        "difficulty": "hard",
        "progress_target": 10,
    }

    missing_target = client.post("/api/missions", json=base_payload)
    before_start = client.post(
        "/api/missions",
        json={**base_payload, "target_date": campaign_target_date(-1)},
    )
    valid = client.post(
        "/api/missions",
        json={**base_payload, "target_date": campaign_target_date(0)},
    )

    assert missing_target.status_code == 422
    assert before_start.status_code == 422
    assert valid.status_code == 201
    assert valid.json()["target_date"] == campaign_target_date(0)


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
            "target_date": campaign_target_date(),
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


def test_complete_mission_accepts_local_completed_on_body_and_returns_rewards_summary(client: TestClient):
    yesterday = date.today() - timedelta(days=1)
    mission = client.post(
        "/api/missions",
        json={
            "title": "Ler 3 páginas",
            "type": "daily",
            "difficulty": "easy",
            "repeat_days": [yesterday.weekday()],
            "start_date": yesterday.isoformat(),
        },
    ).json()

    response = client.post(
        f"/api/missions/{mission['id']}/complete",
        json={"completed_on": yesterday.isoformat()},
    )

    assert response.status_code == 200
    completion = response.json()
    assert completion["completed_at"].startswith(yesterday.isoformat())
    assert completion["xp_awarded"] == 10
    assert completion["gold_awarded"] == 5
    assert completion["mission_completion_count"] == 1
    assert completion["mission_total_xp_awarded"] == 10
    assert completion["mission_total_gold_awarded"] == 5
    report = client.get(f"/api/reports/weekly/{yesterday.isoformat()}").json()
    matching_day = next(day for day in report["daily_activity"] if day["date"] == yesterday.isoformat())
    assert matching_day["completions"] == 1


def test_mission_list_includes_completion_counts_and_today_lock(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Beber agua", "type": "daily", "difficulty": "easy"},
    ).json()

    client.post(f"/api/missions/{mission['id']}/complete")
    listed = client.get("/api/missions?include_archived=true").json()[0]

    assert listed["completion_count"] == 1
    assert listed["total_xp_awarded"] == 10
    assert listed["total_gold_awarded"] == 5
    assert listed["completed_today"] is True


def test_mission_list_uses_local_today_query_for_completion_lock(client: TestClient):
    yesterday = date.today() - timedelta(days=1)
    mission = client.post(
        "/api/missions",
        json={
            "title": "Treino local",
            "type": "daily",
            "difficulty": "easy",
            "start_date": yesterday.isoformat(),
            "repeat_days": [yesterday.weekday()],
        },
    ).json()

    client.post(
        f"/api/missions/{mission['id']}/complete",
        json={"completed_on": yesterday.isoformat()},
    )

    local_list = client.get(f"/api/missions?today={yesterday.isoformat()}").json()[0]
    server_list = client.get("/api/missions").json()[0]

    assert local_list["completed_today"] is True
    assert server_list["completed_today"] is False


def test_mission_completion_has_unique_mission_completion_key_constraint():
    constraints = MissionCompletion.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_mission_completion_key"
        and set(constraint.columns.keys()) == {"mission_id", "completion_key"}
        for constraint in constraints
    )
