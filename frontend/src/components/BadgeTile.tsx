import type { BadgeStatus } from "../types";
import { GameIcon, type GameIconVariant } from "./GameIcon";

const conditionLabels: Record<string, string> = {
  streak: "Sequência",
  missions_completed: "Missões concluídas",
  goals_completed: "Objetivos concluídos",
  perfect_week: "Rotina perfeita",
  reward_purchases: "Compras na loja",
  xp_total: "XP acumulado",
  total_xp: "XP acumulado",
  rewards_purchased: "Compras na loja",
  daily_missions_completed: "Missões diárias",
  weekly_missions_completed: "Missões semanais",
  epic_missions_completed: "Missões épicas",
  hero_class_warrior: "Personagem Guerreiro",
  hero_class_mage: "Personagem Mago",
  hero_class_archer: "Personagem Arqueiro",
  hero_class_guardian: "Personagem Guardião",
};

const heroBadgeNames: Record<string, string> = {
  class_warrior: "Guerreiro",
  class_mage: "Mago",
  class_archer: "Arqueiro",
  class_guardian: "Guardião",
};

function badgeTheme(badge: BadgeStatus): string {
  if (badge.code.startsWith("class_")) return `hero-${badge.code.replace("class_", "")}`;
  if (badge.condition_type.includes("mission") || badge.code.includes("contracts")) return "missions";
  if (badge.condition_type.includes("streak") || badge.code.includes("streak")) return "streak";
  if (badge.condition_type.includes("xp")) return "xp";
  return "guild";
}

function badgeIcon(badge: BadgeStatus): GameIconVariant {
  if (badge.code.startsWith("class_")) return "shield";
  if (badge.condition_type.includes("mission") || badge.code.includes("contracts")) return "scroll";
  if (badge.condition_type.includes("streak") || badge.code.includes("streak")) return "spark";
  if (badge.condition_type.includes("xp")) return "diamond";
  return badge.earned ? "medal" : "ring";
}

function badgeStory(badge: BadgeStatus): string {
  const heroName = heroBadgeNames[badge.code];
  if (heroName) return `Medalha do personagem ${heroName}`;
  if (badge.condition_type.includes("mission") || badge.code.includes("contracts")) return "Medalha de missão";
  if (badge.condition_type.includes("streak") || badge.code.includes("streak")) return "Medalha de sequência";
  return "Medalha da guilda";
}

function formatDate(value: string | null): string {
  if (value === null) return "Ainda bloqueada";
  return new Date(value).toLocaleDateString("pt-BR");
}

export function BadgeTile({ badge }: { badge: BadgeStatus }) {
  const condition = conditionLabels[badge.condition_type] ?? badge.condition_type;
  const theme = badgeTheme(badge);

  return (
    <article className={`badge-tile achievement-tile badge-theme-${theme} ${badge.earned ? "earned" : "locked"}`}>
      <span className="badge-emblem" aria-hidden="true"><GameIcon variant={badgeIcon(badge)} /></span>
      <span className="badge-story">{badgeStory(badge)}</span>
      <h2 className="badge-name">{badge.name}</h2>
      <p className="quest-description">{badge.description}</p>
      <span className="badge-status">{condition}: {badge.threshold}</span>
      <time className="badge-status" dateTime={badge.earned_at ?? undefined}>{badge.earned ? `Conquistada em ${formatDate(badge.earned_at)}` : formatDate(null)}</time>
    </article>
  );
}
