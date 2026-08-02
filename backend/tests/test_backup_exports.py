from fastapi.testclient import TestClient


def test_json_backup_exports_created_mission(client: TestClient):
    client.post("/api/missions", json={"title": "Backup test", "type": "daily", "difficulty": "easy"})

    response = client.get("/api/backup/export.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["missions"][0]["title"] == "Backup test"


def test_missions_csv_contains_header_and_row(client: TestClient):
    client.post("/api/missions", json={"title": "CSV test", "type": "weekly", "difficulty": "medium"})

    response = client.get("/api/backup/missions.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "id,title,type,difficulty,status" in response.text
    assert "CSV test" in response.text
