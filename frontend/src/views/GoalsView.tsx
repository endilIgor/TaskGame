import { apiGet, apiPost } from "../api/client";
import { MissionCard } from "../components/MissionCard";
import { ProgressBar } from "../components/ProgressBar";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { Goal, Mission, MissionProgressPayload } from "../types";
import { useState } from "react";

export function GoalsView() {
  const [refreshKey, setRefreshKey] = useState(0); const [error, setError] = useState<string | null>(null); const [busyId, setBusyId] = useState<number | null>(null);
  const goals = useAsyncData(() => apiGet<Goal[]>("/goals"), [refreshKey]);
  async function advance(goal: Goal) { setBusyId(goal.id); setError(null); try { await apiPost<Mission, MissionProgressPayload>(`/missions/${goal.id}/progress`, { amount: 1 }); setRefreshKey((key) => key + 1); } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível atualizar o objetivo."); } finally { setBusyId(null); } }
  return <section className="view-page" aria-labelledby="goals-heading"><header><span className="section-kicker">Objetivos</span><h1 className="page-heading" id="goals-heading">Campanhas</h1></header>{error ? <ErrorPanel>{error}</ErrorPanel> : null}{goals.status === "loading" ? <LoadingPanel /> : null}{goals.status === "error" ? <ErrorPanel>{goals.error}</ErrorPanel> : null}{goals.status === "ready" ? <div className="goal-list">{goals.data.length ? goals.data.map((goal) => <article className="goal-row" key={goal.id}><MissionCard mission={goal} /><ProgressBar value={goal.progress_current} max={goal.progress_target ?? 1} label={`${goal.progress_percent}% concluído`} />{goal.status === "active" ? <button className="button primary" type="button" disabled={busyId === goal.id} onClick={() => advance(goal)}>Avançar +1</button> : <span className="badge-status">Concluído</span>}</article>) : <EmptyState>Nenhuma campanha ativa.</EmptyState>}</div> : null}</section>;
}
