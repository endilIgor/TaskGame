from fastapi.testclient import TestClient


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
