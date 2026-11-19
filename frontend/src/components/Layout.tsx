import React from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import DataAsOfBanner from './DataAsOfBanner'
import SettingsDrawer from './SettingsDrawer'

const STEPS = [
  { path: '/data',   label: 'Data',   desc: 'Explore schools',   num: '1' },
  { path: '/budget', label: 'Budget', desc: 'Set allocation',    num: '2' },
  { path: '/plan',   label: 'Plan',   desc: 'Optimise & analyse',num: '3' },
  { path: '/review', label: 'Review', desc: 'Human gate',        num: '4' },
]

export default function Layout() {
  const [settingsOpen, setSettingsOpen] = React.useState(false)
  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      <Sidebar onOpenSettings={() => setSettingsOpen(true)} />
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, background: 'var(--bg-base)' }}>
        <DataAsOfBanner />
        <main style={{ flex: 1, padding: 'var(--space-8) var(--space-10)', overflowY: 'auto', maxWidth: 1200, width: '100%', margin: '0 auto', boxSizing: 'border-box' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function Sidebar({ onOpenSettings }: { onOpenSettings: () => void }) {
  const location = useLocation()

  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      background: 'var(--sidebar-bg)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      boxShadow: '2px 0 12px rgba(90,60,120,0.12)',
      position: 'relative',
      zIndex: 10,
    }}>
      {/* Brand */}
      <div style={{
        padding: 'var(--space-6) var(--space-5) var(--space-5)',
        borderBottom: '1px solid rgba(90,60,120,0.15)',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
          marginBottom: 'var(--space-1)',
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: 'var(--radius-sm)',
            background: 'var(--color-primary-dark)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 'var(--font-md)', fontWeight: 800,
            flexShrink: 0,
          }}>V</div>
          <div style={{ fontSize: 'var(--font-lg)', fontWeight: 800, color: 'var(--color-primary-dark)', letterSpacing: '-0.03em' }}>
            VidyaPlan
          </div>
        </div>
        <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', paddingLeft: 40 }}>
          School Infra Planner
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: 'var(--space-4) var(--space-3)' }}>
        <div style={{
          fontSize: 'var(--font-xs)', fontWeight: 700,
          color: 'var(--color-primary-dark)', letterSpacing: '0.08em',
          textTransform: 'uppercase', padding: '0 var(--space-2)',
          marginBottom: 'var(--space-3)', opacity: 0.7,
        }}>
          Workflow
        </div>

        {STEPS.map(step => {
          const isActive = location.pathname === step.path
          return (
            <NavLink
              key={step.path}
              to={step.path}
              style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
                padding: 'var(--space-2) var(--space-3)',
                borderRadius: 'var(--radius-sm)',
                marginBottom: 'var(--space-1)',
                color: isActive ? 'var(--sidebar-active-text)' : 'var(--text-secondary)',
                background: isActive ? 'var(--sidebar-active-bg)' : 'transparent',
                fontWeight: isActive ? 600 : 400,
                fontSize: 'var(--font-sm)',
                textDecoration: 'none',
                transition: 'background var(--transition-fast)',
                borderLeft: isActive ? '3px solid var(--color-primary-dark)' : '3px solid transparent',
              }}
              onMouseEnter={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'var(--sidebar-hover-bg)' }}
              onMouseLeave={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
            >
              <div style={{
                width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
                background: isActive ? 'var(--color-primary-dark)' : 'rgba(90,60,120,0.18)',
                color: isActive ? '#fff' : 'var(--color-primary-dark)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 'var(--font-xs)', fontWeight: 700,
              }}>
                {step.num}
              </div>
              <div>
                <div style={{ lineHeight: 1.2 }}>{step.label}</div>
                <div style={{ fontSize: 'var(--font-xs)', opacity: 0.65, lineHeight: 1 }}>{step.desc}</div>
              </div>
            </NavLink>
          )
        })}
      </nav>

      {/* Settings */}
      <div style={{ padding: 'var(--space-3)' }}>
        <button
          className="btn btn-secondary"
          onClick={onOpenSettings}
          style={{ width: '100%', justifyContent: 'center', fontSize: 'var(--font-sm)' }}
        >
          ⚙ Settings
        </button>
      </div>

      {/* API status */}
      <div style={{ padding: 'var(--space-4) var(--space-5)', borderTop: '1px solid rgba(90,60,120,0.15)' }}>
        <ApiStatusChip />
      </div>
    </aside>
  )
}

function ApiStatusChip() {
  const [status, setStatus] = React.useState<'checking' | 'ok' | 'error'>('checking')
  React.useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(r => r.json())
      .then(d => setStatus(d.status === 'ok' ? 'ok' : 'error'))
      .catch(() => setStatus('error'))
  }, [])

  const color  = status === 'ok' ? 'var(--status-success)' : status === 'error' ? 'var(--status-danger)' : 'var(--status-warning)'
  const label  = status === 'ok' ? 'API Online' : status === 'error' ? 'API Offline' : 'Checking…'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
      <div style={{ width: 7, height: 7, borderRadius: '50%', background: color, flexShrink: 0 }} />
      {label}
    </div>
  )
}
