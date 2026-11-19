interface RobustnessBarProps {
  value: number  // 0 to 1
  label?: string
}

export default function RobustnessBar({ value, label }: RobustnessBarProps) {
  const pct = Math.round(value * 100)
  const band = value >= 0.85 ? 'green' : value >= 0.6 ? 'amber' : 'red'
  const bandLabel = band === 'green' ? 'Robust' : band === 'amber' ? 'Moderate' : 'Fragile'
  const color = band === 'green' ? 'var(--status-success)' : band === 'amber' ? 'var(--status-warning)' : 'var(--status-danger)'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
      {label && (
        <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>{label}</div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <div className="progress-bar" style={{ flex: 1 }}>
          <div
            className={`progress-bar-fill progress-${band}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span style={{ fontSize: 'var(--font-xs)', color, fontWeight: 700, minWidth: 36 }}>
          {pct}%
        </span>
        <span style={{
          fontSize: 'var(--font-xs)',
          fontWeight: 600,
          padding: '1px 6px',
          borderRadius: '999px',
          background: color,
          color: '#fff',
          opacity: 0.9,
        }}>
          {bandLabel}
        </span>
      </div>
    </div>
  )
}
