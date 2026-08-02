import { apiGet } from "./api.js";
import type { BadgeStatus } from "./types.js";

type IsCurrent = () => boolean;

function element<K extends keyof HTMLElementTagNameMap>(tagName: K, className?: string, text?: string): HTMLElementTagNameMap[K] {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export async function renderBadges(root: HTMLElement, isCurrent: IsCurrent = () => true): Promise<void> {
  if (isCurrent()) root.replaceChildren(element("p", "empty-state", "Carregando medalhas..."));
  try {
    const badges = await apiGet<BadgeStatus[]>("/badges");
    if (!isCurrent()) return;
    const page = element("section", "view-page");
    const grid = element("section", "badge-grid");
    page.append(element("h1", "page-heading", "Medalhas"));
    for (const badge of badges) {
      const tile = element("article", `badge-tile ${badge.earned ? "earned" : "locked"}`);
      tile.append(
        element("strong", "badge-name", badge.name),
        element("span", "mission-meta", badge.description),
        element("span", "badge-status", badge.earned ? "Conquistada" : `Meta: ${badge.threshold}`),
      );
      grid.append(tile);
    }
    if (badges.length === 0) grid.append(element("p", "empty-state", "Nenhuma medalha configurada."));
    page.append(grid);
    root.replaceChildren(page);
  } catch (error) {
    if (isCurrent()) {
      const message = error instanceof Error ? error.message : "Erro desconhecido";
      root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar as medalhas: ${message}`));
    }
  }
}
