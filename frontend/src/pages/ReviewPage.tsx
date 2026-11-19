import { useEffect, useState } from 'react'
import { api } from '../api/client'
import ProvenanceBadge from '../components/ProvenanceBadge'

export default function ReviewPage() {
  const [plan,        setPlan]        = useState<any>(null)
  const [reviewer,    setReviewer]    = useState('')
  const [notes,       setNotes]       = useState<Record<number, string>>({})
  const [decisions,   setDecisions]   = useState<Record<number, string>>({})
  const [audit,       setAudit]       = useState<any[]>([])
  const [submitting,  setSubmitting]  = useState<number | null>(null)
  const [finalizing,  setFinalizing]  = useState(false)
  const [planStatus,  setPlanStatus]  = useState('draft')
  const [demoLoading, setDemoLoading] = useState(false)

  useEffect(() => {
    const stored = sessionStorage.getItem('lastPlanResult')
    if (stored) setPlan(JSON.parse(stored))
    api.getAudit().then(setAudit).catch(console.error)
  }, [])

  const handleLoadDemo = async () => {
    setDemoLoading(true)
    try {
      const result = await api.runPlan({ budget: 5000000 })
      sessionStorage.setItem('lastPlanResult', JSON.stringify(result))
      setPlan(result)
      setDecisions({})
      setNotes({})
      setPlanStatus('draft')
    } catch (e: any) {
      alert(`Demo load failed: ${e.message}`)
    } finally {
      setDemoLoading(false)
    }
  }

  const handleResetDemo = () => {
    sessionStorage.removeItem('lastPlanResult')
    setPlan(null)
    setDecisions({})
    setNotes({})
    setPlanStatus('draft')
    window.location.reload()
  }

  const handleReview = async (recId: number, decision: string) => {
    if (!reviewer.trim()) {
      alert('Please enter your name as reviewer.')
      return
    }
    setSubmitting(recId)
    try {
      await api.submitReview(recId, { decision, note: notes[recId], reviewer })
      setDecisions(d => ({ ...d, [recId]: decision }))
      api.getAudit().then(setAudit).catch(console.error)
    } catch (e: any) {
      alert(`Error: ${e.message}`)
    } finally {
      setSubmitting(null)
    }
  }

  const handleFinalize = async () => {
    if (!plan?.plan_id || !reviewer.trim()) {
      alert('Please enter reviewer name and ensure a plan is loaded.')
      return
    }
    setFinalizing(true)
    try {
      await api.finalizePlan(plan.plan_id, reviewer)
      setPlanStatus('final')
      api.getAudit().then(setAudit).catch(console.error)
    } catch (e: any) {
      alert(`Cannot finalize: ${e.message}`)
    } finally {
      setFinalizing(false)
    }
  }

  const selected = plan?.selected ?? []
  const allDecided = selected.length > 0 && selected.every((_: any, i: number) => decisions[i] != null)

  return (
    <div className="page fade-in">

      {/* Page header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Human Review</h2>
          <div className="page-subtitle">
            Approve or reject each funded recommendation before the plan is finalised.
            <ProvenanceBadge type="simulated" />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary"
            onClick={handleLoadDemo}
            disabled={demoLoading}
            style={{ fontSize: 'var(--font-sm)' }}
          >
            {demoLoading ? 'Loading…' : '⚡ Load Demo Preset'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleResetDemo}
            style={{ fontSize: 'var(--font-sm)', color: 'var(--status-danger)' }}
          >
            ↺ Reset Demo
          </button>
        </div>
      </div>

      {!plan ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <h3>No Plan to Review</h3>
          <p style={{ marginTop: 'var(--space-2)' }}>Run a plan first from the Budget page, or use "Load Demo Preset" above.</p>
        </div>
      ) : (
        <>
          {/* Status stepper */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)', flexWrap: 'wrap' }}>
              {['Draft', 'In Review', 'Final'].map((step, i) => {
                const idx    = planStatus === 'draft' ? 0 : planStatus === 'in_review' ? 1 : 2
                const done   = i < idx
                const active = i === idx
                return (
                  <div key={step} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    <div style={{
                      width: 30, height: 30, borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontWeight: 700, fontSize: 'var(--font-sm)',
                      background: done ? 'var(--status-success)' : active ? 'var(--color-primary)' : 'var(--border-main)',
                      color: (done || active) ? '#fff' : 'var(--text-muted)',
                      flexShrink: 0,
                      boxShadow: active ? '0 0 0 3px rgba(198,180,220,0.3)' : undefined,
                    }}>
                      {done ? '✓' : i + 1}
                    </div>
                    <span style={{ fontWeight: active ? 700 : 400, color: active ? 'var(--text-primary)' : 'var(--text-muted)', fontSize: 'var(--font-sm)' }}>
                      {step}
                    </span>
                    {i < 2 && (
                      <span style={{ color: 'var(--border-main)', fontSize: 'var(--font-lg)', marginLeft: 'var(--space-1)' }}>→</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Reviewer name */}
          <div className="card">
            <label className="form-label">Reviewer Name</label>
            <input
              className="form-input"
              placeholder="Enter your name…"
              value={reviewer}
              onChange={e => setReviewer(e.target.value)}
              style={{ maxWidth: 320, marginTop: 'var(--space-2)' }}
            />
          </div>

          {/* Recommendations */}
          <div className="card">
            <div className="section-header">
              <h3 className="section-title">Funded Recommendations ({selected.length})</h3>
              {allDecided && (
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--status-success)', fontWeight: 600 }}>✓ All reviewed</span>
              )}
            </div>
            {selected.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>No funded interventions to review.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                {selected.map((rec: any, i: number) => {
                  const decision = decisions[i]
                  return (
                    <div key={i} style={{
                      padding: 'var(--space-4)',
                      background: decision === 'approved'
                        ? 'var(--bg-success)'
                        : decision === 'rejected'
                          ? 'var(--bg-danger)'
                          : 'var(--bg-soft)',
                      borderRadius: 'var(--radius-sm)',
                      border: `1px solid ${
                        decision === 'approved'
                          ? 'var(--status-success)'
                          : decision === 'rejected'
                            ? 'var(--status-danger)'
                            : 'var(--border-light)'
                      }`,
                      transition: 'background var(--transition-base), border-color var(--transition-base)',
                    }}>
                      {/* Rec header */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-3)' }}>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rec.school_name}</div>
                          <div style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', textTransform: 'capitalize', marginTop: 2 }}>
                            <span style={{ background: 'var(--color-peach-light)', padding: '1px 8px', borderRadius: 999, fontWeight: 600, marginRight: 'var(--space-2)' }}>
                              {rec.facility}
                            </span>
                            Rs. {rec.cost?.toLocaleString('en-IN')}
                          </div>
                        </div>
                        {decision && (
                          <span style={{
                            padding: '3px 10px',
                            borderRadius: '999px',
                            fontSize: 'var(--font-xs)',
                            fontWeight: 700,
                            background: decision === 'approved' ? 'var(--status-success)' : 'var(--status-danger)',
                            color: '#fff',
                          }}>
                            {decision.toUpperCase()}
                          </span>
                        )}
                      </div>

                      {rec.explanation && (
                        <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
                          {rec.explanation}
                        </p>
                      )}

                      {!decision && (
                        <>
                          <input
                            className="form-input"
                            placeholder="Note (optional)…"
                            value={notes[i] ?? ''}
                            onChange={e => setNotes(n => ({ ...n, [i]: e.target.value }))}
                            style={{ marginBottom: 'var(--space-3)' }}
                          />
                          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                            <button
                              className="btn btn-success"
                              onClick={() => handleReview(i, 'approved')}
                              disabled={submitting === i}
                            >
                              ✓ Approve
                            </button>
                            <button
                              className="btn btn-danger"
                              onClick={() => handleReview(i, 'rejected')}
                              disabled={submitting === i}
                            >
                              ✗ Reject
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Finalize */}
          <div className="card">
            <div className="section-header">
              <div>
                <h3 className="section-title">Finalize Plan</h3>
                <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', margin: 0, marginTop: 'var(--space-1)' }}>
                  Once all recommendations are reviewed, finalize to create an immutable record.
                </p>
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleFinalize}
              disabled={!allDecided || finalizing || planStatus === 'final'}
              style={{ padding: 'var(--space-3) var(--space-6)' }}
            >
              {planStatus === 'final' ? '✓ Plan Finalized' : finalizing ? 'Finalizing…' : 'Finalize Plan'}
            </button>
          </div>

          {/* Audit timeline */}
          {audit.length > 0 && (
            <div className="card">
              <div className="section-header">
                <h3 className="section-title">Audit Timeline</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {audit.slice(0, 10).map((entry: any) => (
                  <div key={entry.id} style={{
                    display: 'flex',
                    gap: 'var(--space-3)',
                    padding: 'var(--space-3)',
                    background: 'var(--bg-soft)',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: '3px solid var(--color-primary)',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 'var(--font-sm)' }}>
                        {entry.actor}
                        <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> · {entry.action} · {entry.entity} #{entry.entity_id}</span>
                      </div>
                      <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
                        {new Date(entry.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
