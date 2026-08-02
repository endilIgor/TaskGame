import type { BadgeStatus } from "../types";

const conditionLabels: Record<string, string> = {
  streak: "Sequencia",
  missions_completed: "Missoes concluidas",
  goals_completed: "Objetivos concluidos",
  perfect_week: "Rotina perfeita",
  reward_purchases: "Compras na loja",
  xp_total: "XP acumulado",
};

function formatDate(value: string | null): string {
  if (value === null) return "Ainda bloqueada";
  return new Date(value).toLocaleDateString("pt-BR");
}

export function BadgeTile({ badge }: { badge: BadgeStatus }) {
  const condition = conditionLabels[badge.condition_type] ?? badge.condition_type;

  return (
    <article className={`badge-tile ${badge.earned ? "earned" : "locked"}`}>
      <span className="badge-emblem" aria-hidden="true">{badge.earned ? "*" : "?"}</span>
      <h2 className="badge-name">{badge.name}</h2>
      <p className="quest-description">{badge.description}</p>
      <span className="badge-status">{condition}: {badge.threshold}</span>
      <time className="badge-status" dateTime={badge.earned_at ?? undefined}>{badge.earned ? `Conquistada em ${formatDate(badge.earned_at)}` : formatDate(null)}</time>
    </article>
  );
}
