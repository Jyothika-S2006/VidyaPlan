interface ProvenanceBadgeProps {
  type: 'official' | 'simulated' | 'granite' | 'template'
  year?: string
}

export default function ProvenanceBadge({ type, year }: ProvenanceBadgeProps) {
  const configs = {
    official:  { label: year ? `OFFICIAL ${year}` : 'OFFICIAL', className: 'badge badge-official' },
    simulated: { label: 'SIMULATED',             className: 'badge badge-simulated' },
    granite:   { label: 'AI · Granite',          className: 'badge badge-unreliable' },
    template:  { label: 'Template',              className: 'badge', style: { background: 'var(--bg-surface-2)', color: 'var(--text-muted)' } },
  }
  const cfg = configs[type]

  return (
    <span className={cfg.className} style={(cfg as any).style ?? undefined}>
      {cfg.label}
    </span>
  )
}
