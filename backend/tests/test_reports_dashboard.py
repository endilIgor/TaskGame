from fastapi.testclient import TestClient


def test_dashboard_contains_player_progress_and_recent_badge(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={
            "title": "Treino",
            "type": "daily",
            "difficulty": "easy",
            "repeat_days": [0, 1, 2, 3, 4, 5, 6],
        },
    ).json()
    client.post(f"/api/missions/{mission['id']}/complete")

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data["player"]["level"] == 1
    assert data["player"]["total_xp"] == 10
    assert data["today"]["completed"] == 1
    assert data["weekly"]["xp_gained"] == 10


def test_goals_returns_long_term_missions(client: TestClient):
    client.post(
        "/api/missions",
        json={
            "title": "Publicar portfolio",
            "type": "long_term",
            "difficulty": "hard",
            "progress_target": 5,
        },
    )

    response = client.get("/api/goals")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Publicar portfolio"
    assert response.json()[0]["progress_percent"] == 0


def test_weekly_report_counts_completed_missions(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Leitura", "type": "weekly", "difficulty": "medium"},
    ).json()
    client.post(f"/api/missions/{mission['id']}/complete")

    response = client.get("/api/reports/weekly")

    assert response.status_code == 200
    assert response.json()["missions_completed"] == 1
    assert response.json()["xp_gained"] == 25


def test_perfect_week_badge_unlocks_after_seven_completed_missions(client: TestClient):
    for number in range(7):
        mission = client.post(
            "/api/missions",
            json={
                "title": f"Missao semanal {number}",
                "type": "weekly",
                "difficulty": "easy",
            },
        ).json()
        client.post(f"/api/missions/{mission['id']}/complete")

    badges = client.get("/api/badges").json()

    assert "perfect_week" in {badge["code"] for badge in badges if badge["earned"]}
