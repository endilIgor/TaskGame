from fastapi.testclient import TestClient


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
