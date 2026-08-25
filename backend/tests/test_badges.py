from datetime import date, timedelta

from fastapi.testclient import TestClient


def campaign_target_date() -> str:
    return (date.today() + timedelta(days=31)).isoformat()


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
        json={
            "title": "Ler livro",
            "type": "long_term",
            "difficulty": "medium",
            "progress_target": 2,
            "target_date": campaign_target_date(),
        },
    ).json()

    client.post(f"/api/missions/{mission['id']}/progress", json={"amount": 2})

    badges = client.get("/api/badges").json()
    earned_codes = {badge["code"] for badge in badges if badge["earned"]}
    assert "first_goal" in earned_codes


def test_class_badge_unlocks_for_the_chosen_class_on_onboarding_completion(client: TestClient):
    answers = {
        "hero_name": "Rowan",
        "hero_class": "guardian",
        "focus_skills": ["health", "social"],
        "daily_minutes": 15,
        "preferred_days": [0, 1, 2, 3, 4],
        "main_goal": "Cuidar mais da rotina em casa",
        "progress_prompt": "Fazer 1 ação de cuidado por dia",
        "reward_style": "food",
        "intensity": "light",
    }

    response = client.post(
        "/api/onboarding/confirm",
        json={"answers": answers, "selected_mission_keys": [], "selected_reward_keys": []},
    )

    assert response.status_code == 200
    badges = client.get("/api/badges").json()
    earned_by_code = {badge["code"]: badge for badge in badges if badge["earned"]}
    assert "class_guardian" in earned_by_code
    assert "class_warrior" not in earned_by_code
    assert "class_mage" not in earned_by_code
    assert "class_archer" not in earned_by_code


def test_mission_specific_badges_unlock_from_daily_weekly_and_epic_completions(client: TestClient):
    for index in range(10):
        mission = client.post(
            "/api/missions",
            json={"title": f"Diaria {index}", "type": "daily", "difficulty": "easy"},
        ).json()
        client.post(f"/api/missions/{mission['id']}/complete")

    for index in range(4):
        mission = client.post(
            "/api/missions",
            json={"title": f"Semanal {index}", "type": "weekly", "difficulty": "medium"},
        ).json()
        client.post(f"/api/missions/{mission['id']}/complete")

    for index in range(3):
        mission = client.post(
            "/api/missions",
            json={
                "title": f"Campanha {index}",
                "type": "long_term",
                "difficulty": "epic",
                "progress_target": 1,
                "target_date": campaign_target_date(),
            },
        ).json()
        client.post(f"/api/missions/{mission['id']}/progress", json={"amount": 1})

    badges = client.get("/api/badges").json()
    earned_codes = {badge["code"] for badge in badges if badge["earned"]}

    assert "daily_contracts_10" in earned_codes
    assert "weekly_contracts_4" in earned_codes
    assert "epic_campaigns_3" in earned_codes
