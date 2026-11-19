export default function DataAsOfBanner() {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-main)',
      padding: 'var(--space-2) var(--space-8)',
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      fontSize: 'var(--font-xs)',
      color: 'var(--text-muted)',
      flexShrink: 0,
    }}>
      <span style={{
        background: 'var(--color-sage)',
        color: '#1a3a1f',
        padding: '2px var(--space-2)',
        borderRadius: '999px',
        fontSize: 'var(--font-xs)',
        fontWeight: 700,
        letterSpacing: '0.05em',
        flexShrink: 0,
      }}>
        OFFICIAL
      </span>
      <span style={{ color: 'var(--text-secondary)' }}>
        Karnataka Schools dataset · <strong>2017-18</strong> · Verify all recommendations before acting.
      </span>
      <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: 'var(--font-xs)' }}>
        Provenance-tracked · IBM Granite AI
      </span>
    </div>
  )
}
