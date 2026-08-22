import { useState } from "react";
import type { ReactNode } from "react";
import type { ViewKey } from "../types";

const navigation = [
  { key: "dashboard", label: "Salão", eyebrow: "Personagem" },
  { key: "missions", label: "Missões", eyebrow: "Contratos" },
  { key: "journal", label: "Diário", eyebrow: "Aventuras" },
  { key: "goals", label: "Campanhas", eyebrow: "Objetivos" },
  { key: "badges", label: "Medalhas", eyebrow: "Conquistas" },
  { key: "rewards", label: "Loja", eyebrow: "Ouro" },
  { key: "reports", label: "Crônica", eyebrow: "Relatórios" },
] as const;

const navigationIcons: Record<ViewKey, string> = {
  dashboard: "✦",
  missions: "◇",
  journal: "✎",
  goals: "▣",
  badges: "◆",
  rewards: "◈",
  reports: "☷",
};

interface AppShellProps {
  renderView: (activeView: ViewKey) => ReactNode;
}

export function AppShell({ renderView }: AppShellProps) {
  const [activeView, setActiveView] = useState<ViewKey>("dashboard");
  const currentNavigation = navigation.find((item) => item.key === activeView) ?? navigation[0];

  return (
    <div className="app-shell guild-shell" data-liquid-ignore>
      <aside className="sidebar" aria-label="Navegação principal">
        <div className="brand-block">
          <div className="brand-lockup">
            <img className="brand-mark" src="/app-icon.svg" alt="" aria-hidden="true" />
            <div>
              <div className="brand">NagiGame</div>
              <p className="brand-tagline">Seu RPG moderno de produtividade</p>
            </div>
          </div>
        </div>
        <nav>
          {navigation.map((item) => (
            <button
              key={item.key}
              className={`nav-button${item.key === activeView ? " active" : ""}`}
              type="button"
              aria-current={item.key === activeView ? "page" : undefined}
              onClick={() => setActiveView(item.key)}
            >
              <span className="nav-icon" aria-hidden="true">{navigationIcons[item.key]}</span>
              <span className="nav-copy">
                <span className="nav-eyebrow">{item.eyebrow}</span>
                <span className="nav-label">{item.label}</span>
              </span>
            </button>
          ))}
        </nav>
      </aside>
      <main className="content" aria-label={`${currentNavigation.label}: ${currentNavigation.eyebrow}`}>
        {renderView(activeView)}
      </main>
    </div>
  );
}
