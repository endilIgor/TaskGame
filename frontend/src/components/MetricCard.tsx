import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: ReactNode;
  detail?: string;
  tone?: "arcane" | "gold" | "danger";
}

export function MetricCard({ label, value, detail, tone = "arcane" }: MetricCardProps) {
  return (
    <article className={`metric-card metric-card-${tone} glass-panel`}>
      <span className="liquid-glass-surface" aria-hidden="true" />
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      {detail ? <span className="metric-detail">{detail}</span> : null}
    </article>
  );
}
