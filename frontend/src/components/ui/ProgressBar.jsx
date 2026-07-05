export default function ProgressBar({ value, max = 100, color: colorOverride, className = '' }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  const color = colorOverride
    ? colorOverride
    : pct >= 70
    ? 'var(--c-success)'
    : pct >= 40
    ? 'var(--c-warning)'
    : 'var(--c-danger)'

  return (
    <div
      className={`h-3 w-full overflow-hidden rounded-full neu-pressed-sm ${className}`}
      style={{ backgroundColor: 'var(--c-surface)' }}
    >
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  )
}
