import { apiGet } from "./api.js";
const weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];
function element                                       (tagName   , className         , text         )                           {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function stat(label        , value        , valueClassName         )              {
  const card = element("article", "stat-card");
  card.append(element("span", "stat-label", label), element("strong", `stat-value${valueClassName ? ` ${valueClassName}` : ""}`, value));
  return card;
}
function createChart(report              )              {
  const chart = element("section", "panel report-chart");
  chart.append(element("h2", "panel-heading", "Conclusoes da semana"));
  const bars = element("div", "bar-chart");
  const maximum = Math.max(...report.daily_completions, 1);
  weekdays.forEach((day, index) => {
    const column = element("div", "chart-column");
    const value = report.daily_completions[index] ?? 0;
    const bar = element("div", `chart-bar${value > 0 ? " filled" : ""}`);
    bar.style.height = `${Math.max(8, (value / maximum) * 100)}%`;
    bar.setAttribute("aria-label", `${day}: ${value} conclusoes`);
    column.append(bar, element("span", "chart-label", day));
    bars.append(column);
  });
  chart.append(bars);
  return chart;
}
function createAnalysis(report              )              {
  const grid = element("section", "analysis-grid");
  const categories = element("section", "panel");
  categories.append(element("h2", "panel-heading", "Categorias em destaque"));
  const categoryList = element("div", "history-list");
  if (report.top_categories.length === 0) categoryList.append(element("p", "empty-state", "Sem conclusoes por categoria."));
  for (const category of report.top_categories) {
    const row = element("div", "history-row");
    row.append(element("strong", undefined, category.category), element("span", "mission-meta", `${category.completions} conclusoes`));
    categoryList.append(row);
  }
  categories.append(categoryList);
  const goals = element("section", "panel");
  goals.append(element("h2", "panel-heading", "Objetivos concluidos"));
  const goalList = element("div", "history-list");
  if (report.goals_completed.length === 0) goalList.append(element("p", "empty-state", "Nenhum objetivo concluido nesta semana."));
  for (const goal of report.goals_completed) goalList.append(element("div", "history-row", goal));
  goals.append(goalList);
  grid.append(categories, goals);
  return grid;
}
function reportPage(root             , report              , isCurrent           )              {
  const page = element("section", "view-page");
  const history = element("form", "panel history-controls");
  const week = element("label", "form-field");
  week.append(element("span", "field-label", "Semana iniciada em"));
  const weekInput = element("input")                    ;
  weekInput.type = "date";
  weekInput.value = report.week_start;
  week.append(weekInput);
  const load = element("button", "button", "Carregar semana")                     ;
  load.type = "submit";
  history.append(week, load);
  history.addEventListener("submit", (event) => {
    event.preventDefault();
    void (async () => {
      load.disabled = true;
      try {
        const selected = await apiGet              (`/reports/weekly/${weekInput.value}`);
        if (isCurrent()) root.replaceChildren(reportPage(root, selected, isCurrent));
      } catch (error) {
        if (isCurrent()) {
          const message = error instanceof Error ? error.message : "Erro desconhecido";
          root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar a semana: ${message}`));
        }
      } finally {
        if (isCurrent()) load.disabled = false;
      }
    })();
  });
  const summary = element("section", "summary-grid");
  summary.append(
    stat("Missoes concluidas", String(report.missions_completed)),
    stat("Missoes falhas", String(report.missions_failed)),
    stat("XP ganho", String(report.xp_gained)),
    stat("Ouro ganho", String(report.gold_gained), "gold"),
    stat("Streak atual", `${report.current_streak} dias`),
    stat("Melhor streak", `${report.best_streak} dias`),
  );
  page.append(
    element("h1", "page-heading", "Relatorio semanal"),
    history,
    element("p", "report-period", `${report.week_start} a ${report.week_end} | Melhor dia: ${report.best_day ?? "Sem dados"}`),
    summary,
    createChart(report),
    createAnalysis(report),
  );
  return page;
}
export async function renderReports(root             , isCurrent            = () => true)                {
  if (isCurrent()) root.replaceChildren(element("p", "empty-state", "Carregando relatorio..."));
  try {
    const report = await apiGet              ("/reports/weekly");
    if (!isCurrent()) return;
    root.replaceChildren(reportPage(root, report, isCurrent));
  } catch (error) {
    if (isCurrent()) {
      const message = error instanceof Error ? error.message : "Erro desconhecido";
      root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar o relatorio: ${message}`));
    }
  }
}
