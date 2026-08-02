import { apiGet } from "../api/client";
import { MetricCard } from "../components/MetricCard";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { WeeklyReport } from "../types";

const weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];

export function ReportsView() {
  const report = useAsyncData(() => apiGet<WeeklyReport>("/reports/weekly"), []);
  if (report.status === "loading") return <LoadingPanel />;
  if (report.status === "error") return <ErrorPanel>{report.error}</ErrorPanel>;
  const maximum = Math.max(...report.data.daily_completions, 1);

  return (
    <section className="view-page" aria-labelledby="reports-heading">
      <header>
        <span className="section-kicker">Semana</span>
        <h1 className="page-heading" id="reports-heading">Cronica</h1>
        <p className="report-period">{report.data.week_start} a {report.data.week_end} | Melhor dia: {report.data.best_day || "Sem dados"}</p>
      </header>
      <div className="metric-grid report-metrics">
        <MetricCard label="Missoes concluidas" value={report.data.missions_completed} />
        <MetricCard label="Pontos de atencao" value={report.data.missions_failed} />
        <MetricCard label="XP ganho" value={report.data.xp_gained} />
        <MetricCard label="Ouro ganho" value={report.data.gold_gained} tone="gold" />
      </div>
      <section className="panel">
        <h2 className="panel-heading">Conclusoes da semana</h2>
        <div className="bar-chart">
          {weekdays.map((day, index) => {
            const total = report.data.daily_completions[index] ?? 0;
            return (
              <div className="chart-column" key={day}>
                <span className="chart-value">{total}</span>
                <div
                  className={`chart-bar${total ? " filled" : ""}`}
                  style={{ height: `${Math.max(8, total / maximum * 100)}%` }}
                  aria-label={`${day}: ${total} conclusoes`}
                />
                <span className="chart-label">{day}</span>
              </div>
            );
          })}
        </div>
      </section>
      <div className="analysis-grid">
        <section className="panel">
          <h2 className="panel-heading">Categorias em destaque</h2>
          {report.data.top_categories.length ? (
            <div className="history-list">
              {report.data.top_categories.map((category) => (
                <div className="history-row" key={category.category}>
                  <strong>{category.category}</strong>
                  <span>{category.completions} conclusoes</span>
                </div>
              ))}
            </div>
          ) : <EmptyState>Sem conclusoes por categoria.</EmptyState>}
        </section>
        <section className="panel">
          <h2 className="panel-heading">Objetivos concluidos</h2>
          {report.data.goals_completed.length ? (
            <div className="history-list">
              {report.data.goals_completed.map((goal) => <div className="history-row" key={goal}>{goal}</div>)}
            </div>
          ) : <EmptyState>Nenhum objetivo concluido nesta semana.</EmptyState>}
        </section>
      </div>
    </section>
  );
}
