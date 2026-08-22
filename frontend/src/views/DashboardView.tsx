import { apiGet } from "../api/client";
import { GameIcon } from "../components/GameIcon";
import { MetricCard } from "../components/MetricCard";
import { MissionCard } from "../components/MissionCard";
import { ProgressBar } from "../components/ProgressBar";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { DashboardData } from "../types";

export function DashboardView() {
  const dashboard = useAsyncData(() => apiGet<DashboardData>("/dashboard"), []);

  if (dashboard.status === "loading") return <LoadingPanel />;
  if (dashboard.status === "error") return <ErrorPanel>{dashboard.error}</ErrorPanel>;

  const { player, today, weekly, upcoming_missions: upcomingMissions, recent_badge: recentBadge } = dashboard.data;

  return (
    <section className="dashboard guild-main" aria-labelledby="guild-hall-heading">
      <header className="hero-panel">
        <div className="hero-copy">
          <span className="section-kicker">Salão da Guilda</span>
          <h1 id="guild-hall-heading">Nível {player.level}</h1>
          <p>NagiGame organiza missões, pontos, ouro e conquistas em um painel de aventura diária.</p>
          <div className="hero-chip-row" aria-label="Resumo rápido do personagem">
            <span className="hero-chip"><GameIcon variant="spark" />{player.total_xp} XP total</span>
            <span className="hero-chip gold"><GameIcon variant="coin" />{player.gold} ouro</span>
            <span className="hero-chip"><GameIcon variant="medal" />{player.current_streak} dias de sequência</span>
          </div>
        </div>
        <div className="hero-progress">
          <ProgressBar value={player.xp_into_level} max={player.xp_for_next_level} label="XP para o próximo nível" />
          <span className="hero-total-xp">{player.total_xp} XP total</span>
        </div>
      </header>

      <div className="metric-grid" aria-label="Resumo do personagem">
        <MetricCard label="Ouro" value={player.gold} detail="Disponível na loja" tone="gold" />
        <MetricCard label="Sequência atual" value={`${player.current_streak} dias`} detail={`Melhor: ${player.best_streak} dias`} />
        <MetricCard label="Concluídas hoje" value={today.completed} detail={`${today.active} ativas`} />
        <MetricCard label="Em atraso" value={today.overdue} detail="Missões pendentes" tone={today.overdue > 0 ? "danger" : "arcane"} />
      </div>

      <div className="dashboard-grid">
        <section className="panel guild-panel" aria-labelledby="today-heading">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Quadro diário</span>
              <h2 id="today-heading">Missões de hoje</h2>
            </div>
            <span className="section-count">{today.active} ativas</span>
          </div>
          <div className="today-grid">
            <MetricCard label="Concluídas" value={today.completed} />
            <MetricCard label="Ativas" value={today.active} />
            <MetricCard label="Atrasadas" value={today.overdue} tone={today.overdue > 0 ? "danger" : "arcane"} />
          </div>
        </section>

        <section className="panel guild-panel weekly-panel" aria-labelledby="weekly-heading">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Crônica semanal</span>
              <h2 id="weekly-heading">Esta semana</h2>
            </div>
          </div>
          <dl className="weekly-stats">
            <div><dt>Missões</dt><dd>{weekly.missions_completed}</dd></div>
            <div><dt>XP ganho</dt><dd>{weekly.xp_gained}</dd></div>
            <div><dt>Ouro ganho</dt><dd>{weekly.gold_gained}</dd></div>
            <div><dt>Melhor dia</dt><dd>{weekly.best_day || "Ainda por vir"}</dd></div>
          </dl>
        </section>
      </div>

      <div className="dashboard-grid dashboard-grid-missions">
        <section className="panel guild-panel" aria-labelledby="missions-heading">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Próximos contratos</span>
              <h2 id="missions-heading">Missões a caminho</h2>
            </div>
            <span className="section-count">{upcomingMissions.length}</span>
          </div>
          {upcomingMissions.length ? (
            <div className="mission-list">
              {upcomingMissions.map((mission) => <MissionCard key={mission.id} mission={mission} />)}
            </div>
          ) : <EmptyState>Nenhuma missão no horizonte.</EmptyState>}
        </section>

        <aside className="panel guild-panel badge-highlight" aria-labelledby="badge-heading">
          <span className="section-kicker">Última conquista</span>
          <h2 id="badge-heading">Medalha recente</h2>
          {recentBadge ? (
            <div className="badge-card">
              <span className="badge-emblem" aria-hidden="true"><GameIcon variant={recentBadge.earned ? "medal" : "ring"} /></span>
              <h3 className="badge-name">{recentBadge.name}</h3>
              <p>{recentBadge.description}</p>
              <span className="badge-status">{recentBadge.earned ? "Conquistada" : "Em progresso"}</span>
            </div>
          ) : <EmptyState>A próxima medalha aguarda seus feitos.</EmptyState>}
        </aside>
      </div>
    </section>
  );
}
