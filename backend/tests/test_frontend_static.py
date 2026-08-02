from pathlib import Path

from fastapi.testclient import TestClient


def test_frontend_index_is_served_after_api_routes(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert '<main id="app" class="content" tabindex="-1"></main>' in response.text


def test_frontend_routes_all_taskgame_views():
    frontend = Path(__file__).resolve().parents[2] / "frontend" / "src"
    app_source = (frontend / "app.ts").read_text()

    expected_views = {
        "missions.ts": "renderMissions",
        "missions.ts": "renderGoals",
        "badges.ts": "renderBadges",
        "rewards.ts": "renderRewards",
        "reports.ts": "renderReports",
        "backup.ts": "renderBackup",
    }
    for filename, renderer in expected_views.items():
        source = (frontend / filename).read_text()
        assert f"export async function {renderer}" in source
        assert renderer in app_source
