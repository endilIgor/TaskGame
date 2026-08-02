from pathlib import Path
import re

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_frontend_dist_is_react_shell_served_after_api_routes(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "/vendor/liquidGL.js" in response.text
    script_match = re.search(
        r'<script type="module" crossorigin src="/assets/([^\"]+\.js)"></script>',
        response.text,
    )
    stylesheet_match = re.search(
        r'<link rel="stylesheet" crossorigin href="/assets/([^\"]+\.css)">',
        response.text,
    )

    assert script_match
    assert stylesheet_match
    assert client.get(f"/assets/{script_match.group(1)}").status_code == 200
    assert client.get(f"/assets/{stylesheet_match.group(1)}").status_code == 200


def test_vite_development_index_remains_a_source_shell():
    source_index = (FRONTEND / "index.html").read_text()

    assert '<script type="module" src="/src/main.tsx"></script>' in source_index


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
    styles = (FRONTEND / "styles" / "app.css").read_text()

    assert "window.liquidGL" in liquid_source
    assert "try" in liquid_source
    assert "catch" in liquid_source
    assert "aria-hidden" in liquid_source
    assert "pointer-events-none" in liquid_source
    assert ".pointer-events-none" in styles
    assert ".liquid-glass-decor" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles


def test_build_script_has_docker_safe_dist_fallback():
    source = (ROOT / "scripts" / "build_frontend.sh").read_text()

    assert "npm --prefix frontend run build" in source
    assert "frontend/dist" in source
    assert "React frontend build is missing" in source


def test_react_api_client_wraps_existing_backend_endpoints():
    source = (FRONTEND / "src" / "api" / "client.ts").read_text()

    assert "export async function apiGet" in source
    assert "export async function apiPost" in source
    assert "export async function apiPatch" in source
    assert 'fetch(`/api${path}`' in source
    assert "throw new Error" in source


def test_react_app_uses_stateful_shell_navigation():
    source = (FRONTEND / "src" / "components" / "AppShell.tsx").read_text()

    for view in ("dashboard", "missions", "goals", "badges", "rewards", "reports", "backup"):
        assert view in source
    assert "useState<ViewKey>" in source
    assert "setActiveView" in source


def test_rpg_theme_css_contains_centered_premium_tokens():
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert "--color-void" in css
    assert "--color-arcane" in css
    assert "--color-gold" in css
    assert "max-width: 1440px" in css
    assert ".hero-panel" in css
    assert ".quest-card" in css
    assert "@media (max-width: 720px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_dashboard_view_uses_live_dashboard_endpoint():
    source = (FRONTEND / "src" / "views" / "DashboardView.tsx").read_text()

    assert 'apiGet<DashboardData>("/dashboard")' in source
    assert "XP para o proximo nivel" in source
    assert "Missoes de hoje" in source
    assert "Ouro" in source


def test_progress_bar_clamps_aria_value_to_safe_maximum():
    source = (FRONTEND / "src" / "components" / "ProgressBar.tsx").read_text()

    assert "const safeMax = Math.max(max, 1);" in source
    assert "const clampedValue = Math.min(safeMax, Math.max(0, value));" in source
    assert "aria-valuenow={clampedValue}" in source


def test_missions_view_supports_create_complete_progress_and_archive_flows():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert 'apiGet<Mission[]>("/missions?include_archived=true")' in source
    assert 'apiPost<Mission, MissionCreatePayload>("/missions"' in source
    assert '`/missions/${mission.id}/complete`' in source
    assert '`/missions/${mission.id}/archive`' in source
    assert '`/missions/${mission.id}/progress`' in source


def test_missions_view_requires_a_positive_long_term_progress_target_before_posting():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert 'if (form.type === "long_term" && (!Number.isInteger(target) || target < 1))' in source
    assert 'setError("Campanhas precisam de uma meta de progresso positiva.")' in source
    assert 'required={form.type === "long_term"}' in source


def test_rewards_reports_backup_views_use_existing_endpoints():
    rewards = (FRONTEND / "src" / "views" / "RewardsView.tsx").read_text()
    reports = (FRONTEND / "src" / "views" / "ReportsView.tsx").read_text()
    backup = (FRONTEND / "src" / "views" / "BackupView.tsx").read_text()

    assert 'apiGet<Reward[]>("/rewards")' in rewards
    assert 'apiPost<Reward, RewardCreatePayload>("/rewards"' in rewards
    assert 'apiPost<RewardPurchase>(`/rewards/${reward.id}/purchase`)' in rewards
    assert 'apiGet<WeeklyReport>("/reports/weekly")' in reports
    assert 'apiGet<BackupStatus>("/backup/status")' in backup
    assert 'href="/api/backup/export.json"' in backup
    assert 'href="/api/backup/missions.csv"' in backup
    assert 'href="/api/backup/completions.csv"' in backup


def test_rewards_view_surfaces_purchase_history_failures_without_an_import_alias():
    source = (FRONTEND / "src" / "views" / "RewardsView.tsx").read_text()

    assert 'purchases.status === "error"' in source
    assert '<ErrorPanel>{purchases.error}</ErrorPanel>' in source
    assert "RewardPurchase as" not in source
