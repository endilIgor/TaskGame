import type { ReactNode } from "react";

interface StatePanelProps {
  children?: ReactNode;
}

export function LoadingPanel() {
  return <section className="panel" aria-live="polite">Carregando...</section>;
}

export function EmptyState({ children = "Nada para mostrar ainda." }: StatePanelProps) {
  return <section className="panel empty-state">{children}</section>;
}

export function ErrorPanel({ children = "Erro inesperado." }: StatePanelProps) {
  return <section className="error-panel" role="alert">{children}</section>;
}
