import { apiGet } from "./api.js";
function createElement(tagName, className, text) {
    const element = document.createElement(tagName);
    if (className) {
        element.className = className;
    }
    if (text !== undefined) {
        element.textContent = text;
    }
    return element;
}
function createStat(label, value, valueClassName) {
    const card = createElement("article", "stat-card");
    card.append(createElement("span", "stat-label", label));
    card.append(createElement("strong", `stat-value${valueClassName ? ` ${valueClassName}` : ""}`, value));
    return card;
}
function formatMissionMeta(mission) {
    const target = mission.target_date ? ` | Alvo: ${mission.target_date}` : "";
    return `${mission.type} | ${mission.difficulty}${target}`;
}
function createMissionList(missions) {
    const list = createElement("div", "mission-list");
    if (missions.length === 0) {
        list.append(createElement("p", "empty-state", "Nenhuma missao pendente."));
        return list;
    }
    for (const mission of missions) {
        const item = createElement("article", "mission-item");
        item.append(createElement("span", "mission-title", mission.title));
        item.append(createElement("span", "mission-meta", formatMissionMeta(mission)));
        list.append(item);
    }
    return list;
}
function createXpProgress(player) {
    const progress = createElement("div", "xp-progress");
    const label = createElement("span", "stat-label", `${player.xp_into_level} / ${player.xp_for_next_level} XP para o proximo nivel`);
    const track = createElement("div", "progress-track");
    const bar = createElement("div", "progress-bar");
    const percentage = player.xp_for_next_level === 0
        ? 0
        : Math.min(100, (player.xp_into_level / player.xp_for_next_level) * 100);
    bar.style.width = `${percentage}%`;
    track.append(bar);
    progress.append(label, track);
    return progress;
}
function createBadge(badge) {
    const content = createElement("div", "badge-card");
    if (badge === null) {
        content.append(createElement("p", "empty-state", "Nenhuma medalha conquistada."));
        return content;
    }
    content.append(createElement("span", "badge-name", badge.name));
    content.append(createElement("span", "mission-meta", badge.description));
    return content;
}
function createPanel(title, content) {
    const panel = createElement("section", "panel");
    panel.append(createElement("h2", "panel-heading", title), content);
    return panel;
}
function renderDashboardData(root, dashboard) {
    const page = createElement("section", "dashboard");
    page.append(createElement("h1", "page-heading", "Dashboard"));
    const summary = createElement("section", "summary-grid");
    summary.append(createStat("Nivel", String(dashboard.player.level)), createStat("XP total", String(dashboard.player.total_xp)), createStat("Ouro", String(dashboard.player.gold), "gold"), createStat("Streak atual", `${dashboard.player.current_streak} dias`), createStat("Melhor streak", `${dashboard.player.best_streak} dias`));
    page.append(summary, createXpProgress(dashboard.player));
    const lowerGrid = createElement("section", "dashboard-grid");
    lowerGrid.append(createPanel("Proximas missoes", createMissionList(dashboard.upcoming_missions)), createPanel("Hoje", (() => {
        const today = createElement("div", "today-grid");
        today.append(createStat("Concluidas", String(dashboard.today.completed)), createStat("Ativas", String(dashboard.today.active)), createStat("Atrasadas", String(dashboard.today.overdue)));
        return today;
    })()), createPanel("Semana", (() => {
        const weekly = createElement("div", "today-grid");
        weekly.append(createStat("Missoes", String(dashboard.weekly.missions_completed)), createStat("XP ganho", String(dashboard.weekly.xp_gained)), createStat("Ouro ganho", String(dashboard.weekly.gold_gained), "gold"), createStat("Melhor dia", dashboard.weekly.best_day ?? "Sem dados"));
        return weekly;
    })()), createPanel("Medalha recente", createBadge(dashboard.recent_badge)));
    page.append(lowerGrid);
    root.replaceChildren(page);
}
export async function renderDashboard(root, isCurrent = () => true) {
    if (isCurrent()) {
        root.replaceChildren(createElement("p", "empty-state", "Carregando..."));
    }
    try {
        const dashboard = await apiGet("/dashboard");
        if (isCurrent()) {
            renderDashboardData(root, dashboard);
        }
    }
    catch (error) {
        if (!isCurrent()) {
            return;
        }
        const message = error instanceof Error ? error.message : "Erro desconhecido";
        root.replaceChildren(createElement("section", "error-panel", `Nao foi possivel carregar o dashboard: ${message}`));
    }
}
//# sourceMappingURL=dashboard.js.map
