from datetime import date, timedelta

from fastapi.testclient import TestClient


def campaign_target_date() -> str:
    return (date.today() + timedelta(days=31)).isoformat()


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
            "target_date": campaign_target_date(),
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
    assert response.json()["best_day"] in {
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    }
    assert response.json()["best_day"] not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def test_monthly_report_groups_completions_xp_and_gold_by_day(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Leitura mensal", "type": "weekly", "difficulty": "medium"},
    ).json()
    client.post(f"/api/missions/{mission['id']}/complete")

    response = client.get("/api/reports/monthly")

    assert response.status_code == 200
    report = response.json()
    assert report["period_type"] == "monthly"
    assert report["missions_completed"] == 1
    assert report["xp_gained"] == 25
    assert report["gold_gained"] == 12
    assert sum(day["completions"] for day in report["daily_activity"]) == 1
    active_day = next(day for day in report["daily_activity"] if day["completions"] == 1)
    assert active_day["xp_gained"] == 25
    assert active_day["gold_gained"] == 12


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


def test_weekly_report_includes_daily_category_and_goal_analysis(client: TestClient):
    daily = client.post(
        "/api/missions",
        json={
            "title": "Estudar",
            "type": "daily",
            "difficulty": "easy",
            "category": "Estudo",
        },
    ).json()
    goal = client.post(
        "/api/missions",
        json={
            "title": "Concluir modulo",
            "type": "long_term",
            "difficulty": "easy",
            "category": "Estudo",
            "progress_target": 1,
            "target_date": campaign_target_date(),
        },
    ).json()
    client.post(f"/api/missions/{daily['id']}/complete")
    client.post(f"/api/missions/{goal['id']}/progress", json={"amount": 1})

    report = client.get("/api/reports/weekly").json()

    assert sum(report["daily_completions"]) == 2
    assert report["daily_completions"][date.today().weekday()] == 2
    assert report["top_categories"] == [{"category": "Estudo", "completions": 2}]
    assert report["goals_completed"] == ["Concluir modulo"]
