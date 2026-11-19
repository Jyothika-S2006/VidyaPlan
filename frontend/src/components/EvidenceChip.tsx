type EvidenceState = 'CONFIRMED_GAP' | 'CONFIRMED_OK' | 'MISSING' | 'UNRELIABLE'

const CONFIG: Record<EvidenceState, { label: string; className: string }> = {
  CONFIRMED_GAP:  { label: 'Gap',        className: 'badge badge-confirmed-gap' },
  CONFIRMED_OK:   { label: 'OK',         className: 'badge badge-confirmed-ok'  },
  MISSING:        { label: 'Missing',    className: 'badge badge-missing'       },
  UNRELIABLE:     { label: 'Unreliable', className: 'badge badge-unreliable'    },
}

export default function EvidenceChip({ state }: { state: string }) {
  const cfg = CONFIG[state as EvidenceState] ?? { label: state, className: 'badge' }
  return <span className={cfg.className}>{cfg.label}</span>
}
