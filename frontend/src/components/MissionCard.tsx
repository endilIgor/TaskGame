import type { Mission } from "../types";
import { GameIcon } from "./GameIcon";
import type { GameIconVariant } from "./GameIcon";
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

const missionTypeIcons: Record<Mission["type"], GameIconVariant> = {
  daily: "spark",
  weekly: "scroll",
  long_term: "flag",
};

const skillLabels: Record<string, string> = {
  knowledge: "Conhecimento",
  strength: "Força",
  money: "Dinheiro",
  health: "Saúde",
  creativity: "Criatividade",
  social: "Social",
};

const skillIcons: Record<string, GameIconVariant> = {
  knowledge: "spark",
  strength: "triangle",
  money: "coin",
  health: "cross",
  creativity: "diamond",
  social: "ring",
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
        <span className={`mission-type type-${mission.type}`}><GameIcon variant={missionTypeIcons[mission.type]} />{missionTypeLabels[mission.type]}</span>
      </div>
      {mission.description ? <p className="quest-description">{mission.description}</p> : null}
      <div className="quest-meta">
        <span className="skill-pill"><GameIcon variant={skillIcons[skill] ?? "spark"} />{skillLabels[skill] ?? "Sem skill"}</span>
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
