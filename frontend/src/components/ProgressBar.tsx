interface ProgressBarProps {
  value: number;
  max: number;
  label: string;
}

export function ProgressBar({ value, max, label }: ProgressBarProps) {
  const safeMax = Math.max(max, 1);
  const clampedValue = Math.min(safeMax, Math.max(0, value));
  const percentage = (clampedValue / safeMax) * 100;
  const percentageLabel = `${Math.round(percentage)}%`;

  return (
    <div className="progress-bar-group">
      <div className="progress-label-row">
        <span>{label}</span>
        <strong>{value} / {max} · {percentageLabel}</strong>
      </div>
      <div className="progress-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={safeMax} aria-valuenow={clampedValue}>
        <div className="progress-bar" style={{ width: `${percentage}%` }}><span>{percentageLabel}</span></div>
      </div>
    </div>
  );
}
