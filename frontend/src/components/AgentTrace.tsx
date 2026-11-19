interface TraceStep {
  agent: string
  tool_called: string | null
  latency_ms: number
  source: string
  output_summary: string
}

interface Props {
  steps: TraceStep[]
  open: boolean
  onClose: () => void
  loading?: boolean
}

export default function AgentTrace({ steps, open, onClose, loading }: Props) {
  if (!open) return null

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', justifyContent: 'flex-end' }}>
      <div onClick={onClose} style={{ position: 'absolute', inset: 0, background: 'rgba(54,44,42,0.3)' }} />
      <div style={{ position: 'relative', width: 420, background: 'var(--bg-surface)', boxShadow: 'var(--shadow-lg)', display: 'flex', flexDirection: 'column', zIndex: 1, overflowY: 'auto' }}>
        <div style={{ padding: 'var(--space-6)', borderBottom: '1px solid var(--border-main)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
          <h3 style={{ margin: 0 }}>Agent Trace</h3>
          <button className="btn btn-secondary" onClick={onClose} style={{ padding: 'var(--space-1) var(--space-3)' }}>✕</button>
        </div>

        <div style={{ padding: 'var(--space-5)', flex: 1 }}>
          {loading ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-sm)' }}>⏳ Agent pipeline is running… check back in a moment.</p>
          ) : steps.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-sm)' }}>No agent steps recorded yet. Run a plan to see the agent pipeline.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {steps.map((step, i) => (
                <div key={i} style={{ padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-soft)', borderRadius: 'var(--radius-sm)', borderLeft: `3px solid ${step.source === 'granite' ? 'var(--color-primary)' : 'var(--border-main)'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
                    <span style={{ fontWeight: 600, fontSize: 'var(--font-sm)', textTransform: 'capitalize' }}>{step.agent.replace('_', ' ')}</span>
                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>{step.latency_ms}ms</span>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                    <span style={{ fontSize: 'var(--font-xs)', background: step.source === 'granite' ? 'var(--color-primary-light)' : 'var(--bg-surface-2)', color: step.source === 'granite' ? 'var(--color-primary-dark)' : 'var(--text-muted)', padding: '1px 6px', borderRadius: 999 }}>
                      {step.source}
                    </span>
                    {step.tool_called && (
                      <span style={{ fontSize: 'var(--font-xs)', background: 'var(--color-peach-light)', color: '#5a3a10', padding: '1px 6px', borderRadius: 999 }}>
                        {step.tool_called}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', margin: 0 }}>{step.output_summary}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
