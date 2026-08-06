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
  const periodLabel = period === "weekly" ? "Semana" : "Mês";

  return (
    <section className="view-page" aria-labelledby="reports-heading">
      <header>
        <span className="section-kicker">{periodLabel}</span>
        <h1 className="page-heading" id="reports-heading">Crônica</h1>
        <p className="report-period">{report.data.period_start} a {report.data.period_end} | Melhor dia: {report.data.best_day || "Sem dados"}</p>
      </header>
      <div className="period-toggle" aria-label="Período da crônica">
        <button className={`button${period === "weekly" ? " primary" : ""}`} type="button" onClick={() => setPeriod("weekly")}>Semana</button>
        <button className={`button${period === "monthly" ? " primary" : ""}`} type="button" onClick={() => setPeriod("monthly")}>Mês</button>
      </div>
      <div className="metric-grid report-metrics">
        <MetricCard label="Missões concluídas" value={report.data.missions_completed} />
        <MetricCard label="Pontos de atenção" value={report.data.missions_failed} />
        <MetricCard label="XP ganho" value={report.data.xp_gained} />
        <MetricCard label="Ouro ganho" value={report.data.gold_gained} tone="gold" />
      </div>
      <section className="panel">
        <h2 className="panel-heading">Conclusões do período</h2>
        <div className={`bar-chart ${period === "monthly" ? "monthly-chart" : "weekly-chart"}`}>
          {report.data.daily_activity.map((day) => {
            const total = day.completions;
            const hasRewards = day.xp_gained > 0 || day.gold_gained > 0;
            const rewardTotal = Math.max(day.xp_gained + day.gold_gained, 1);
            return (
              <div className="chart-column" key={day.date}>
                <span className="chart-value">{total}</span>
                <div
                  className="chart-bar reward-comparison"
                  style={{ flexDirection: "column", height: `${Math.max(8, total / maximum * 100)}%` }}
                  aria-label={`${day.label}: ${total} conclusões, ${day.xp_gained} XP, ${day.gold_gained} ouro`}
                >
                  {hasRewards ? (
                    <>
                      <div className="chart-reward-segment xp" style={{ flexGrow: Math.max(day.xp_gained, 0), flexBasis: `${day.xp_gained / rewardTotal * 100}%` }}>
                        <span>XP</span>
                        <strong>{day.xp_gained}</strong>
                      </div>
                      <div className="chart-reward-segment gold" style={{ flexGrow: Math.max(day.gold_gained, 0), flexBasis: `${day.gold_gained / rewardTotal * 100}%` }}>
                        <span>Ouro</span>
                        <strong>{day.gold_gained}</strong>
                      </div>
                    </>
                  ) : null}
                </div>
                <span className="chart-label">{day.label}</span>
              </div>
            );
          })}
        </div>
      </section>
      <div className="analysis-grid">
        <section className="panel">
          <h2 className="panel-heading">Skills em destaque</h2>
          {report.data.top_categories.length ? (
            <div className="history-list">
              {report.data.top_categories.map((category) => (
                <div className="history-row" key={category.category}>
                  <strong>{category.category}</strong>
                  <span>{category.completions} conclusões</span>
                </div>
              ))}
            </div>
          ) : <EmptyState>Sem conclusões por skill.</EmptyState>}
        </section>
        <section className="panel">
          <h2 className="panel-heading">Objetivos concluídos</h2>
          {report.data.goals_completed.length ? (
            <div className="history-list">
              {report.data.goals_completed.map((goal) => <div className="history-row" key={goal}>{goal}</div>)}
            </div>
          ) : <EmptyState>Nenhum objetivo concluído neste período.</EmptyState>}
        </section>
      </div>
    </section>
  );
}
