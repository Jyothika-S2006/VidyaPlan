import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import ProvenanceBadge from '../components/ProvenanceBadge'

const DEFAULT_BUDGET = 5000000

function formatRs(amount: number): string {
  if (amount >= 10000000) return `Rs. ${(amount / 10000000).toFixed(1)}Cr`
  if (amount >= 100000)   return `Rs. ${(amount / 100000).toFixed(1)}L`
  return `Rs. ${amount.toLocaleString('en-IN')}`
}

const COST_ASSUMPTIONS = [
  { label: 'Library',     cost: 'Rs. 1,50,000', accent: 'var(--color-peach)',       dot: 'var(--color-peach)' },
  { label: 'Electricity', cost: 'Rs. 2,50,000', accent: 'var(--color-dusty-pink)', dot: 'var(--color-dusty-pink)' },
  { label: 'Computers',   cost: 'Rs. 4,00,000', accent: 'var(--color-sage)',        dot: 'var(--color-sage)' },
]

export default function BudgetPage() {
  const [budget, setBudget]   = useState(DEFAULT_BUDGET)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)
  const navigate = useNavigate()

  const handleRunPlan = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.runPlan({ budget, cohort_only: true })
      sessionStorage.setItem('lastPlanId', String(result.plan_id))
      sessionStorage.setItem('lastPlanResult', JSON.stringify(result))
      navigate('/plan')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const presets = [
    { label: 'Conservative (Rs. 25L)', value: 2500000 },
    { label: 'Base (Rs. 50L)',          value: 5000000 },
    { label: '+30% (Rs. 65L)',          value: 6500000 },
  ]

  const pct = Math.round((budget / 20000000) * 100)

  return (
    <div className="page fade-in" style={{ maxWidth: 740 }}>

      {/* Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Set Budget</h2>
          <div className="page-subtitle">
            Configure the total allocation for infrastructure interventions.
            <ProvenanceBadge type="simulated" />
          </div>
        </div>
      </div>

      {/* Budget configurator */}
      <div className="card">
        <div className="section-header">
          <h3 className="section-title">Total Budget (INR)</h3>
          <div style={{
            fontSize: 'var(--font-2xl)',
            fontWeight: 800,
            color: 'var(--color-primary-dark)',
            letterSpacing: '-0.03em',
          }}>
            {formatRs(budget)}
          </div>
        </div>

        {/* Slider + track labels */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <input
            type="range"
            min={500000}
            max={20000000}
            step={100000}
            value={budget}
            onChange={e => setBudget(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--color-primary-dark)', height: 6 }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-1)' }}>
            <span>Rs. 5L</span>
            <span style={{ color: 'var(--color-primary-dark)', fontWeight: 600 }}>{pct}% of max</span>
            <span>Rs. 2Cr</span>
          </div>
        </div>

        {/* Numeric input */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div style={{ flex: 1 }}>
            <label className="form-label">Enter exact amount (Rs.)</label>
            <input
              className="form-input"
              type="number"
              value={budget}
              min={500000}
              max={20000000}
              step={100000}
              onChange={e => setBudget(Number(e.target.value))}
            />
          </div>
        </div>

        {/* Presets */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <label className="form-label">Quick Presets</label>
          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginTop: 'var(--space-2)' }}>
            {presets.map(p => (
              <button
                key={p.value}
                className={`btn ${budget === p.value ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setBudget(p.value)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}

        <button
          className="btn btn-primary"
          onClick={handleRunPlan}
          disabled={loading}
          style={{ width: '100%', justifyContent: 'center', padding: 'var(--space-3) var(--space-6)', fontSize: 'var(--font-md)' }}
        >
          {loading
            ? <><div className="spinner" style={{ borderTopColor: 'var(--color-primary-dark)' }} /> Running Solver…</>
            : '▶  Run Plan'
          }
        </button>
      </div>

      {/* Cost assumptions card */}
      <div className="card card-warn">
        <div className="section-header">
          <h4 className="section-title" style={{ fontSize: 'var(--font-base)' }}>
            Intervention Cost Assumptions
          </h4>
          <ProvenanceBadge type="simulated" />
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-6)', flexWrap: 'wrap' }}>
          {COST_ASSUMPTIONS.map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: item.dot, flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{item.label}</div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 'var(--font-md)' }}>{item.cost}</div>
              </div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-4)', marginBottom: 0 }}>
          All costs are hypothetical and labelled SIMULATED. Editable in Settings → Config.
        </p>
      </div>
    </div>
  )
}
