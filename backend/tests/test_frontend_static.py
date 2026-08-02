from pathlib import Path
import re
import subprocess

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_frontend_index_is_react_shell_served_after_api_routes(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "/vendor/liquidGL.js" in response.text
    assert 'type="module"' in response.text


def test_frontend_has_vite_react_project_files():
    package_json = (FRONTEND / "package.json").read_text()
    vite_config = (FRONTEND / "vite.config.ts").read_text()
    tsconfig = (FRONTEND / "tsconfig.json").read_text()

    assert '"react"' in package_json
    assert '"@vitejs/plugin-react"' in package_json
    assert 'outDir: "dist"' in vite_config
    assert '"jsx": "react-jsx"' in tsconfig


def test_react_app_routes_all_taskgame_views():
    app_source = (FRONTEND / "src" / "App.tsx").read_text()
    expected_views = [
        "DashboardView",
        "MissionsView",
        "GoalsView",
        "BadgesView",
        "RewardsView",
        "ReportsView",
        "BackupView",
    ]

    for view in expected_views:
        assert view in app_source


def test_liquidgl_is_decorative_and_guarded():
    liquid_source = (FRONTEND / "src" / "components" / "LiquidGlassDecor.tsx").read_text()

    assert "window.liquidGL" in liquid_source
    assert "try" in liquid_source
    assert "catch" in liquid_source
    assert "aria-hidden" in liquid_source
    assert "pointer-events-none" in liquid_source


def test_build_script_has_docker_safe_dist_fallback():
    source = (ROOT / "scripts" / "build_frontend.sh").read_text()

    assert "npm --prefix frontend run build" in source
    assert "frontend/dist" in source
    assert "React frontend build is missing" in source
