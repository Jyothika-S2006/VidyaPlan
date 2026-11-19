import { useEffect, useState, useMemo } from 'react'
import { api } from '../api/client'
import KpiTile from '../components/KpiTile'
import EvidenceChip from '../components/EvidenceChip'
import ProvenanceBadge from '../components/ProvenanceBadge'

type EvidenceFilter = 'ALL' | 'CONFIRMED_GAP' | 'CONFIRMED_OK' | 'MISSING' | 'UNRELIABLE'
type FacilityFilter = 'all' | 'electricity' | 'library' | 'computers'

const FACILITY_DOT: Record<string, string> = {
  electricity: 'var(--color-dusty-pink)',
  library:     'var(--color-peach)',
  computers:   'var(--color-sage)',
}

const FILTER_PRESETS: { label: string; facility: FacilityFilter; state: EvidenceFilter }[] = [
  { label: 'All Schools',      facility: 'all',         state: 'ALL' },
  { label: '⚡ No Electricity', facility: 'electricity', state: 'CONFIRMED_GAP' },
  { label: '📚 No Library',    facility: 'library',     state: 'CONFIRMED_GAP' },
  { label: '💻 No Computers',  facility: 'computers',   state: 'CONFIRMED_GAP' },
  { label: '❓ Missing Data',   facility: 'all',         state: 'MISSING' },
]

export default function DataPage() {
  const [summary,        setSummary]        = useState<any>(null)
  const [quality,        setQuality]        = useState<any[]>([])
  const [schools,        setSchools]        = useState<any[]>([])
  const [loading,        setLoading]        = useState(true)
  const [search,         setSearch]         = useState('')
  const [facilityFilter, setFacilityFilter] = useState<FacilityFilter>('all')
  const [stateFilter,    setStateFilter]    = useState<EvidenceFilter>('ALL')
  const [districtFilter, setDistrictFilter] = useState<string>('all')
  const [activePreset,   setActivePreset]   = useState<number>(0)

  useEffect(() => {
    setLoading(true)
    Promise.all([api.dataSummary(), api.dataQuality(), api.schools({ in_cohort: true })])
      .then(([s, q, sc]) => { setSummary(s); setQuality(q); setSchools(sc) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const districts = useMemo(() => {
    const ds = new Set(schools.map(s => s.district).filter(Boolean))
    return ['all', ...Array.from(ds).sort()]
  }, [schools])

  const filtered = useMemo(() => {
    return schools.filter(school => {
      const matchesSearch = !search ||
        school.name?.toLowerCase().includes(search.toLowerCase()) ||
        school.district?.toLowerCase().includes(search.toLowerCase()) ||
        school.external_id?.toLowerCase().includes(search.toLowerCase())
      const matchesDistrict = districtFilter === 'all' || school.district === districtFilter
      let matchesFacilityState = true
      if (facilityFilter !== 'all' && stateFilter !== 'ALL') {
        matchesFacilityState = school.evidence?.[facilityFilter] === stateFilter
      } else if (stateFilter !== 'ALL') {
        matchesFacilityState = Object.values(school.evidence ?? {}).some(v => v === stateFilter)
      }
      return matchesSearch && matchesDistrict && matchesFacilityState
    })
  }, [schools, search, facilityFilter, stateFilter, districtFilter])

  const applyPreset = (index: number) => {
    const p = FILTER_PRESETS[index]
    setActivePreset(index)
    setFacilityFilter(p.facility)
    setStateFilter(p.state)
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300 }}>
      <div className="spinner" />
    </div>
  )

  const ec = summary?.evidence_counts ?? {}
  const facilities = ['electricity', 'library', 'computers']
  const countGaps    = (f: string) => ec[f]?.CONFIRMED_GAP ?? 0
  const countMissing = (f: string) => ec[f]?.MISSING ?? 0

  return (
    <div className="page fade-in">

      {/* Page header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Data Overview</h2>
          <div className="page-subtitle">
            Karnataka Schools Facilities Dataset
            <span style={{ color: 'var(--border-main)' }}>·</span>
            {summary?.cohort_schools ?? 0} schools in cohort
            <ProvenanceBadge type="official" year="2017-18" />
          </div>
        </div>
      </div>

      {/* KPI tiles */}
      <div className="grid-kpi">
        <KpiTile label="Cohort Schools"   value={summary?.cohort_schools ?? 0}                                   provenance="official" accent="var(--color-primary)"    />
        <KpiTile label="Electricity Gaps" value={countGaps('electricity')}                                       provenance="official" accent="var(--color-dusty-pink)" />
        <KpiTile label="Library Gaps"     value={countGaps('library')}                                           provenance="official" accent="var(--color-peach)"       />
        <KpiTile label="Computer Gaps"    value={countGaps('computers')}                                         provenance="official" accent="var(--color-sage)"        />
        <KpiTile label="Missing Records"  value={facilities.reduce((a, f) => a + countMissing(f), 0)}            provenance="official" accent="var(--color-yellow)"      />
      </div>

      {/* Evidence State Breakdown */}
      <div className="card">
        <div className="section-header">
          <h3 className="section-title">Evidence State Breakdown</h3>
          <ProvenanceBadge type="official" year="2017-18" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {facilities.map(facility => {
            const counts   = ec[facility] ?? {}
            const total    = Object.values(counts).reduce((a: any, b: any) => a + b, 0) as number
            const gapCount = counts['CONFIRMED_GAP'] ?? 0
            const gapPct   = total > 0 ? Math.round(gapCount / total * 100) : 0
            return (
              <div key={facility}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: FACILITY_DOT[facility], display: 'inline-block', flexShrink: 0 }} />
                    {facility}
                  </span>
                  <span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)' }}>
                    {total} records · <strong style={{ color: gapPct > 50 ? 'var(--status-danger)' : 'var(--text-secondary)' }}>{gapPct}% gaps</strong>
                  </span>
                </div>
                {/* Stacked bar */}
                <div style={{ height: 10, borderRadius: 999, background: 'var(--border-light)', display: 'flex', overflow: 'hidden', marginBottom: 'var(--space-2)' }}>
                  {(['CONFIRMED_GAP', 'CONFIRMED_OK', 'MISSING', 'UNRELIABLE'] as const).map(state => {
                    const pct   = total > 0 ? ((counts[state] ?? 0) / total * 100) : 0
                    const color = state === 'CONFIRMED_GAP'
                      ? 'var(--status-danger)'
                      : state === 'CONFIRMED_OK'
                        ? 'var(--status-success)'
                        : state === 'MISSING'
                          ? 'var(--status-warning)'
                          : 'var(--color-mauve)'
                    return pct > 0
                      ? <div key={state} style={{ width: `${pct}%`, background: color, transition: 'width 0.4s' }} />
                      : null
                  })}
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                  {Object.entries(counts).map(([state, count]: any) => (
                    <button
                      key={state}
                      onClick={() => { setFacilityFilter(facility as FacilityFilter); setStateFilter(state as EvidenceFilter); setActivePreset(-1) }}
                      style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                      title={`Filter: ${facility} = ${state}`}
                    >
                      <EvidenceChip state={state} />
                      <span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)' }}>{count}</span>
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
          {/* Legend */}
          <div style={{ display: 'flex', gap: 'var(--space-5)', flexWrap: 'wrap', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--border-light)' }}>
            {[
              ['CONFIRMED_GAP', 'var(--status-danger)', 'Gap'],
              ['CONFIRMED_OK',  'var(--status-success)', 'OK'],
              ['MISSING',       'var(--status-warning)', 'Missing'],
              ['UNRELIABLE',    'var(--color-mauve)',    'Unreliable'],
            ].map(([s, c, l]) => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)', fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: c as string, flexShrink: 0 }} />
                {l}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Schools Table */}
      <div className="card">
        {/* Table toolbar */}
        <div style={{ marginBottom: 'var(--space-5)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
            <h3 className="section-title" style={{ margin: 0 }}>
              Cohort Schools
              <span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', fontWeight: 400 }}>
                {filtered.length} of {schools.length}
              </span>
            </h3>
            <input
              className="form-input"
              placeholder="Search by name, district or code…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ width: 260 }}
            />
          </div>

          {/* Quick filter chips */}
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', marginBottom: 'var(--space-3)' }}>
            {FILTER_PRESETS.map((p, i) => (
              <button
                key={i}
                onClick={() => applyPreset(i)}
                className={`chip${activePreset === i ? ' chip-active' : ''}`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Advanced filters */}
          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div>
              <label className="form-label">Facility</label>
              <select
                className="form-input"
                value={facilityFilter}
                onChange={e => { setFacilityFilter(e.target.value as FacilityFilter); setActivePreset(-1) }}
                style={{ width: 150 }}
              >
                <option value="all">All Facilities</option>
                <option value="electricity">Electricity</option>
                <option value="library">Library</option>
                <option value="computers">Computers</option>
              </select>
            </div>
            <div>
              <label className="form-label">Evidence State</label>
              <select
                className="form-input"
                value={stateFilter}
                onChange={e => { setStateFilter(e.target.value as EvidenceFilter); setActivePreset(-1) }}
                style={{ width: 170 }}
              >
                <option value="ALL">Any State</option>
                <option value="CONFIRMED_GAP">Confirmed Gap</option>
                <option value="CONFIRMED_OK">Confirmed OK</option>
                <option value="MISSING">Missing Data</option>
                <option value="UNRELIABLE">Unreliable</option>
              </select>
            </div>
            <div>
              <label className="form-label">District</label>
              <select
                className="form-input"
                value={districtFilter}
                onChange={e => setDistrictFilter(e.target.value)}
                style={{ width: 140 }}
              >
                {districts.map(d => (
                  <option key={d} value={d}>{d === 'all' ? 'All Districts' : `Dist ${d}`}</option>
                ))}
              </select>
            </div>
            {(facilityFilter !== 'all' || stateFilter !== 'ALL' || districtFilter !== 'all' || search) && (
              <button
                className="btn btn-secondary"
                onClick={() => { setFacilityFilter('all'); setStateFilter('ALL'); setDistrictFilter('all'); setSearch(''); setActivePreset(0) }}
                style={{ fontSize: 'var(--font-sm)' }}
              >
                ✕ Clear
              </button>
            )}
          </div>

          {/* Active filter pill */}
          {(facilityFilter !== 'all' || stateFilter !== 'ALL') && (
            <div style={{
              marginTop: 'var(--space-3)',
              padding: 'var(--space-2) var(--space-3)',
              background: 'var(--color-primary-light)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-sm)',
              color: 'var(--color-primary-dark)',
              display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)',
            }}>
              <span style={{ fontWeight: 600 }}>Filtered:</span>
              <span style={{ textTransform: 'capitalize' }}>{facilityFilter !== 'all' ? facilityFilter : 'all facilities'}</span>
              <span style={{ opacity: 0.5 }}>·</span>
              <span>{stateFilter !== 'ALL' ? stateFilter.replace(/_/g, ' ').toLowerCase() : 'any state'}</span>
              <span style={{ opacity: 0.5 }}>·</span>
              <strong>{filtered.length} school{filtered.length !== 1 ? 's' : ''}</strong>
            </div>
          )}
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>School</th>
                <th>District</th>
                <th>Block</th>
                <th
                  style={{ cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => { setFacilityFilter('electricity'); setStateFilter('CONFIRMED_GAP'); setActivePreset(-1) }}
                  title="Click to filter electricity gaps"
                >
                  Electricity ↓
                </th>
                <th
                  style={{ cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => { setFacilityFilter('library'); setStateFilter('CONFIRMED_GAP'); setActivePreset(-1) }}
                  title="Click to filter library gaps"
                >
                  Library ↓
                </th>
                <th
                  style={{ cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => { setFacilityFilter('computers'); setStateFilter('CONFIRMED_GAP'); setActivePreset(-1) }}
                  title="Click to filter computer gaps"
                >
                  Computers ↓
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 'var(--space-10)' }}>
                    {schools.length === 0
                      ? 'No schools loaded. Add a CSV to data/raw/ and reload.'
                      : 'No schools match the current filters.'}
                  </td>
                </tr>
              ) : filtered.map(school => (
                <tr key={school.id}>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: 'var(--font-sm)' }}>
                    {school.name}
                  </td>
                  <td style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>
                    {school.district ? `Dist ${school.district}` : '—'}
                  </td>
                  <td style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>
                    {school.block ? `Block ${school.block}` : '—'}
                  </td>
                  <td><EvidenceChip state={school.evidence?.electricity ?? 'MISSING'} /></td>
                  <td><EvidenceChip state={school.evidence?.library    ?? 'MISSING'} /></td>
                  <td><EvidenceChip state={school.evidence?.computers  ?? 'MISSING'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filtered.length > 0 && (
          <div style={{ marginTop: 'var(--space-3)', fontSize: 'var(--font-xs)', color: 'var(--text-muted)', textAlign: 'right' }}>
            Tip: click column headers to filter by that facility gap
          </div>
        )}
      </div>

      {/* Data Quality Log */}
      {quality.length > 0 && (
        <div className="card">
          <div className="section-header">
            <h3 className="section-title">Data Quality Log</h3>
          </div>
          <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
            Fields excluded or flagged during data cleaning.
          </p>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr><th>Field</th><th>Reason</th><th>Rows Affected</th></tr>
              </thead>
              <tbody>
                {quality.map((q, i) => (
                  <tr key={i}>
                    <td><code>{q.field}</code></td>
                    <td style={{ fontSize: 'var(--font-sm)' }}>{q.reason}</td>
                    <td style={{ fontWeight: 600 }}>{q.rows_affected.toLocaleString()}</td>
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
