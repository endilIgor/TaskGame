import type { Mission } from "../types";
import { ProgressBar } from "./ProgressBar";

interface MissionCardProps {
  mission: Mission;
}

const difficultyLabels: Record<Mission["difficulty"], string> = {
  easy: "Fácil",
  medium: "Média",
  hard: "Difícil",
  epic: "Épica",
};

const missionTypeLabels: Record<Mission["type"], string> = {
  daily: "Diária",
  weekly: "Semanal",
  long_term: "Lendária",
};

const missionTypeIcons: Record<Mission["type"], string> = {
  daily: "✦",
  weekly: "◇",
  long_term: "▣",
};

const skillLabels: Record<string, string> = {
  knowledge: "Conhecimento",
  strength: "Força",
  money: "Dinheiro",
  health: "Saúde",
  creativity: "Criatividade",
  social: "Social",
};

const skillIcons: Record<string, string> = {
  knowledge: "✦",
  strength: "▲",
  money: "◈",
  health: "✚",
  creativity: "✧",
  social: "◌",
};

export function MissionCard({ mission }: MissionCardProps) {
  const hasProgress = mission.progress_target !== null;
  const skill = mission.skill ?? "";

  return (
    <div className={`quest-card${mission.completed_today ? " completed-today" : ""}`}>
      <span className={`quest-accent type-${mission.type}`} aria-hidden="true" />
      <div className="quest-card-header">
        <div>
          <span className={`quest-difficulty difficulty-${mission.difficulty}`}>{difficultyLabels[mission.difficulty]}</span>
          <h3 className="mission-title">{mission.title}</h3>
        </div>
        <span className={`mission-type type-${mission.type}`}><span aria-hidden="true">{missionTypeIcons[mission.type]}</span>{missionTypeLabels[mission.type]}</span>
      </div>
      {mission.description ? <p className="quest-description">{mission.description}</p> : null}
      <div className="quest-meta">
        <span className="skill-pill"><span aria-hidden="true">{skillIcons[skill] ?? "◇"}</span>{skillLabels[skill] ?? "Sem skill"}</span>
        {mission.target_date ? <span>Prazo: {mission.target_date}</span> : null}
      </div>
      {hasProgress ? <ProgressBar value={mission.progress_current} max={mission.progress_target ?? 1} label="Progresso da missão" /> : null}
      <div className="mission-reward-strip" aria-label="Resumo de recompensas da missão">
        <span><strong>{mission.completion_count}</strong> vezes concluída</span>
        <span><strong>{mission.total_xp_awarded}</strong> XP nesta missão</span>
        <span><strong>{mission.total_gold_awarded}</strong> ouro nesta missão</span>
      </div>
    </div>
  );
}
