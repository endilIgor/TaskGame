import { useState } from "react";
import { apiGet } from "../api/client";
import { MetricCard } from "../components/MetricCard";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { ReportPeriod } from "../types";

type ReportMode = "weekly" | "monthly";

export function ReportsView() {
  const [period, setPeriod] = useState<ReportMode>("weekly");
  const endpoint = period === "weekly" ? "/reports/weekly" : "/reports/monthly";
  const report = useAsyncData(() => apiGet<ReportPeriod>(endpoint), [period]);
  if (report.status === "loading") return <LoadingPanel />;
  if (report.status === "error") return <ErrorPanel>{report.error}</ErrorPanel>;
  const maximum = Math.max(
    ...report.data.daily_activity.map((day) => day.completions),
    1,
  );
  const periodLabel = period === "weekly" ? "Semana" : "Mes";

  return (
    <section className="view-page" aria-labelledby="reports-heading">
      <header>
        <span className="section-kicker">{periodLabel}</span>
        <h1 className="page-heading" id="reports-heading">Cronica</h1>
        <p className="report-period">{report.data.period_start} a {report.data.period_end} | Melhor dia: {report.data.best_day || "Sem dados"}</p>
      </header>
      <div className="period-toggle" aria-label="Periodo da cronica">
        <button className={`button${period === "weekly" ? " primary" : ""}`} type="button" onClick={() => setPeriod("weekly")}>Semana</button>
        <button className={`button${period === "monthly" ? " primary" : ""}`} type="button" onClick={() => setPeriod("monthly")}>Mes</button>
      </div>
      <div className="metric-grid report-metrics">
        <MetricCard label="Missoes concluidas" value={report.data.missions_completed} />
        <MetricCard label="Pontos de atencao" value={report.data.missions_failed} />
        <MetricCard label="XP ganho" value={report.data.xp_gained} />
        <MetricCard label="Ouro ganho" value={report.data.gold_gained} tone="gold" />
      </div>
      <section className="panel">
        <h2 className="panel-heading">Conclusoes do periodo</h2>
        <div className={`bar-chart ${period === "monthly" ? "monthly-chart" : "weekly-chart"}`}>
          {report.data.daily_activity.map((day) => {
            const total = day.completions;
            return (
              <div className="chart-column" key={day.date}>
                <span className="chart-value">{total}</span>
                <div
                  className={`chart-bar${total ? " filled" : ""}`}
                  style={{ height: `${Math.max(8, total / maximum * 100)}%` }}
                  aria-label={`${day.label}: ${total} conclusoes, ${day.xp_gained} XP, ${day.gold_gained} ouro`}
                />
                {day.xp_gained || day.gold_gained ? (
                  <>
                    <span className="chart-rewards">{day.xp_gained} XP</span>
                    <span className="chart-rewards">{day.gold_gained} ouro</span>
                  </>
                ) : null}
                <span className="chart-label">{day.label}</span>
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
          ) : <EmptyState>Nenhum objetivo concluido neste periodo.</EmptyState>}
        </section>
      </div>
    </section>
  );
}
