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
  long_term: "Campanha",
};

export function MissionCard({ mission }: MissionCardProps) {
  const hasProgress = mission.progress_target !== null;

  return (
    <div className="quest-card">
      <div className="quest-card-header">
        <div>
          <span className={`quest-difficulty difficulty-${mission.difficulty}`}>{difficultyLabels[mission.difficulty]}</span>
          <h3 className="mission-title">{mission.title}</h3>
        </div>
        <span className="mission-type">{missionTypeLabels[mission.type]}</span>
      </div>
      {mission.description ? <p className="quest-description">{mission.description}</p> : null}
      <div className="quest-meta">
        <span>{mission.category || "Sem categoria"}</span>
        {mission.target_date ? <span>Prazo: {mission.target_date}</span> : null}
      </div>
      {hasProgress ? <ProgressBar value={mission.progress_current} max={mission.progress_target} label="Progresso da missão" /> : null}
    </div>
  );
}
