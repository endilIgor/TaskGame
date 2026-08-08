import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPost } from "../api/client";
import { DateInput, FormField, SelectInput, TextArea, TextInput } from "../components/FormControls";
import { MissionCard } from "../components/MissionCard";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { BadgeStatus, Difficulty, Mission, MissionCompletePayload, MissionCompletion, MissionCreatePayload, MissionType, SkillType } from "../types";

const initialForm = { title: "", description: "", type: "daily" as MissionType, difficulty: "easy" as Difficulty, skill: "knowledge" as SkillType, target_date: "", progress_target: "" };
type MissionFormState = typeof initialForm;
type StatusFilter = "all" | "active" | "completed";
type TypeFilter = "all" | MissionType;
type RewardToast = { title: string; xp: number; gold: number; badges: BadgeStatus[] } | null;
const DEADLINE_TICK_MS = 30_000;

function todayIsoDate(): string {
  return formatLocalIsoDate(new Date());
}

function tomorrowIsoDate(): string {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return formatLocalIsoDate(tomorrow);
}

function formatLocalIsoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function campaignMinDate(): string {
  return todayIsoDate();
}

function endOfIsoDateLocal(isoDate: string): Date {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day, 23, 59, 59, 999);
}

function startOfIsoDateLocal(isoDate: string): Date {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day, 0, 0, 0, 0);
}

function nextCycleEndFromStart(startIsoDate: string, cycleDays: number, nowMs: number): Date {
  const cycleStart = startOfIsoDateLocal(startIsoDate);
  const cycleMs = cycleDays * 24 * 60 * 60 * 1000;
  const elapsedCycles = Math.max(0, Math.floor((nowMs - cycleStart.getTime()) / cycleMs));
  return new Date(cycleStart.getTime() + (elapsedCycles + 1) * cycleMs - 1);
}

function formatDateBR(isoDate: string): string {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

function formatCountdown(targetMs: number, nowMs: number): string {
  const diffMs = targetMs - nowMs;
  if (diffMs <= 0) return "Prazo esgotado";
  const totalMinutes = Math.floor(diffMs / 60_000);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function todayWeekday(): number {
  const day = new Date().getDay();
  return day === 0 ? 6 : day - 1;
}

function isStarted(mission: Mission): boolean {
  return mission.start_date <= todayIsoDate() || mission.start_date === tomorrowIsoDate();
}

function isScheduledToday(mission: Mission): boolean {
  if (mission.type !== "daily" || mission.repeat_days === null || mission.repeat_days.length === 0) return true;
  return mission.repeat_days.includes(todayWeekday());
}

function payloadFromForm(form: MissionFormState): MissionCreatePayload {
  return {
    title: form.title.trim(),
    type: form.type,
    difficulty: form.difficulty,
    description: form.description.trim() || null,
    skill: form.skill,
    start_date: todayIsoDate(),
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
    return "Campanhas precisam de uma data alvo a partir de hoje.";
  }
  return null;
}

export function MissionsView() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [error, setError] = useState<string | null>(null);
  const [rewardToast, setRewardToast] = useState<RewardToast>(null);
  const [busyId, setBusyId] = useState<number | "create" | null>(null);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const missions = useAsyncData(() => apiGet<Mission[]>(`/missions?today=${todayIsoDate()}`), [refreshKey]);
  const refresh = () => setRefreshKey((key) => key + 1);

  useEffect(() => {
    const interval = window.setInterval(() => setNowMs(Date.now()), DEADLINE_TICK_MS);
    return () => window.clearInterval(interval);
  }, []);

  const visibleMissions = useMemo(() => {
    if (missions.status !== "ready") return [];
    return missions.data.filter((mission) => {
      const statusMatches = statusFilter === "all" || mission.status === statusFilter || (statusFilter === "completed" && mission.completed_today);
      const typeMatches = typeFilter === "all" || mission.type === typeFilter;
      return statusMatches && typeMatches;
    });
  }, [missions, statusFilter, typeFilter]);

  const completedVisibleMissions = visibleMissions.filter((mission) => mission.completed_today || mission.status === "completed");
  const openVisibleMissions = visibleMissions.filter((mission) => !mission.completed_today && mission.status !== "completed");

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

  async function runMissionAction(mission: Mission, action: "complete" | "delete") {
    if (action === "delete" && !window.confirm(`Apagar "${mission.title}" permanentemente?`)) return;
    setBusyId(mission.id);
    setError(null);
    try {
      if (action === "complete") {
        const completion = await apiPost<MissionCompletion, MissionCompletePayload>(`/missions/${mission.id}/complete`, { completed_on: todayIsoDate() });
        setRewardToast({ title: mission.title, xp: completion.xp_awarded, gold: completion.gold_awarded, badges: completion.unlocked_badges });
      }
      if (action === "delete") {
        await apiDelete(`/missions/${mission.id}`);
      }
      refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível atualizar a missão.");
    } finally {
      setBusyId(null);
    }
  }

  function renderMissionDeadline(mission: Mission) {
    if (mission.type === "long_term") {
      if (!mission.target_date || mission.status === "completed") return null;
      const deadlineMs = endOfIsoDateLocal(mission.target_date).getTime();
      const expired = deadlineMs <= nowMs;
      return (
        <div className={`daily-timer${expired ? " done" : ""}`} aria-label={`Prazo de ${mission.title}`}>
          <span className="daily-timer-label">Prazo da campanha</span>
          <strong>{formatCountdown(deadlineMs, nowMs)}</strong>
          <span className="mission-meta">até {formatDateBR(mission.target_date)}</span>
        </div>
      );
    }
    if (mission.completed_today) return null;
    const cycleDays = mission.type === "daily" ? 1 : 7;
    const deadlineMs = nextCycleEndFromStart(mission.start_date, cycleDays, nowMs).getTime();
    return (
      <div className="daily-timer" aria-label={`Prazo de ${mission.title}`}>
        <span className="daily-timer-label">Ciclo de {mission.type === "daily" ? "24h" : "7 dias"}</span>
        <strong>{formatCountdown(deadlineMs, nowMs)}</strong>
        <span className="mission-meta">até renovar</span>
      </div>
    );
  }

  function renderMission(mission: Mission) {
    const isActive = mission.status === "active";
    const eligibleToday = isActive && isStarted(mission) && isScheduledToday(mission);
    const longTermTargetReached = mission.type === "long_term" && mission.progress_target !== null && mission.progress_current >= mission.progress_target;
    const canComplete = eligibleToday && !mission.completed_today && mission.type !== "long_term";
    const repeatLabel = mission.type === "daily" ? "Repetir amanhã" : mission.type === "weekly" ? "Repetir no próximo ciclo" : "Concluída";

    return (
      <article className="mission-row" key={mission.id}>
        <MissionCard mission={mission} />
        <div className="mission-actions">
          {renderMissionDeadline(mission)}
          <div className="row-actions">
            {canComplete ? <button className="button primary" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "complete")}>Concluir</button> : null}
            {mission.completed_today ? <button className="button success" type="button" disabled>{repeatLabel}</button> : null}
            <button className="button danger" type="button" disabled={busyId === mission.id} onClick={() => runMissionAction(mission, "delete")}>Excluir</button>
          </div>
          {mission.completion_count > 0 ? <span className="badge-status">Concluída {mission.completion_count}x · {mission.total_xp_awarded} XP · {mission.total_gold_awarded} ouro nesta missão</span> : null}
          {isActive && mission.type === "long_term" && !longTermTargetReached ? <span className="badge-status">Campanhas lendárias ainda usam progresso automático; conclusão manual fica desativada por enquanto.</span> : null}
        </div>
      </article>
    );
  }

  return (
    <section className="view-page missions-page" aria-labelledby="missions-heading">
      <header className="view-hero missions-hero"><span className="section-kicker">Quadro de contratos</span><h1 className="page-heading" id="missions-heading">Central de missões</h1><p>Inspirado em Habitica, Linear e Raycast: registre missões como contratos de RPG, acompanhe skills e veja recompensas sem parecer uma planilha simples.</p></header>
      <form className="panel mission-form" onSubmit={createMission}>
        <div className="section-heading">
          <div>
            <span className="section-kicker">Criador de quest</span>
            <h2 className="panel-heading">Novo contrato da guilda</h2>
          </div>
          <span className="section-count">✦</span>
        </div>
        <div className="quest-composer-grid">
          <FormField className="field-title" label="Nome da missão" hint="Curto, claro e com cara de objetivo."><TextInput required maxLength={120} placeholder="Ex: Ler 3 páginas" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></FormField>
          <FormField className="field-type" label="Tipo"><SelectInput value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as MissionType, target_date: event.target.value === "long_term" ? form.target_date : "", progress_target: event.target.value === "long_term" ? form.progress_target : "" })}><option value="daily">Diária</option><option value="weekly">Semanal</option><option value="long_term">Lendária</option></SelectInput></FormField>
          <FormField className="field-description" label="Descrição / contexto" hint="Aqui fica a história da quest, critério de conclusão ou observação."><TextArea value={form.description} placeholder="O que conta como feito? Qual o contexto dessa aventura?" onChange={(event) => setForm({ ...form, description: event.target.value })} /></FormField>
          <FormField className="field-difficulty" label="Dificuldade"><SelectInput value={form.difficulty} onChange={(event) => setForm({ ...form, difficulty: event.target.value as Difficulty })}><option value="easy">Fácil</option><option value="medium">Média</option><option value="hard">Difícil</option><option value="epic">Épica</option></SelectInput></FormField>
          <FormField className="field-skill" label="Skill afetada"><SelectInput value={form.skill} onChange={(event) => setForm({ ...form, skill: event.target.value as SkillType })}><option value="knowledge">Conhecimento</option><option value="strength">Força</option><option value="money">Dinheiro</option><option value="health">Saúde</option><option value="creativity">Criatividade</option><option value="social">Social</option></SelectInput></FormField>
          {form.type === "long_term" ? (
            <>
              <FormField className="field-target-date" label="Data alvo"><DateInput min={campaignMinDate()} required={form.type === "long_term"} value={form.target_date} onChange={(value) => setForm({ ...form, target_date: value })} /></FormField>
              <FormField className="field-progress-target" label="Meta de progresso"><TextInput type="number" min="1" required={form.type === "long_term"} value={form.progress_target} onChange={(event) => setForm({ ...form, progress_target: event.target.value })} /></FormField>
            </>
          ) : null}
        </div>
        <div className="composer-footer"><span>XP e ouro são calculados pela dificuldade da missão.</span><button className="button primary" disabled={busyId === "create"}>Registrar missão</button></div>
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
          <FormField label="Status"><SelectInput value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}><option value="all">Todos</option><option value="active">Ativas</option><option value="completed">Concluídas</option></SelectInput></FormField>
          <FormField label="Tipo"><SelectInput value={typeFilter} onChange={(event) => setTypeFilter(event.target.value as TypeFilter)}><option value="all">Todos</option><option value="daily">Diárias</option><option value="weekly">Semanais</option><option value="long_term">Lendárias</option></SelectInput></FormField>
        </div>
      </section>
      {error ? <ErrorPanel>{error}</ErrorPanel> : null}
      {rewardToast ? (
        <div className="reward-popover" role="status" aria-live="polite">
          <button className="reward-popover-close" type="button" aria-label="Fechar recompensa" onClick={() => setRewardToast(null)}>×</button>
          <span className="section-kicker">Missão concluída</span>
          <h2>{rewardToast.title}</h2>
          <div className="reward-popover-prizes"><span>+{rewardToast.xp} XP</span><span>+{rewardToast.gold} ouro</span></div>
          {rewardToast.badges.length ? <div className="achievement-pop"><strong>Nova conquista!</strong>{rewardToast.badges.map((badge) => <span key={badge.code}>◆ {badge.name}</span>)}</div> : null}
        </div>
      ) : null}
      {missions.status === "loading" ? <LoadingPanel /> : null}
      {missions.status === "error" ? <ErrorPanel>{missions.error}</ErrorPanel> : null}
      {missions.status === "ready" ? visibleMissions.length ? (
        <div className="mission-board">
          <section className="panel mission-column">
            <div className="section-heading"><div><span className="section-kicker">Disponíveis</span><h2 className="panel-heading">Para fazer</h2></div><span className="section-count">{openVisibleMissions.length}</span></div>
            <div className="mission-list">{openVisibleMissions.length ? openVisibleMissions.map(renderMission) : <EmptyState>Nada pendente neste filtro.</EmptyState>}</div>
          </section>
          <section className="panel mission-column completed-column">
            <div className="section-heading"><div><span className="section-kicker">Concluídas</span><h2 className="panel-heading">Feitas hoje / finalizadas</h2></div><span className="section-count">{completedVisibleMissions.length}</span></div>
            <div className="mission-list">{completedVisibleMissions.length ? completedVisibleMissions.map(renderMission) : <EmptyState>As missões concluídas aparecem aqui.</EmptyState>}</div>
          </section>
        </div>
      ) : <EmptyState>Nenhuma missão encontrada para os filtros.</EmptyState> : null}
    </section>
  );
}
