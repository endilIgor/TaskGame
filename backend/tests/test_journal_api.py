from datetime import date

from fastapi.testclient import TestClient


def test_adventurer_journal_create_list_and_read_entry(client: TestClient):
    response = client.post(
        "/api/journal/entries",
        json={
            "title": "Aventura diferente",
            "entry_date": date.today().isoformat(),
            "content": "Hoje eu treinei, estudei e derrotei a procrastinacao.",
            "mood": "focado",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Aventura diferente"
    assert created["entry_date"] == date.today().isoformat()
    assert created["content"].startswith("Hoje eu treinei")
    assert created["mood"] == "focado"

    listed = client.get("/api/journal/entries").json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert listed[0]["excerpt"] == "Hoje eu treinei, estudei e derrotei a procrastinacao."

    read = client.get(f"/api/journal/entries/{created['id']}")
    assert read.status_code == 200
    assert read.json()["content"] == created["content"]


def test_adventurer_journal_defaults_title_to_entry_day(client: TestClient):
    response = client.post(
        "/api/journal/entries",
        json={"entry_date": "2026-08-06", "content": "Dia comum salvo como post."},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Diario de 06/08/2026"


def test_adventurer_journal_month_filter_and_update(client: TestClient):
    august = client.post(
        "/api/journal/entries",
        json={"entry_date": "2026-08-06", "content": "Post de agosto."},
    ).json()
    client.post(
        "/api/journal/entries",
        json={"entry_date": "2026-07-31", "content": "Post de julho."},
    )

    listed = client.get("/api/journal/entries?month=2026-08").json()
    assert [entry["id"] for entry in listed] == [august["id"]]

    updated = client.patch(
        f"/api/journal/entries/{august['id']}",
        json={"title": "Boss final da quinta", "mood": "vitorioso"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Boss final da quinta"
    assert updated.json()["mood"] == "vitorioso"
