import { apiGet } from "./api.js";
const weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];
function element(tagName, className, text) {
    const node = document.createElement(tagName);
    if (className)
        node.className = className;
    if (text !== undefined)
        node.textContent = text;
    return node;
}
function stat(label, value, valueClassName) {
    const card = element("article", "stat-card");
    card.append(element("span", "stat-label", label), element("strong", `stat-value${valueClassName ? ` ${valueClassName}` : ""}`, value));
    return card;
}
function createChart(report) {
    const chart = element("section", "panel report-chart");
    chart.append(element("h2", "panel-heading", "Conclusoes da semana"));
    const bars = element("div", "bar-chart");
    const maximum = Math.max(report.missions_completed, 1);
    weekdays.forEach((day, index) => {
        const column = element("div", "chart-column");
        const bar = element("div", `chart-bar${index === 0 ? " filled" : ""}`);
        const value = index === 0 ? report.missions_completed : 0;
        bar.style.height = `${Math.max(8, (value / maximum) * 100)}%`;
        bar.setAttribute("aria-label", `${day}: ${value} conclusoes`);
        column.append(bar, element("span", "chart-label", day));
        bars.append(column);
    });
    chart.append(bars);
    return chart;
}
export async function renderReports(root, isCurrent = () => true) {
    if (isCurrent())
        root.replaceChildren(element("p", "empty-state", "Carregando relatorio..."));
    try {
        const report = await apiGet("/reports/weekly");
        if (!isCurrent())
            return;
        const page = element("section", "view-page");
        const summary = element("section", "summary-grid");
        summary.append(stat("Missoes concluidas", String(report.missions_completed)), stat("Missoes falhas", String(report.missions_failed)), stat("XP ganho", String(report.xp_gained)), stat("Ouro ganho", String(report.gold_gained), "gold"), stat("Streak atual", `${report.current_streak} dias`), stat("Melhor streak", `${report.best_streak} dias`));
        page.append(element("h1", "page-heading", "Relatorio semanal"), element("p", "report-period", `${report.week_start} a ${report.week_end} | Melhor dia: ${report.best_day ?? "Sem dados"}`), summary, createChart(report));
        root.replaceChildren(page);
    }
    catch (error) {
        if (isCurrent()) {
            const message = error instanceof Error ? error.message : "Erro desconhecido";
            root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar o relatorio: ${message}`));
        }
    }
}
//# sourceMappingURL=reports.js.map
