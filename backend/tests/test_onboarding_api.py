from fastapi.testclient import TestClient


def onboarding_answers(**overrides) -> dict:
    base = {
        "hero_name": "Aria",
        "hero_class": "warrior",
        "focus_skills": ["strength", "health"],
        "daily_minutes": 15,
        "preferred_days": [0, 1, 2, 3, 4],
        "main_goal": "Treinar 3 vezes por semana",
        "progress_prompt": "Treinar 3x",
        "reward_style": "rest",
        "intensity": "balanced",
    }
    base.update(overrides)
    return base


def test_get_profile_returns_404_when_no_profile_exists(client: TestClient):
    response = client.get("/api/profile")

    assert response.status_code == 404


def test_preview_onboarding_returns_suggestions_without_persisting(client: TestClient):
    response = client.post("/api/onboarding/preview", json=onboarding_answers())

    assert response.status_code == 200
    data = response.json()
    assert len(data["missions"]) == 5
    daily = [mission for mission in data["missions"] if mission["type"] == "daily"]
    weekly = [mission for mission in data["missions"] if mission["type"] == "weekly"]
    campaign = [mission for mission in data["missions"] if mission["type"] == "long_term"]
    assert len(daily) == 3
    assert len(weekly) == 1
    assert len(campaign) == 1
    assert len(data["rewards"]) == 2
    assert data["class_badge"]["code"] == "class_warrior"

    assert client.get("/api/profile").status_code == 404
    assert client.get("/api/missions").json() == []
    assert client.get("/api/rewards").json() == []


def test_preview_onboarding_validates_focus_skills_and_days(client: TestClient):
    empty_skills = client.post("/api/onboarding/preview", json=onboarding_answers(focus_skills=[]))
    assert empty_skills.status_code == 422

    too_many_skills = client.post(
        "/api/onboarding/preview",
        json=onboarding_answers(focus_skills=["strength", "health", "knowledge", "money"]),
    )
    assert too_many_skills.status_code == 422

    bad_day = client.post("/api/onboarding/preview", json=onboarding_answers(preferred_days=[7]))
    assert bad_day.status_code == 422

    bad_minutes = client.post("/api/onboarding/preview", json=onboarding_answers(daily_minutes=1))
    assert bad_minutes.status_code == 422


def test_confirm_onboarding_creates_selected_missions_and_rewards_and_unlocks_class_badge(
    client: TestClient,
):
    answers = onboarding_answers()
    preview = client.post("/api/onboarding/preview", json=answers).json()
    selected_mission_keys = [mission["key"] for mission in preview["missions"]][:2]
    selected_reward_keys = [reward["key"] for reward in preview["rewards"]][:1]

    response = client.post(
        "/api/onboarding/confirm",
        json={
            "answers": answers,
            "selected_mission_keys": selected_mission_keys,
            "selected_reward_keys": selected_reward_keys,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["profile"]["hero_name"] == "Aria"
    assert result["profile"]["hero_class"] == "warrior"
    assert result["profile"]["onboarding_completed_at"] is not None
    assert len(result["missions"]) == 2
    assert len(result["rewards"]) == 1
    assert any(badge["code"] == "class_warrior" for badge in result["badges"])

    profile_response = client.get("/api/profile")
    assert profile_response.status_code == 200
    assert profile_response.json()["hero_name"] == "Aria"

    missions = client.get("/api/missions").json()
    assert len(missions) == 2

    rewards = client.get("/api/rewards").json()
    assert len(rewards) == 1

    badges = client.get("/api/badges").json()
    earned_codes = {badge["code"] for badge in badges if badge["earned"]}
    assert "class_warrior" in earned_codes


def test_confirm_onboarding_is_idempotent_and_does_not_duplicate_missions(client: TestClient):
    answers = onboarding_answers()
    preview = client.post("/api/onboarding/preview", json=answers).json()
    selected_mission_keys = [mission["key"] for mission in preview["missions"]]
    payload = {
        "answers": answers,
        "selected_mission_keys": selected_mission_keys,
        "selected_reward_keys": [],
    }

    first = client.post("/api/onboarding/confirm", json=payload)
    second = client.post("/api/onboarding/confirm", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    missions = client.get("/api/missions").json()
    assert len(missions) == 5


def test_confirm_onboarding_allows_empty_mission_and_reward_selection(client: TestClient):
    answers = onboarding_answers(hero_class="mage", focus_skills=["knowledge"])

    response = client.post(
        "/api/onboarding/confirm",
        json={"answers": answers, "selected_mission_keys": [], "selected_reward_keys": []},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["missions"] == []
    assert result["rewards"] == []
    assert any(badge["code"] == "class_mage" for badge in result["badges"])
