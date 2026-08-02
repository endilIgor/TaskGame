interface ProgressBarProps {
  value: number;
  max: number;
  label: string;
}

export function ProgressBar({ value, max, label }: ProgressBarProps) {
  const safeMax = Math.max(max, 1);
  const percentage = Math.min(100, Math.max(0, (value / safeMax) * 100));

  return (
    <div className="progress-bar-group">
      <div className="progress-label-row">
        <span>{label}</span>
        <strong>{value} / {max}</strong>
      </div>
      <div className="progress-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={safeMax} aria-valuenow={Math.max(0, value)}>
        <div className="progress-bar" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}
