import { useState, useEffect } from 'react'
import { api } from '../api/client'
import ProvenanceBadge from './ProvenanceBadge'

interface Props {
  open: boolean
  onClose: () => void
}

const FACILITIES = ['electricity', 'library', 'computers'] as const

export default function SettingsDrawer({ open, onClose }: Props) {
  const [costs, setCosts] = useState<Record<string, number>>({ electricity: 250000, library: 150000, computers: 400000 })
  const [weights, setWeights] = useState<Record<string, number>>({ electricity: 1.0, library: 0.8, computers: 0.9 })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (open) {
      api.getConfig().then(c => { setCosts(c.costs); setWeights(c.weights) }).catch(console.error)
    }
  }, [open])

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.updateConfig({ costs, weights })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) { console.error(e) }
    setSaving(false)
  }

  if (!open) return null

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', justifyContent: 'flex-end' }}>
      {/* Backdrop */}
      <div onClick={onClose} style={{ position: 'absolute', inset: 0, background: 'rgba(54,44,42,0.3)' }} />
      {/* Drawer */}
      <div style={{ position: 'relative', width: 360, background: 'var(--bg-surface)', boxShadow: 'var(--shadow-lg)', display: 'flex', flexDirection: 'column', zIndex: 1 }}>
        <div style={{ padding: 'var(--space-6)', borderBottom: '1px solid var(--border-main)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0 }}>Settings</h3>
            <ProvenanceBadge type="simulated" />
          </div>
          <button className="btn btn-secondary" onClick={onClose} style={{ padding: 'var(--space-1) var(--space-3)' }}>✕</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-6)' }}>
          <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-5)' }}>
            All values are SIMULATED hypothetical estimates. They are not official government figures.
          </p>

          <h4 style={{ marginBottom: 'var(--space-3)' }}>Intervention Costs (Rs.)</h4>
          {FACILITIES.map(f => (
            <div key={f} style={{ marginBottom: 'var(--space-4)' }}>
              <label className="form-label" style={{ textTransform: 'capitalize' }}>{f}</label>
              <input
                className="form-input"
                type="number"
                min={10000}
                max={10000000}
                step={10000}
                value={costs[f] ?? 0}
                onChange={e => setCosts(c => ({ ...c, [f]: Number(e.target.value) }))}
              />
            </div>
          ))}

          <h4 style={{ marginTop: 'var(--space-5)', marginBottom: 'var(--space-3)' }}>Priority Weights (0–2)</h4>
          {FACILITIES.map(f => (
            <div key={f} style={{ marginBottom: 'var(--space-4)' }}>
              <label className="form-label" style={{ textTransform: 'capitalize' }}>{f}</label>
              <input
                className="form-input"
                type="number"
                min={0.1}
                max={2.0}
                step={0.1}
                value={weights[f] ?? 1.0}
                onChange={e => setWeights(w => ({ ...w, [f]: Number(e.target.value) }))}
              />
            </div>
          ))}
        </div>

        <div style={{ padding: 'var(--space-5)', borderTop: '1px solid var(--border-main)' }}>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ width: '100%', justifyContent: 'center' }}>
            {saved ? '✓ Saved' : saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
