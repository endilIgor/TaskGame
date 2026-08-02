import type { BadgeStatus } from "../types";

export function BadgeTile({ badge }: { badge: BadgeStatus }) {
  return (
    <article className={`badge-tile ${badge.earned ? "earned" : "locked"}`}>
      <span className="badge-emblem" aria-hidden="true">{badge.earned ? "*" : "?"}</span>
      <h2 className="badge-name">{badge.name}</h2>
      <p className="quest-description">{badge.description}</p>
      <span className="badge-status">{badge.earned ? "Conquistada" : `Meta: ${badge.threshold}`}</span>
    </article>
  );
}
