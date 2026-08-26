from fastapi.testclient import TestClient
from sqlalchemy.dialects import mysql

from backend.app.services.rewards import build_badge_suggestion_statement


def earn_gold(client: TestClient, times: int = 1) -> None:
    for _ in range(times):
        mission = client.post(
            "/api/missions",
            json={"title": "Ganhar ouro", "type": "weekly", "difficulty": "epic"},
        ).json()
        client.post(f"/api/missions/{mission['id']}/complete")


def test_create_and_purchase_reward(client: TestClient):
    earn_gold(client, times=1)
    reward = client.post(
        "/api/rewards",
        json={"name": "Pizza", "description": "Sexta a noite", "cost": 40},
    )
    assert reward.status_code == 201

    purchase = client.post(f"/api/rewards/{reward.json()['id']}/purchase")
    assert purchase.status_code == 200
    assert purchase.json()["cost_paid"] == 40

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["player"]["gold"] == 20


def test_purchase_requires_enough_gold(client: TestClient):
    reward = client.post("/api/rewards", json={"name": "Filme", "cost": 20}).json()

    purchase = client.post(f"/api/rewards/{reward['id']}/purchase")

    assert purchase.status_code == 400
    assert purchase.json()["detail"] == "Not enough gold"


def test_reward_purchase_history_is_listed_newest_first(client: TestClient):
    earn_gold(client, times=1)
    reward = client.post(
        "/api/rewards",
        json={"name": "Livro", "cost": 20},
    ).json()
    purchased = client.post(f"/api/rewards/{reward['id']}/purchase").json()

    response = client.get("/api/rewards/purchases")

    assert response.status_code == 200
    assert response.json() == [purchased]


def test_shop_suggestions_are_based_on_current_missions_and_badges(client: TestClient):
    mission = client.post(
        "/api/missions",
        json={"title": "Estudar para prova", "type": "daily", "difficulty": "medium"},
    ).json()
    client.post(f"/api/missions/{mission['id']}/complete")

    response = client.get("/api/rewards/suggestions")

    assert response.status_code == 200
    suggestions = response.json()
    assert any(
        suggestion["source"] == "mission" and "Estudar para prova" in suggestion["description"]
        for suggestion in suggestions
    )
    assert any(
        suggestion["source"] == "badge" and "Primeira compra na loja" in suggestion["name"]
        for suggestion in suggestions
    )
    assert all(suggestion["cost"] >= 1 for suggestion in suggestions)


def test_shop_suggestion_badge_query_compiles_for_mysql_without_nulls_last():
    compiled = str(build_badge_suggestion_statement().compile(dialect=mysql.dialect()))

    assert "NULLS LAST" not in compiled
    assert "CASE WHEN" in compiled
