from fastapi.testclient import TestClient


def test_xp_badge_unlocks_after_threshold(client: TestClient):
    for _ in range(10):
        mission = client.post(
            "/api/missions",
            json={"title": "Projeto epico", "type": "weekly", "difficulty": "epic"},
        ).json()
        client.post(f"/api/missions/{mission['id']}/complete")

    badges = client.get("/api/badges").json()
    earned_codes = {badge["code"] for badge in badges if badge["earned"]}

    assert "xp_1000" in earned_codes


def test_first_goal_badge_unlocks_when_long_term_goal_completes(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Ler livro", "type": "long_term", "difficulty": "medium", "progress_target": 2},
    ).json()

    client.post(f"/api/missions/{mission['id']}/progress", json={"amount": 2})

    badges = client.get("/api/badges").json()
    earned_codes = {badge["code"] for badge in badges if badge["earned"]}
    assert "first_goal" in earned_codes
