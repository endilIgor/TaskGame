import { useMemo, useState } from "react";
import { apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import { FormField, SelectInput, TextArea, TextInput } from "../components/FormControls";
import { MissionCard } from "../components/MissionCard";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { Difficulty, Mission, MissionCreatePayload, MissionProgressPayload, MissionStatus, MissionType, MissionUpdate } from "../types";

const initialForm = { title: "", description: "", type: "daily" as MissionType, difficulty: "easy" as Difficulty, category: "", target_date: "", progress_target: "" };
type MissionFormState = typeof initialForm;
type StatusFilter = "all" | MissionStatus;
type TypeFilter = "all" | MissionType;

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function campaignMinDate(): string {
  const minimumDate = new Date();
  minimumDate.setDate(minimumDate.getDate() + 30);
  return minimumDate.toISOString().slice(0, 10);
}

function todayWeekday(): number {
  const day = new Date().getDay();
  return day === 0 ? 6 : day - 1;
}

function isStarted(mission: Mission): boolean {
  return mission.start_date <= todayIsoDate();
}

function isScheduledToday(mission: Mission): boolean {
  if (mission.type !== "daily" || mission.repeat_days === null || mission.repeat_days.length === 0) return true;
  return mission.repeat_days.includes(todayWeekday());
}

function formFromMission(mission: Mission): MissionFormState {
  return {
    title: mission.title,
    description: mission.description ?? "",
    type: mission.type,
    difficulty: mission.difficulty,
    category: mission.category ?? "",
    target_date: mission.target_date ?? "",
    progress_target: mission.progress_target === null ? "" : String(mission.progress_target),
  };
}

function payloadFromForm(form: MissionFormState): MissionCreatePayload {
  return {
    title: form.title.trim(),
    type: form.type,
    difficulty: form.difficulty,
    description: form.description.trim() || null,
    category: form.category.trim() || null,
    target_date: form.type === "long_term" ? form.target_date || null : null,
    progress_target: form.type === "long_term" ? Number(form.progress_target) : null,
  };
}

function validateMissionForm(form: MissionFormState): string | null {
  if (!form.title.trim()) return "Informe um título para a missão.";
  const target = Number(form.progress_target);
  if (form.type === "long_term" && (!Number.isInteger(target) || target < 1)) {
    return "Campanhas precisam de uma meta de progresso positiva.";
  }
  if (form.type === "long_term" && (!form.target_date || form.target_date < campaignMinDate())) {
    return "Campanhas precisam de uma data alvo de pelo menos 1 mês.";
  }
  return null;
}

export function MissionsView() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [editing, setEditing] = useState<Record<number, MissionFormState>>({});
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | "create" | null>(null);
  const missions = useAsyncData(() => apiGet<Mission[]>("/missions?include_archived=true"), [refreshKey]);
  const refresh = () => setRefreshKey((key) => key + 1);

  const visibleMissions = useMemo(() => {
    if (missions.status !== "ready") return [];
    return missions.data.filter((mission) => {
      const statusMatches = statusFilter === "all" || mission.status === statusFilter;
      const typeMatches = typeFilter === "all" || mission.type === typeFilter;
      return statusMatches && typeMatches;
    });
  }, [missions, statusFilter, typeFilter]);

  async function createMission(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = validateMissionForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setBusyId("create");
    setError(null);
    try {
      await apiPost<Mission, MissionCreatePayload>("/missions", payloadFromForm(form));
      setForm(initialForm);
      refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível criar a missão.");
    } finally {
      setBusyId(null);
    }
  }

  async function runMissionAction(mission: Mission, action: "complete" | "archive" | "restore" | "delete" | "progress") {
    if (action === "delete" && !window.confirm(`Apagar "${mission.title}" permanentemente?`)) return;
    setBusyId(mission.id);
    setError(null);
    try {
      if (action === "complete") await apiPost(`/missions/${mission.id}/complete`);
      if (action === "archive") await apiPost<Mission>(`/missions/${mission.id}/archive`);
      if (action === "restore") await apiPost<Mission>(`/missions/${mission.id}/restore`);
      if (action === "delete") await apiDelete(`/missions/${mission.id}`);
      if (action === "progress") await apiPost<Mission, MissionProgressPayload>(`/missions/${mission.id}/progress`, { amount: 1 });
      refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível atualizar a missão.");
    } finally {
      setBusyId(null);
    }
  }

  async function saveMission(mission: Mission, editForm: MissionFormState) {
    const validationError = validateMissionForm(editForm);
    if (validationError) {
      setError(validationError);
      return;
    }
    const payload = payloadFromForm(editForm) as MissionUpdate;
    setBusyId(mission.id);
    setError(null);
    try {
      await apiPatch<Mission, MissionUpdate>(`/missions/${mission.id}`, payload);
      setEditing((current) => {
        const next = { ...current };
        delete next[mission.id];
        return next;
      });
      refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível editar a missão.");
    } finally {
      setBusyId(null);
    }
  }

  function updateEditForm(missionId: number, update: Partial<MissionFormState>) {
    setEditing((current) => ({ ...current, [missionId]: { ...current[missionId], ...update } }));
  }

  function renderMission(mission: Mission) {
    const editForm = editing[mission.id];
    const isActive = mission.status === "active";
    const isArchived = mission.status === "archived";
    const eligibleToday = isActive && isStarted(mission) && isScheduledToday(mission);
    const longTermTargetReached = mission.type === "long_term" && mission.progress_target !== null && mission.progress_current >= mission.progress_target;
    const canProgress = eligibleToday && mission.type === "long_term" && mission.progress_target !== null && mission.progress_current < mission.progress_target;
    const canComplete = eligibleToday && (mission.type !== "long_term" || longTermTargetReached);

    return (
      <article className="mission-row" key={mission.id}>
        <MissionCard mission={mission} />
        <div className="mission-actions">
          {editForm ? (
            <form className="compact-form" onSubmit={(event) => { event.preventDefault(); void saveMission(mission, editForm); }}>
              <TextInput required maxLength={120} value={editForm.title} aria-label={`Título de ${mission.title}`} onChange={(event) => updateEditForm(mission.id, { title: event.target.value })} />
              <SelectInput value={editForm.type} aria-label={`Tipo de ${mission.title}`} onChange={(event) => updateEditForm(mission.id, { type: event.target.value as MissionType, target_date: event.target.value === "long_term" ? editForm.target_date : "", progress_target: event.target.value === "long_term" ? editForm.progress_target : "" })}>
                <option value="daily">Diária</option>
                <option value="weekly">Semanal</option>
                <option value="long_term">Campanha</option>
              </SelectInput>
              <SelectInput value={editForm.difficulty} aria-label={`Dificuldade de ${mission.title}`} onChange={(event) => updateEditForm(mission.id, { difficulty: event.target.value as Difficulty })}>
                <option value="easy">Fácil</option>
                <option value="medium">Média</option>
                <option value="hard">Difícil</option>
                <option value="epic">Épica</option>
              </SelectInput>
              <TextInput maxLength={80} value={editForm.category} placeholder="Categoria" aria-label={`Categoria de ${mission.title}`} onChange={(event) => updateEditForm(mission.id, { category: event.target.value })} />
              {editForm.type === "long_term" ? (
                <>
                  <TextInput type="date" min={campaignMinDate()} required={editForm.type === "long_term"} value={editForm.target_date} aria-label={`Data alvo de ${mission.title}`} onChange={(event) => updateEditForm(mission.id, { target_date: event.target.value })} />
                  <TextInput type="number" min="1" required={editForm.type === "long_term"} value={editForm.progress_target} placeholder="Meta de progresso" aria-label={`Meta de progresso de ${mission.title}`} onChange={(event) => updateEditForm(mission.id, { progress_target: event.target.value })} />
                </>
              ) : null}
              <TextArea value={editForm.description} placeholder="Descrição" aria-label={`Descrição de ${mission.title}`} onChange={(event) => updateEditForm(mission.id, { description: event.target.value })} />
              <div className="row-actions">
                <button className="button primary" disabled={busyId === mission.id}>Salvar</button>
                <button className="button" type="button" onClick={() => setEditing((current) => { const next = { ...current }; delete next[mission.id]; return next; })}>Cancelar</button>
              </div>
            </form>
          ) : (
            <>
              <div className="row-actions">
                {canComplete ? <button className="button primary" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "complete")}>Concluir</button> : null}
                {canProgress ? <button className="button primary" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "progress")}>+1 progresso</button> : null}
                {isActive ? <button className="button danger" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "archive")}>Arquivar</button> : <span className="badge-status">{mission.status === "completed" ? "Concluída" : "Arquivada"}</span>}
                {isArchived ? <button className="button primary" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "restore")}>Restaurar</button> : null}
                <button className="button" type="button" disabled={busyId === mission.id} onClick={() => setEditing((current) => ({ ...current, [mission.id]: formFromMission(mission) }))}>Editar</button>
                <button className="button danger" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "delete")}>Apagar</button>
              </div>
              {isActive && mission.type === "long_term" ? <span className="badge-status">Campanhas concluem automaticamente ao atingir a meta.</span> : null}
            </>
          )}
        </div>
      </article>
    );
  }

  return (
    <section className="view-page missions-page" aria-labelledby="missions-heading">
      <header className="view-hero"><span className="section-kicker">Contratos</span><h1 className="page-heading" id="missions-heading">Missões</h1><p>Crie, acompanhe e refine seus contratos sem perder o ritmo da guilda.</p></header>
      <form className="panel mission-form" onSubmit={createMission}>
        <div className="section-heading">
          <div>
            <span className="section-kicker">Registro</span>
            <h2 className="panel-heading">Novo contrato</h2>
          </div>
          <span className="section-count">+</span>
        </div>
        <div className="form-grid">
          <FormField label="Título"><TextInput required maxLength={120} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></FormField>
          <FormField label="Descrição"><TextArea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></FormField>
          <FormField label="Tipo"><SelectInput value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as MissionType, target_date: event.target.value === "long_term" ? form.target_date : "", progress_target: event.target.value === "long_term" ? form.progress_target : "" })}><option value="daily">Diária</option><option value="weekly">Semanal</option><option value="long_term">Campanha</option></SelectInput></FormField>
          <FormField label="Dificuldade"><SelectInput value={form.difficulty} onChange={(event) => setForm({ ...form, difficulty: event.target.value as Difficulty })}><option value="easy">Fácil</option><option value="medium">Média</option><option value="hard">Difícil</option><option value="epic">Épica</option></SelectInput></FormField>
          <FormField label="Categoria"><TextInput maxLength={80} value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} /></FormField>
          {form.type === "long_term" ? (
            <>
              <FormField label="Data alvo"><TextInput type="date" min={campaignMinDate()} required={form.type === "long_term"} value={form.target_date} onChange={(event) => setForm({ ...form, target_date: event.target.value })} /></FormField>
              <FormField label="Meta de progresso"><TextInput type="number" min="1" required={form.type === "long_term"} value={form.progress_target} onChange={(event) => setForm({ ...form, progress_target: event.target.value })} /></FormField>
            </>
          ) : null}
        </div>
        <button className="button primary" disabled={busyId === "create"}>Registrar missão</button>
      </form>
      <section className="panel filters-panel" aria-label="Filtros de missões">
        <div className="section-heading">
          <div>
            <span className="section-kicker">Busca</span>
            <h2 className="panel-heading">Filtros</h2>
          </div>
          {missions.status === "ready" ? <span className="section-count">{visibleMissions.length}</span> : null}
        </div>
        <div className="form-grid">
          <FormField label="Status"><SelectInput value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}><option value="all">Todos</option><option value="active">Ativas</option><option value="completed">Concluídas</option><option value="archived">Arquivadas</option></SelectInput></FormField>
          <FormField label="Tipo"><SelectInput value={typeFilter} onChange={(event) => setTypeFilter(event.target.value as TypeFilter)}><option value="all">Todos</option><option value="daily">Diárias</option><option value="weekly">Semanais</option><option value="long_term">Campanhas</option></SelectInput></FormField>
        </div>
      </section>
      {error ? <ErrorPanel>{error}</ErrorPanel> : null}
      {missions.status === "loading" ? <LoadingPanel /> : null}
      {missions.status === "error" ? <ErrorPanel>{missions.error}</ErrorPanel> : null}
      {missions.status === "ready" ? <div className="mission-list">{visibleMissions.length ? visibleMissions.map(renderMission) : <EmptyState>Nenhuma missão encontrada para os filtros.</EmptyState>}</div> : null}
    </section>
  );
}
