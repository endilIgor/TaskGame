import { useState } from "react";
import type { ReactNode } from "react";
import type { ViewKey } from "../types";

const navigation = [
  { key: "dashboard", label: "Salao", eyebrow: "Personagem" },
  { key: "missions", label: "Missoes", eyebrow: "Contratos" },
  { key: "goals", label: "Campanhas", eyebrow: "Objetivos" },
  { key: "badges", label: "Medalhas", eyebrow: "Conquistas" },
  { key: "rewards", label: "Loja", eyebrow: "Ouro" },
  { key: "reports", label: "Cronica", eyebrow: "Semana" },
  { key: "backup", label: "Arquivo", eyebrow: "Dados" },
] as const;

interface AppShellProps {
  renderView: (activeView: ViewKey) => ReactNode;
}

export function AppShell({ renderView }: AppShellProps) {
  const [activeView, setActiveView] = useState<ViewKey>("dashboard");
  const currentNavigation = navigation.find((item) => item.key === activeView) ?? navigation[0];

  return (
    <div className="app-shell guild-shell">
      <aside className="sidebar" aria-label="Navegacao principal" data-liquid-ignore>
        <div className="brand">TaskGame</div>
        <nav>
          {navigation.map((item) => (
            <button
              key={item.key}
              className={`nav-button${item.key === activeView ? " active" : ""}`}
              type="button"
              aria-current={item.key === activeView ? "page" : undefined}
              onClick={() => setActiveView(item.key)}
            >
              <span className="nav-eyebrow">{item.eyebrow}</span>
              <span>{item.label}</span>
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
