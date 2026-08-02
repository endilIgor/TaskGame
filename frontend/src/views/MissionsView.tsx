import { useState } from "react";
import { apiGet, apiPatch, apiPost } from "../api/client";
import { FormField, SelectInput, TextArea, TextInput } from "../components/FormControls";
import { MissionCard } from "../components/MissionCard";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { Difficulty, Mission, MissionCreatePayload, MissionProgressPayload, MissionType } from "../types";

const initialForm = { title: "", description: "", type: "daily" as MissionType, difficulty: "easy" as Difficulty, category: "", target_date: "", progress_target: "" };

export function MissionsView() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | "create" | null>(null);
  const missions = useAsyncData(() => apiGet<Mission[]>("/missions?include_archived=true"), [refreshKey]);
  const refresh = () => setRefreshKey((key) => key + 1);

  async function createMission(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const target = form.progress_target ? Number(form.progress_target) : null;
    const payload: MissionCreatePayload = { title: form.title.trim(), type: form.type, difficulty: form.difficulty, description: form.description.trim() || null, category: form.category.trim() || null, target_date: form.target_date || null, progress_target: target };
    setBusyId("create"); setError(null);
    try { await apiPost<Mission, MissionCreatePayload>("/missions", payload); setForm(initialForm); refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Nao foi possivel criar a missao."); } finally { setBusyId(null); }
  }

  async function runMissionAction(mission: Mission, action: "complete" | "archive" | "progress") {
    setBusyId(mission.id); setError(null);
    try {
      if (action === "complete") await apiPost(`/missions/${mission.id}/complete`);
      if (action === "archive") await apiPost<Mission>(`/missions/${mission.id}/archive`);
      if (action === "progress") await apiPost<Mission, MissionProgressPayload>(`/missions/${mission.id}/progress`, { amount: 1 });
      refresh();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Nao foi possivel atualizar a missao."); } finally { setBusyId(null); }
  }

  async function renameMission(mission: Mission, title: string) {
    if (!title.trim() || title.trim() === mission.title) return;
    setBusyId(mission.id); setError(null);
    try { await apiPatch<Mission, { title: string }>(`/missions/${mission.id}`, { title: title.trim() }); refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Nao foi possivel editar a missao."); } finally { setBusyId(null); }
  }

  return <section className="view-page" aria-labelledby="missions-heading">
    <header><span className="section-kicker">Contratos</span><h1 className="page-heading" id="missions-heading">Missoes</h1></header>
    <form className="panel mission-form" onSubmit={createMission}><h2 className="panel-heading">Novo contrato</h2><div className="form-grid">
      <FormField label="Titulo"><TextInput required maxLength={120} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></FormField>
      <FormField label="Descricao"><TextArea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></FormField>
      <FormField label="Tipo"><SelectInput value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as MissionType })}><option value="daily">Diaria</option><option value="weekly">Semanal</option><option value="long_term">Campanha</option></SelectInput></FormField>
      <FormField label="Dificuldade"><SelectInput value={form.difficulty} onChange={(event) => setForm({ ...form, difficulty: event.target.value as Difficulty })}><option value="easy">Facil</option><option value="medium">Media</option><option value="hard">Dificil</option><option value="epic">Epica</option></SelectInput></FormField>
      <FormField label="Categoria"><TextInput maxLength={80} value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} /></FormField>
      <FormField label="Data alvo"><TextInput type="date" value={form.target_date} onChange={(event) => setForm({ ...form, target_date: event.target.value })} /></FormField>
      <FormField label="Meta de progresso"><TextInput type="number" min="1" value={form.progress_target} onChange={(event) => setForm({ ...form, progress_target: event.target.value })} /></FormField>
    </div><button className="button primary" disabled={busyId === "create"}>Registrar missao</button></form>
    {error ? <ErrorPanel>{error}</ErrorPanel> : null}
    {missions.status === "loading" ? <LoadingPanel /> : null}
    {missions.status === "error" ? <ErrorPanel>{missions.error}</ErrorPanel> : null}
    {missions.status === "ready" ? <div className="mission-list">{missions.data.length ? missions.data.map((mission) => <article className="mission-row" key={mission.id}><MissionCard mission={mission} /><div className="mission-actions"><div className="row-actions">{mission.status === "active" ? <><button className="button primary" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "complete")}>Concluir</button>{mission.progress_target !== null ? <button className="button" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "progress")}>+1 progresso</button> : null}<button className="button danger" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "archive")}>Arquivar</button></> : <span className="badge-status">{mission.status === "completed" ? "Concluida" : "Arquivada"}</span>}</div><form className="rename-form" onSubmit={(event) => { event.preventDefault(); renameMission(mission, new FormData(event.currentTarget).get("title") as string); }}><TextInput name="title" defaultValue={mission.title} aria-label={`Renomear ${mission.title}`} /><button className="button" disabled={busyId === mission.id}>Salvar</button></form></div></article>) : <EmptyState>Nenhuma missao cadastrada.</EmptyState>}</div> : null}
  </section>;
}
