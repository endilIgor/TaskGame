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


def test_frontend_static_responses_disable_cache_for_rebuilt_assets(client: TestClient):
    response = client.get("/")
    script_match = re.search(
        r'<script type="module" crossorigin src="/assets/([^\"]+\.js)"></script>',
        response.text,
    )

    assert script_match
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"

    asset_response = client.get(f"/assets/{script_match.group(1)}")

    assert asset_response.status_code == 200
    assert asset_response.headers["cache-control"] == "no-store, no-cache, must-revalidate"
    assert asset_response.headers["pragma"] == "no-cache"
    assert asset_response.headers["expires"] == "0"


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

    forbidden = [
        ".button.liquid",
        "input.liquid",
        "select.liquid",
        "textarea.liquid",
        ".quest-card.liquid-glass-decor",
    ]
    for selector in forbidden:
        assert selector not in css


def test_liquidgl_does_not_snapshot_or_cover_functional_shell():
    shell = (FRONTEND / "src" / "components" / "AppShell.tsx").read_text()
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert "data-liquid-ignore" in shell
    assert "inset: 0" not in css
    assert ".liquid-glass-decor" in css
    assert "z-index: -1" in css
    assert "@media (max-width: 720px)" in css
    assert ".guild-shell { grid-template-columns: 1fr;" in css
    assert ".sidebar, .content { width: 100%; max-width: 100vw;" in css
    assert "display: none" in css


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

    for view in ("dashboard", "missions", "goals", "badges", "rewards", "reports"):
        assert view in source
    assert '{ key: "backup", label: "Arquivo", eyebrow: "Dados" }' not in source
    assert "useState<ViewKey>" in source
    assert "setActiveView" in source


def test_cronica_navigation_does_not_keep_a_fixed_week_label():
    source = (FRONTEND / "src" / "components" / "AppShell.tsx").read_text()

    assert '{ key: "reports", label: "Crônica", eyebrow: "Relatórios" }' in source
    assert '{ key: "reports", label: "Cronica", eyebrow: "Semana" }' not in source


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


def test_select_controls_use_custom_app_themed_dropdown_instead_of_browser_menu():
    css = (FRONTEND / "styles" / "app.css").read_text()
    source = (FRONTEND / "src" / "components" / "FormControls.tsx").read_text()

    assert "return <select" not in source
    assert "custom-select-trigger" in source
    assert "custom-select-menu" in source
    assert "role=\"listbox\"" in source
    assert "role=\"option\"" in source
    assert ".custom-select-trigger" in css
    assert ".custom-select-menu" in css
    assert ".custom-select-option.selected" in css
    assert ".custom-select.open { z-index: 80; }" in css
    assert "white-space: nowrap" in css
    assert ".custom-select-menu { position: static; margin-top: 8px; }" in css


def test_dashboard_view_uses_live_dashboard_endpoint():
    source = (FRONTEND / "src" / "views" / "DashboardView.tsx").read_text()

    assert 'apiGet<DashboardData>("/dashboard")' in source
    assert "XP para o próximo nível" in source
    assert "Missões de hoje" in source
    assert "Ouro" in source


def test_progress_bar_clamps_aria_value_to_safe_maximum():
    source = (FRONTEND / "src" / "components" / "ProgressBar.tsx").read_text()

    assert "const safeMax = Math.max(max, 1);" in source
    assert "const clampedValue = Math.min(safeMax, Math.max(0, value));" in source
    assert "aria-valuenow={clampedValue}" in source


def test_missions_view_supports_create_complete_delete_and_deadline_flows():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert 'apiGet<Mission[]>(`/missions?today=${todayIsoDate()}`)' in source
    assert 'apiPost<Mission, MissionCreatePayload>("/missions"' in source
    assert "start_date: todayIsoDate()" in source
    assert '`/missions/${mission.id}/complete`' in source
    assert '`/missions/${mission.id}/archive`' not in source
    assert '`/missions/${mission.id}/restore`' not in source
    assert "Arquivar" not in source
    assert "Restaurar" not in source
    assert "Editar" not in source
    assert 'apiDelete(`/missions/${mission.id}`)' in source
    assert "dailyTimers" not in source
    assert "timer_minutes" not in source
    assert "renderMissionDeadline" in source
    assert "Ciclo de" in source
    assert "24h" in source
    assert "7 dias" in source


def test_missions_view_uses_skill_selector_instead_of_category_input():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()
    card_source = (FRONTEND / "src" / "components" / "MissionCard.tsx").read_text()

    assert "skill" in source
    assert "Conhecimento" in source
    assert "Força" in source
    assert "Dinheiro" in source
    assert "mission.skill" in card_source
    assert "Categoria" not in source
    assert "mission.category" not in card_source


def test_missions_view_requires_a_positive_long_term_progress_target_before_posting():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert 'if (form.type === "long_term" && (!Number.isInteger(target) || target < 1))' in source
    assert '"Campanhas precisam de uma meta de progresso positiva."' in source
    assert '"Campanhas precisam de uma data alvo a partir de hoje."' in source
    assert 'required={form.type === "long_term"}' in source
    assert "campaignMinDate()" in source
    assert 'form.type === "long_term" ?' in source
    assert 'editForm.type === "long_term" ?' not in source


def test_missions_view_filters_edits_and_gates_actions_by_backend_rules():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert "useMemo" in source
    assert "statusFilter" in source
    assert "typeFilter" in source
    assert "visibleMissions" in source
    assert "eligibleToday = isActive && isStarted(mission) && isScheduledToday(mission)" in source
    assert 'mission.type === "long_term" && mission.progress_target !== null && mission.progress_current >= mission.progress_target' in source
    assert 'const canComplete = eligibleToday && !mission.completed_today && mission.type !== "long_term"' in source
    assert "apiPatch<Mission, MissionUpdate>" not in source
    assert "Missões lendárias concluem automaticamente ao atingir a meta." not in source


def test_missions_view_completion_gating_matches_backend_schedule_rules():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert "mission.start_date <= todayIsoDate() || mission.start_date === tomorrowIsoDate()" in source
    assert "mission.repeat_days.includes(todayWeekday())" in source
    assert "return day === 0 ? 6 : day - 1;" in source


def test_missions_view_uses_local_dates_instead_of_utc_iso_dates():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert "formatLocalIsoDate" in source
    assert ".toISOString().slice(0, 10)" not in source


def test_calendar_controls_show_brazilian_dates_and_open_native_picker():
    source = (FRONTEND / "src" / "components" / "FormControls.tsx").read_text()
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert "formatDateDisplay" in source
    assert "`${day}/${month}/${year}`" in source
    assert "formatMonthDisplay" in source
    assert "`${month}/${year}`" in source
    assert "showPicker" in source
    assert "calendar-picker-button" in source
    assert "opacity: 0" not in css[css.index(".calendar-native-input"):css.index(".calendar-picker-button")]


def test_rewards_and_reports_views_use_existing_endpoints():
    rewards = (FRONTEND / "src" / "views" / "RewardsView.tsx").read_text()
    reports = (FRONTEND / "src" / "views" / "ReportsView.tsx").read_text()

    assert 'apiGet<Reward[]>("/rewards")' in rewards
    assert 'apiPost<Reward, RewardCreatePayload>("/rewards"' in rewards
    assert 'apiPost<RewardPurchase>(`/rewards/${reward.id}/purchase`)' in rewards
    assert 'apiGet<ReportPeriod>(endpoint)' in reports
    assert '"/reports/weekly"' in reports
    assert '"/reports/monthly"' in reports


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

    assert "Pontos de atenção" in source
    assert "Missões falhas" not in source
    assert 'tone="danger"' not in source


def test_reports_view_supports_weekly_and_monthly_breakdowns_with_xp_and_gold():
    source = (FRONTEND / "src" / "views" / "ReportsView.tsx").read_text()

    assert 'ReportPeriod' in source
    assert '"/reports/monthly"' in source
    assert '"/reports/weekly"' in source
    assert "daily_activity" in source
    assert "xp_gained" in source
    assert "gold_gained" in source
    assert 'period === "weekly" ? "Semana" : "Mês"' in source
    assert "Conclusões do período" in source


def test_reports_reward_chart_uses_blue_xp_and_gold_inside_the_main_bar():
    source = (FRONTEND / "src" / "views" / "ReportsView.tsx").read_text()
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert "chart-reward-stack" not in source
    assert 'className="chart-bar reward-comparison"' in source
    assert 'className="chart-reward-segment xp"' in source
    assert 'className="chart-reward-segment gold"' in source
    assert ">XP<" in source
    assert ">Ouro<" in source
    assert "flexDirection: \"column\"" in source
    assert ".chart-reward-segment.xp" in css
    assert "var(--color-arcane)" in css
    assert ".chart-reward-segment.gold" in css
    assert "var(--color-gold)" in css
    assert "justify-content: center" in css
    assert "space-between" not in css[css.index(".chart-reward-segment"):]


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

    assert '<div className={`quest-card${mission.completed_today ? " completed-today" : ""}`}>' in source
    assert '<article className="quest-card">' not in source


def test_hero_class_catalog_defines_four_classes_with_portuguese_labels():
    source = (FRONTEND / "src" / "data" / "heroClasses.ts").read_text()

    for class_id in ["warrior", "mage", "archer", "guardian"]:
        assert f'id: "{class_id}"' in source
        assert f"/assets/heroes/{class_id}.svg" in source

    for label in ["Guerreiro", "Mago", "Arqueiro", "Guardião"]:
        assert label in source


def test_hero_sprite_assets_exist_as_project_authored_placeholders():
    heroes_dir = FRONTEND / "public" / "assets" / "heroes"

    for class_id in ["warrior", "mage", "archer", "guardian"]:
        sprite = heroes_dir / f"{class_id}.svg"
        assert sprite.exists()
        assert "<svg" in sprite.read_text()

    attribution = (heroes_dir / "ATTRIBUTION.md").read_text()
    assert "project-authored" in attribution


def test_onboarding_view_covers_wizard_questions_and_confirm_flow():
    source = (FRONTEND / "src" / "views" / "OnboardingView.tsx").read_text()

    assert "Escolha sua classe" in source
    assert "Começar aventura" in source
    assert 'apiPost<OnboardingPreviewResult, OnboardingAnswers>("/onboarding/preview"' in source
    assert 'apiPost<OnboardingConfirmResult, OnboardingConfirmPayload>("/onboarding/confirm"' in source
    assert "HERO_CLASSES.map" in source
    assert "selectedMissionKeys" in source
    assert "selectedRewardKeys" in source
    assert "onComplete()" in source


def test_app_shows_onboarding_when_no_profile_exists():
    source = (FRONTEND / "src" / "App.tsx").read_text()

    assert "OnboardingView" in source
    assert 'apiGetOptional<PlayerProfile>("/profile")' in source
    assert '"onboarding"' in source


def test_react_api_client_exposes_optional_get_for_404_as_null():
    source = (FRONTEND / "src" / "api" / "client.ts").read_text()

    assert "export async function apiGetOptional" in source
    assert "response.status === 404" in source


def test_dashboard_view_shows_hero_profile_card_when_present():
    source = (FRONTEND / "src" / "views" / "DashboardView.tsx").read_text()

    assert 'apiGetOptional<PlayerProfile>("/profile")' in source
    assert "HeroProfileCard" in source
    assert "hero-profile-card" in source


def test_hero_classes_expose_role_and_trait_metadata_for_four_classes():
    source = (FRONTEND / "src" / "data" / "heroClasses.ts").read_text()

    assert "role: string;" in source
    assert "traits: string[];" in source
    for role in [
        "Tanque de disciplina",
        "Arquiteto do conhecimento",
        "Caçador de hábitos",
        "Guardião do equilíbrio",
    ]:
        assert role in source


def test_onboarding_class_cards_show_selection_state_and_traits():
    source = (FRONTEND / "src" / "views" / "OnboardingView.tsx").read_text()

    assert "class-card-check" in source
    assert "class-card-role" in source
    assert "class-card-traits" in source
    assert "heroClass.traits.map" in source
    assert "hero-sprite-frame" in source
    assert "hero-sprite-copy" in source
    assert "hero-sprite-role" in source


def test_onboarding_layout_is_responsive_across_breakpoints():
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert ".onboarding-layout { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(240px, 0.9fr)" in css
    onboarding_media = css[css.index("@media (max-width: 1180px)"):]
    assert ".filters-panel, .mission-board, .dashboard-grid, .journal-layout, .onboarding-layout { grid-template-columns: 1fr; }" in onboarding_media
    assert ".class-grid { grid-template-columns: 1fr; }" in onboarding_media
    mobile_media = css[css.index("@media (max-width: 720px)"):]
    assert 'grid-template-areas: "kicker kicker" "sprite copy";' in mobile_media
    assert ".hero-sprite-frame { grid-area: sprite; width: 76px; height: 92px; }" in mobile_media
    footer_media = css[css.index("@media (max-width: 560px)"):]
    assert ".onboarding-footer .row-actions { grid-template-columns: 1fr; justify-content: stretch; width: 100%; }" in footer_media
    assert ".onboarding-footer .row-actions .button { width: 100%; min-height: 52px; }" in footer_media


def test_onboarding_class_cards_have_hover_focus_and_selected_states():
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert ".class-card:hover { transform: translateY(-3px); }" in css
    assert ".class-card:focus-visible { outline: 0; box-shadow: 0 0 0 3px rgba(85, 179, 255, 0.4); }" in css
    assert ".class-card.selected .class-card-check { opacity: 1; transform: scale(1); }" in css
    assert ".choice-pill:focus-visible" in css
    assert ".suggestion-item:hover" in css


def test_onboarding_hero_and_class_sprites_use_css_only_animations_respecting_reduced_motion():
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert "@keyframes hero-idle-bob" in css
    assert "@keyframes hero-glow-pulse" in css
    assert "@keyframes class-card-enter" in css
    assert "@keyframes selected-glow-red" in css
    assert ".hero-sprite-image { position: relative; z-index: 1; width: 140px; height: 170px; object-fit: contain; filter: drop-shadow(0 14px 26px rgba(0, 0, 0, 0.42)); animation: hero-idle-bob 3.6s ease-in-out infinite; }" in css
    assert ".class-card-sprite { width: 64px; height: 78px; object-fit: contain; transition: transform 220ms ease; animation: hero-idle-bob 4.2s ease-in-out infinite; }" in css
    assert "animation: class-card-enter 420ms ease backwards" in css

    reduced_motion_block = css[css.index("@media (prefers-reduced-motion: reduce)"):]
    assert ".hero-sprite-image, .class-card-sprite, .hero-sprite-frame::before, .class-card { animation: none !important; }" in reduced_motion_block
