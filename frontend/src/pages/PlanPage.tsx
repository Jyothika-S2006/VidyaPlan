import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import KpiTile from '../components/KpiTile'
import ProvenanceBadge from '../components/ProvenanceBadge'
import RobustnessBar from '../components/RobustnessBar'
import AgentTrace from '../components/AgentTrace'
import { api } from '../api/client'
import type { StressResult, VoiEntry, ScenarioCompare, BaselineRow } from '../api/types'

function formatRs(n: number) {
  if (n >= 10000000) return `Rs. ${(n / 10000000).toFixed(1)}Cr`
  if (n >= 100000)   return `Rs. ${(n / 100000).toFixed(1)}L`
  return `Rs. ${n.toLocaleString('en-IN')}`
}

// ── Shared idle / loading panel helpers ─────────────────────────────────────
function PanelIdle({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="panel-idle">
      <div className="panel-idle-icon">{icon}</div>
      <span>{text}</span>
    </div>
  )
}

function PanelLoading({ text }: { text: string }) {
  return (
    <div className="panel-loading">
      <div className="spinner" />
      <span>{text}</span>
    </div>
  )
}

// ── Provenance legend ────────────────────────────────────────────────────────
function ProvenanceLegend() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-5)',
      flexWrap: 'wrap',
      padding: 'var(--space-3) var(--space-4)',
      background: 'var(--bg-soft)',
      borderRadius: 'var(--radius-sm)',
      border: '1px solid var(--border-light)',
      fontSize: 'var(--font-xs)',
      color: 'var(--text-secondary)',
    }}>
      <span style={{ fontWeight: 700, color: 'var(--text-primary)', marginRight: 'var(--space-1)' }}>Provenance:</span>
      <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <ProvenanceBadge type="official" year="2017-18" />
        <span>Dataset-derived fact (official Karnataka Schools census)</span>
      </span>
      <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <ProvenanceBadge type="simulated" />
        <span>Hypothetical estimate — verify before acting</span>
      </span>
    </div>
  )
}

// ── Facility pill ────────────────────────────────────────────────────────────
function FacilityPill({ facility }: { facility: string }) {
  return (
    <span style={{
      background: 'var(--color-peach-light)',
      color: 'var(--text-secondary)',
      padding: '2px 8px',
      borderRadius: 999,
      fontSize: 'var(--font-sm)',
      fontWeight: 600,
      textTransform: 'capitalize' as const,
    }}>{facility}</span>
  )
}

export default function PlanPage() {
  const [plan,              setPlan]              = useState<any>(null)
  const [stress,            setStress]            = useState<StressResult | null>(null)
  const [stressLoading,     setStressLoading]     = useState(false)
  const [voi,               setVoi]               = useState<VoiEntry[] | null>(null)
  const [voiLoading,        setVoiLoading]        = useState(false)
  const [scenarios,         setScenarios]         = useState<ScenarioCompare | null>(null)
  const [scenariosLoading,  setScenariosLoading]  = useState(false)
  const [baselines,         setBaselines]         = useState<BaselineRow[] | null>(null)
  const [baselinesLoading,  setBaselinesLoading]  = useState(false)
  const [copilotInput,      setCopilotInput]      = useState('')
  const [copilotResult,     setCopilotResult]     = useState<any>(null)
  const [copilotLoading,    setCopilotLoading]    = useState(false)
  const [traceOpen,         setTraceOpen]         = useState(false)
  const [traceSteps,        setTraceSteps]        = useState<any[]>([])
  const [traceLoading,      setTraceLoading]      = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const stored = sessionStorage.getItem('lastPlanResult')
    if (stored) setPlan(JSON.parse(stored))
  }, [])

  const handleStress = async () => {
    if (!plan) return
    setStressLoading(true)
    try {
      const r = await api.runStress({ budget: plan.budget, n_scenarios: 100, seed: 42 })
      setStress(r)
    } catch (e: any) { alert(e.message) }
    setStressLoading(false)
  }

  const handleVerifyFirst = async () => {
    if (!plan?.plan_id) return
    setVoiLoading(true)
    try {
      const r = await api.getVerifyFirst(plan.plan_id)
      setVoi(r)
    } catch (e: any) { alert(e.message) }
    setVoiLoading(false)
  }

  const handleScenarios = async () => {
    if (!plan) return
    setScenariosLoading(true)
    try {
      const r = await api.compareScenarios({ budget: plan.budget })
      setScenarios(r)
    } catch (e: any) { alert(e.message) }
    setScenariosLoading(false)
  }

  const handleBaselines = async () => {
    if (!plan?.plan_id) return
    setBaselinesLoading(true)
    try {
      const r = await api.getBaselines(plan.plan_id)
      setBaselines(r)
    } catch (e: any) { alert(e.message) }
    setBaselinesLoading(false)
  }

  const handleCopilot = async () => {
    if (!plan || !copilotInput.trim()) return
    setCopilotLoading(true)
    try {
      const r = await api.copilot({ instruction: copilotInput, budget: plan.budget })
      setCopilotResult(r)
    } catch (e: any) { alert(e.message) }
    setCopilotLoading(false)
  }

  const handleExportMemo = () => {
    if (!plan?.plan_id) return
    window.open(`http://localhost:8000/api/plan/${plan.plan_id}/memo.pdf`, '_blank')
  }

  if (!plan) return (
    <div className="empty-state fade-in">
      <div className="empty-state-icon">📋</div>
      <h3 style={{ marginBottom: 'var(--space-2)' }}>No Plan Yet</h3>
      <p>Go to the Budget step to run the solver first.</p>
      <button className="btn btn-primary" style={{ marginTop: 'var(--space-5)' }} onClick={() => navigate('/budget')}>
        Go to Budget →
      </button>
    </div>
  )

  const kpis      = plan.kpis ?? {}
  const selected  = plan.selected ?? []
  const deferred  = plan.deferred ?? []
  const blocked   = plan.blocked ?? []
  const budgetPct = plan.budget > 0 ? Math.round((plan.budget_used / plan.budget) * 100) : 0

  return (
    <div className="page fade-in">
      <AgentTrace steps={traceSteps} open={traceOpen} onClose={() => setTraceOpen(false)} loading={traceLoading} />

      {/* Page header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Recommended Plan</h2>
          <div className="page-subtitle">
            Budget: {formatRs(plan.budget)} · {selected.length} interventions funded
            <ProvenanceBadge type="simulated" />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={() => {
            setTraceOpen(true)
            if (plan?.plan_id && traceSteps.length === 0) {
              setTraceLoading(true)
              const poll = () => api.getPlanTrace(plan.plan_id).then(steps => {
                if (steps.length > 0) { setTraceSteps(steps); setTraceLoading(false) }
                else setTimeout(poll, 3000)
              }).catch(() => setTraceLoading(false))
              poll()
            }
          }} style={{ fontSize: 'var(--font-sm)' }}>Agent Trace</button>
          <button className="btn btn-secondary" onClick={handleExportMemo}           style={{ fontSize: 'var(--font-sm)' }}>Export Memo PDF</button>
          <button className="btn btn-primary"   onClick={() => navigate('/review')}  style={{ fontSize: 'var(--font-sm)' }}>Review →</button>
        </div>
      </div>

      {/* ── Change 1: Provenance legend ─────────────────────────── */}
      <ProvenanceLegend />

      {/* KPIs — costs are SIMULATED, counts from dataset are OFFICIAL */}
      <div className="grid-kpi-wide">
        <KpiTile label="Budget Used"      value={formatRs(plan.budget_used)}     provenance="simulated" accent="var(--color-primary)"    sublabel={`${budgetPct}% of total`} />
        <KpiTile label="Funded"           value={kpis.interventions_funded ?? 0} provenance="simulated" accent="var(--color-sage)"        />
        <KpiTile label="Schools Improved" value={kpis.schools_improved ?? 0}     provenance="official"  accent="var(--color-dusty-pink)" />
        <KpiTile label="Deferred"         value={kpis.deferred_count ?? 0}       provenance="simulated" accent="var(--color-yellow)"      />
      </div>

      {/* Budget bar */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
          <span style={{ fontWeight: 600 }}>Budget Utilisation</span>
          <span style={{ color: 'var(--text-muted)', fontSize: 'var(--font-sm)' }}>
            {formatRs(plan.budget_used)} / {formatRs(plan.budget)}
            <ProvenanceBadge type="simulated" />
          </span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill progress-purple" style={{ width: `${budgetPct}%` }} />
        </div>
        <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-1)' }}>
          {formatRs(plan.budget_remaining)} remaining
        </div>
      </div>

      {/* Funded interventions — gap status is OFFICIAL, cost is SIMULATED */}
      <div className="card">
        <div className="section-header">
          <h3 className="section-title">Funded Interventions ({selected.length})</h3>
          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>Gap status: OFFICIAL · Cost: SIMULATED</span>
        </div>
        {selected.length === 0
          ? <PanelIdle icon="📭" text="No interventions funded at this budget level." />
          : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>School</th>
                    <th>Intervention <ProvenanceBadge type="official" /></th>
                    <th>Cost <ProvenanceBadge type="simulated" /></th>
                    <th>Priority</th>
                    <th>Robustness <ProvenanceBadge type="simulated" /></th>
                  </tr>
                </thead>
                <tbody>
                  {selected.map((item: any, i: number) => {
                    const stressDetail = stress?.details?.find(d => d.item_id === item.id)
                    return (
                      <tr key={i}>
                        <td style={{ fontWeight: 500 }}>{item.school_name}</td>
                        <td><FacilityPill facility={item.facility} /></td>
                        <td>{formatRs(item.cost)}</td>
                        <td>{item.priority?.toFixed(2)}</td>
                        <td>
                          {stressDetail
                            ? <RobustnessBar value={stressDetail.robustness} />
                            : <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>Run stress-test ↓</span>
                          }
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )
        }
      </div>

      {/* Prerequisite-blocked */}
      {blocked.length > 0 && (
        <div className="card card-warn">
          <div className="section-header">
            <h3 className="section-title">Prerequisite-Blocked ({blocked.length})</h3>
            <ProvenanceBadge type="official" />
          </div>
          <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
            Computer interventions cannot be funded because electricity status is unverified (OFFICIAL dataset). See Verify-First Queue below.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {blocked.map((b: any, i: number) => (
              <div key={i} style={{
                padding: 'var(--space-2) var(--space-3)',
                background: 'var(--color-yellow-light)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--font-sm)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontWeight: 500 }}>{b.school_name}</span>
                <code style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>BLOCKED_PREREQ_UNVERIFIED</code>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Stress-Test ────────────────────────────────────────────────────── */}
      <div className="card">
        <div className="section-header">
          <div>
            <h3 className="section-title" style={{ marginBottom: 2 }}>
              Plan Stress-Test <ProvenanceBadge type="simulated" />
            </h3>
            <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', margin: 0 }}>
              Monte Carlo robustness: how many scenarios still fund each pick?
            </p>
          </div>
          <button className="btn btn-primary" onClick={handleStress} disabled={stressLoading} style={{ flexShrink: 0 }}>
            {stressLoading ? <><div className="spinner" /> Running…</> : 'Run Stress-Test (100)'}
          </button>
        </div>

        {/* Change 3: idle / loading / result states */}
        {!stress && !stressLoading && (
          <PanelIdle icon="🎲" text="Click Run Stress-Test to compute Monte Carlo robustness across 100 cost scenarios." />
        )}
        {stressLoading && <PanelLoading text="Running 100 cost scenarios…" />}
        {stress && !stressLoading && (
          <div>
            <div className="stat-row" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="stat-item">
                <span className="stat-label">Scenarios</span>
                <span className="stat-value">{stress.n_scenarios}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Seed</span>
                <span className="stat-value">{stress.seed}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Expected Regret</span>
                <span className="stat-value">{stress.expected_regret_pct.toFixed(1)}%</span>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {stress.details.map((d, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <code style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', width: 160, flexShrink: 0 }}>{d.item_id}</code>
                  <div style={{ flex: 1 }}><RobustnessBar value={d.robustness} /></div>
                  {d.fragile && (
                    <span style={{ fontSize: 'var(--font-xs)', background: 'var(--status-danger)', color: '#fff', padding: '1px 6px', borderRadius: 999 }}>
                      fragile
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Verify-First Queue ──────────────────────────────────────────────── */}
      <div className="card">
        <div className="section-header">
          <div>
            <h3 className="section-title" style={{ marginBottom: 2 }}>
              Verify-First Queue <ProvenanceBadge type="simulated" />
            </h3>
            <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', margin: 0 }}>
              Which field verifications would most improve this plan? (VOI based on OFFICIAL dataset gaps)
            </p>
          </div>
          <button className="btn btn-secondary" onClick={handleVerifyFirst} disabled={voiLoading || !plan.plan_id} style={{ flexShrink: 0 }}>
            {voiLoading ? 'Loading…' : 'Compute VOI'}
          </button>
        </div>

        {!voi && !voiLoading && (
          <PanelIdle icon="🔍" text="Click Compute VOI to see which MISSING facility records most affect the plan." />
        )}
        {voiLoading && <PanelLoading text="Computing Value of Information…" />}
        {voi && !voiLoading && voi.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-sm)' }}>No MISSING fields found that would change the plan.</p>
        )}
        {voi && !voiLoading && voi.length > 0 && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>School <ProvenanceBadge type="official" /></th>
                  <th>Facility <ProvenanceBadge type="official" /></th>
                  <th>P(gap) <ProvenanceBadge type="simulated" /></th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {voi.map((e, i) => (
                  <tr key={i}>
                    <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                    <td style={{ fontWeight: 500 }}>{e.school_name}</td>
                    <td style={{ textTransform: 'capitalize' }}>{e.facility}</td>
                    <td>{(e.p_gap * 100).toFixed(0)}%</td>
                    <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>{e.action_text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Scenario Compare ────────────────────────────────────────────────── */}
      <div className="card">
        <div className="section-header">
          <div>
            <h3 className="section-title" style={{ marginBottom: 2 }}>
              Scenario Compare <ProvenanceBadge type="simulated" />
            </h3>
            <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', margin: 0 }}>
              B, -30%, +30% side by side with gained/lost items
            </p>
          </div>
          <button className="btn btn-secondary" onClick={handleScenarios} disabled={scenariosLoading} style={{ flexShrink: 0 }}>
            {scenariosLoading ? 'Running…' : 'Compare Scenarios'}
          </button>
        </div>

        {!scenarios && !scenariosLoading && (
          <PanelIdle icon="📊" text="Click Compare Scenarios to see how the plan changes at -30% and +30% budget." />
        )}
        {scenariosLoading && <PanelLoading text="Running budget scenarios…" />}
        {scenarios && !scenariosLoading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)' }}>
              {[scenarios.low, scenarios.base, scenarios.high].map((s, i) => (
                <div key={i} style={{
                  padding: 'var(--space-4)',
                  background: i === 1 ? 'var(--color-primary-light)' : 'var(--bg-soft)',
                  borderRadius: 'var(--radius-sm)',
                  border: i === 1 ? '2px solid var(--color-primary)' : '1px solid var(--border-light)',
                }}>
                  <div style={{ fontWeight: 700, marginBottom: 'var(--space-2)', fontSize: 'var(--font-sm)', color: i === 1 ? 'var(--color-primary-dark)' : 'var(--text-secondary)' }}>
                    {(s as any).label ?? (i === 0 ? 'Low (-30%)' : i === 1 ? 'Base (B)' : 'High (+30%)')}
                  </div>
                  <div style={{ fontSize: 'var(--font-xl)', fontWeight: 700 }}>{s.funded}</div>
                  <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>interventions · {formatRs(s.budget)}</div>
                </div>
              ))}
            </div>
            {scenarios.gained_in_high.length > 0 && (
              <div>
                <span style={{ fontSize: 'var(--font-sm)', color: 'var(--status-success)', fontWeight: 600 }}>+{scenarios.gained_in_high.length} gained at +30%:</span>
                {' '}<span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>{scenarios.gained_in_high.map(item => `${item.school_name} (${item.facility})`).join(', ')}</span>
              </div>
            )}
            {scenarios.lost_in_low.length > 0 && (
              <div>
                <span style={{ fontSize: 'var(--font-sm)', color: 'var(--status-danger)', fontWeight: 600 }}>-{scenarios.lost_in_low.length} lost at -30%:</span>
                {' '}<span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>{scenarios.lost_in_low.map(item => `${item.school_name} (${item.facility})`).join(', ')}</span>
              </div>
            )}
            {scenarios.marginal && (
              <div style={{ padding: 'var(--space-3) var(--space-4)', background: 'var(--color-yellow-light)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-sm)' }}>
                <strong>Next Rs. 10L funds:</strong> {scenarios.marginal.delta_interventions} more interventions
                {scenarios.marginal.new_items.length > 0 && (
                  <div style={{ marginTop: 4, color: 'var(--text-muted)' }}>
                    {scenarios.marginal.new_items.map(item => `${item.school_name} (${item.facility})`).join(', ')}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Baseline Comparison ─────────────────────────────────────────────── */}
      <div className="card">
        <div className="section-header">
          <div>
            <h3 className="section-title" style={{ marginBottom: 2 }}>
              Baseline Comparison <ProvenanceBadge type="simulated" />
            </h3>
            <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', margin: 0 }}>
              CP-SAT optimiser vs greedy vs random (100 plans avg)
            </p>
          </div>
          <button className="btn btn-secondary" onClick={handleBaselines} disabled={baselinesLoading || !plan.plan_id} style={{ flexShrink: 0 }}>
            {baselinesLoading ? 'Running…' : 'Run Baselines'}
          </button>
        </div>

        {!baselines && !baselinesLoading && (
          <PanelIdle icon="📐" text="Click Run Baselines to compare CP-SAT against greedy and random strategies." />
        )}
        {baselinesLoading && <PanelLoading text="Running greedy and random baselines (100 plans)…" />}
        {baselines && !baselinesLoading && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr><th>Method</th><th>Objective</th><th>Funded</th><th>Schools</th><th>Budget Used</th><th>% vs Optimiser</th></tr>
              </thead>
              <tbody>
                {baselines.map((b, i) => (
                  <tr key={i} style={{ background: b.method === 'optimiser' ? 'rgba(198,180,220,0.15)' : undefined }}>
                    <td style={{ fontWeight: b.method === 'optimiser' ? 700 : 400, textTransform: 'capitalize' }}>
                      {b.method.replace('_', ' ')}
                    </td>
                    <td>{typeof b.objective === 'number' ? b.objective.toFixed(2) : b.objective}</td>
                    <td>{typeof b.interventions_funded === 'number' ? Math.round(b.interventions_funded) : b.interventions_funded}</td>
                    <td>{typeof b.schools_improved === 'number' ? Math.round(b.schools_improved) : b.schools_improved}</td>
                    <td>{formatRs(b.budget_used)}</td>
                    <td style={{ fontWeight: 600, color: b.pct_vs_optimiser === 100 ? 'var(--status-success)' : 'var(--text-secondary)' }}>
                      {b.pct_vs_optimiser?.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Scenario Copilot ────────────────────────────────────────────────── */}
      <div className="card">
        <div className="section-header" style={{ marginBottom: 'var(--space-2)' }}>
          <h3 className="section-title">Scenario Copilot <ProvenanceBadge type="simulated" /></h3>
        </div>
        <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
          Ask a natural-language question. The AI converts it to a tool call, the solver runs it.
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
          <input
            className="form-input"
            placeholder='e.g. "what if budget drops 30%" or "set budget to 30 lakh"'
            value={copilotInput}
            onChange={e => setCopilotInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleCopilot() }}
            style={{ flex: 1 }}
          />
          <button className="btn btn-primary" onClick={handleCopilot} disabled={copilotLoading || !copilotInput.trim()} style={{ flexShrink: 0 }}>
            {copilotLoading ? <><div className="spinner" /> Running…</> : 'Ask'}
          </button>
        </div>
        {!copilotResult && !copilotLoading && (
          <PanelIdle icon="💬" text='Type a question and press Ask — e.g. "what if budget drops 30%"' />
        )}
        {copilotLoading && <PanelLoading text="IBM Granite is parsing your instruction…" />}
        {copilotResult && !copilotLoading && (
          <div style={{ padding: 'var(--space-4)', background: 'var(--bg-soft)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-sm)' }}>
            <div style={{ marginBottom: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600 }}>Parsed tool call:</span>
              <code style={{ fontSize: 'var(--font-xs)' }}>{JSON.stringify(copilotResult.tool_call)}</code>
              <span style={{
                fontSize: 'var(--font-xs)',
                background: copilotResult.source === 'granite' ? 'var(--color-primary-light)' : 'var(--bg-surface-2)',
                color: copilotResult.source === 'granite' ? 'var(--color-primary-dark)' : 'var(--text-muted)',
                padding: '1px 6px',
                borderRadius: 999,
              }}>{copilotResult.source}</span>
            </div>
            {copilotResult.status === 'failed'
              ? <p style={{ color: 'var(--status-danger)', margin: 0 }}>{copilotResult.message}</p>
              : <pre style={{ fontSize: 'var(--font-xs)', overflowX: 'auto', whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', margin: 0 }}>{JSON.stringify(copilotResult.result, null, 2)}</pre>
            }
          </div>
        )}
      </div>

      {/* Deferred */}
      {deferred.length > 0 && (
        <div className="card">
          <div className="section-header">
            <h3 className="section-title">Deferred Items ({deferred.length})</h3>
            <ProvenanceBadge type="simulated" />
          </div>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>School</th><th>Intervention</th><th>Cost <ProvenanceBadge type="simulated" /></th><th>Reason</th></tr></thead>
              <tbody>
                {deferred.map((item: any, i: number) => (
                  <tr key={i}>
                    <td>{item.school_name}</td>
                    <td style={{ textTransform: 'capitalize' }}>{item.facility}</td>
                    <td>{formatRs(item.cost)}</td>
                    <td>
                      <code style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                        {item.reason_code ?? 'OUT_OF_BUDGET'}
                      </code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
