import ProvenanceBadge from './ProvenanceBadge'

interface KpiTileProps {
  label: string
  value: string | number
  provenance?: 'official' | 'simulated'
  accent?: string
  sublabel?: string
}

export default function KpiTile({ label, value, provenance, accent, sublabel }: KpiTileProps) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-main)',
      borderRadius: 'var(--radius-md)',
      padding: 'var(--space-5) var(--space-6)',
      boxShadow: 'var(--shadow-sm)',
      borderTop: accent ? `3px solid ${accent}` : '3px solid var(--color-primary)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-2)',
    }}>
      <div style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: 'var(--font-3xl)', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.1 }}>
        {value}
      </div>
      {sublabel && (
        <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>{sublabel}</div>
      )}
      {provenance && <ProvenanceBadge type={provenance} year={provenance === 'official' ? '2017-18' : undefined} />}
    </div>
  )
}
