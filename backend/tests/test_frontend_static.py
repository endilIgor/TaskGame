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
    dashboard = (FRONTEND / "src" / "views" / "DashboardView.tsx").read_text()
    styles = (FRONTEND / "styles" / "app.css").read_text()

    assert "window.liquidGL" in liquid_source
    assert "try" in liquid_source
    assert "catch" in liquid_source
    assert "aria-hidden" in dashboard
    assert ".liquid-glass-surface" in liquid_source
    assert "MutationObserver" in liquid_source
    assert "data-liquidgl-bound" in liquid_source
    assert ".pointer-events-none" in styles
    assert ".liquid-glass-surface" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles


def test_liquidgl_vendor_file_exists_and_is_loaded_before_app():
    index = (FRONTEND / "index.html").read_text()
    vendor = FRONTEND / "public" / "vendor" / "liquidGL.js"

    assert vendor.exists()
    assert vendor.stat().st_size > 1000
    assert '<script src="/vendor/liquidGL.js" defer></script>' in index


def test_production_dist_loads_liquidgl_before_the_app_bundle():
    index = (FRONTEND / "dist" / "index.html").read_text()

    assert index.index('<script src="/vendor/liquidGL.js" defer></script>') < index.index(
        '<script type="module" crossorigin src="/assets/'
    )


def test_liquidgl_component_guards_strict_mode_replay_and_cleans_up_instances():
    liquid_source = (FRONTEND / "src" / "components" / "LiquidGlassDecor.tsx").read_text()

    assert "useRef" in liquid_source
    assert "initializedRef.current" in liquid_source
    assert "cleanupRef.current" in liquid_source
    assert '"destroy"' in liquid_source
    assert '"cleanup"' in liquid_source


def test_liquidgl_css_never_targets_interactive_controls():
    css = (FRONTEND / "styles" / "app.css").read_text()
    backup = (FRONTEND / "src" / "views" / "BackupView.tsx").read_text()
    rewards = (FRONTEND / "src" / "components" / "RewardCard.tsx").read_text()

    forbidden = [
        ".button.liquid",
        "input.liquid",
        "select.liquid",
        "textarea.liquid",
        ".quest-card.liquid-glass-decor",
    ]
    for selector in forbidden:
        assert selector not in css
    assert "reward-tile liquid-glass-surface" not in rewards
    assert 'className="panel backup-panel" data-liquid-ignore' in backup


def test_liquidgl_does_not_snapshot_or_cover_functional_shell():
    shell = (FRONTEND / "src" / "components" / "AppShell.tsx").read_text()
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert "data-liquid-ignore" in shell
    assert 'className="app-shell guild-shell" data-liquid-ignore' not in shell
    assert ".liquid-glass-surface" in css
    assert ".liquid-glass-surface {\n  position: fixed;" not in css
    assert "@media (max-width: 720px)" in css
    assert ".guild-shell { grid-template-columns: 1fr;" in css
    assert ".sidebar, .content { width: 100%; max-width: 100vw;" in css


def test_liquidgl_targets_read_only_information_surfaces():
    dashboard = (FRONTEND / "src" / "views" / "DashboardView.tsx").read_text()
    metrics = (FRONTEND / "src" / "components" / "MetricCard.tsx").read_text()
    mission_card = (FRONTEND / "src" / "components" / "MissionCard.tsx").read_text()
    badges = (FRONTEND / "src" / "components" / "BadgeTile.tsx").read_text()
    reports = (FRONTEND / "src" / "views" / "ReportsView.tsx").read_text()
    rewards = (FRONTEND / "src" / "views" / "RewardsView.tsx").read_text()

    assert 'hero-panel glass-panel' not in dashboard
    assert 'metric-card-${tone} glass-panel' in metrics
    assert 'quest-card glass-panel' in mission_card
    assert 'badge-tile glass-panel' in badges
    assert reports.count("liquid-glass-surface") >= 3
    assert 'panel glass-panel' in rewards
    assert 'aria-hidden="true"' in metrics


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
    assert '"Campanhas precisam de uma meta de progresso positiva."' in source
    assert 'required={form.type === "long_term"}' in source


def test_missions_view_filters_edits_and_gates_actions_by_backend_rules():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert "useMemo" in source
    assert "statusFilter" in source
    assert "typeFilter" in source
    assert "visibleMissions" in source
    assert "eligibleToday = isActive && isStarted(mission) && isScheduledToday(mission)" in source
    assert 'mission.type === "long_term" && mission.progress_target !== null && mission.progress_current >= mission.progress_target' in source
    assert 'const canProgress = eligibleToday && mission.type === "long_term"' in source
    assert 'const canComplete = eligibleToday && (mission.type !== "long_term" || longTermTargetReached)' in source
    assert "apiPatch<Mission, MissionUpdate>" in source
    assert "Campanhas concluem automaticamente ao atingir a meta." in source


def test_missions_view_completion_gating_matches_backend_schedule_rules():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert "mission.start_date <= todayIsoDate()" in source
    assert "mission.repeat_days.includes(todayWeekday())" in source
    assert "return day === 0 ? 6 : day - 1;" in source


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


def test_reward_purchase_requires_confirmation():
    source = (FRONTEND / "src" / "views" / "RewardsView.tsx").read_text()

    assert "window.confirm" in source
    assert 'Comprar "${reward.name}" por ${reward.cost} ouro?' in source


def test_badge_tiles_show_condition_and_unlock_date():
    source = (FRONTEND / "src" / "components" / "BadgeTile.tsx").read_text()

    assert "condition_type" in source
    assert "earned_at" in source
    assert "Conquistada em" in source
    assert "Ainda bloqueada" in source


def test_reports_use_non_punitive_failure_copy():
    source = (FRONTEND / "src" / "views" / "ReportsView.tsx").read_text()

    assert "Pontos de atencao" in source
    assert "Missoes falhas" not in source
    assert 'tone="danger"' not in source


def test_legacy_manual_frontend_files_are_removed():
    legacy_sources = [
        "api.ts",
        "app.ts",
        "backup.ts",
        "badges.ts",
        "dashboard.ts",
        "missions.ts",
        "reports.ts",
        "rewards.ts",
    ]

    for filename in legacy_sources:
        assert not (FRONTEND / "src" / filename).exists()
    assert not list((FRONTEND / "prebuilt").glob("*.js"))


def test_mission_card_is_not_article_inside_article():
    source = (FRONTEND / "src" / "components" / "MissionCard.tsx").read_text()

    assert '<div className="quest-card glass-panel">' in source
    assert '<article className="quest-card">' not in source
