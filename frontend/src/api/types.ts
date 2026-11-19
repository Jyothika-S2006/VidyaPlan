// VidyaPlan API type definitions

export interface HealthResponse {
  status: 'ok' | 'degraded'
  db: 'ok' | 'error'
  watsonx_configured: boolean
  version: string
}

export interface EvidenceCounts {
  CONFIRMED_GAP?: number
  CONFIRMED_OK?: number
  MISSING?: number
  UNRELIABLE?: number
}

export interface DataSummary {
  total_schools: number
  cohort_schools: number
  observation_year: string
  evidence_counts: Record<string, EvidenceCounts>
}

export interface QualityEntry {
  field: string
  reason: string
  rows_affected: number
}

export interface School {
  id: number
  external_id: string
  name: string
  district: string | null
  block: string | null
  enrollment: number | null
  in_cohort: boolean
  observation_year: string
  evidence: Record<string, string>
}

export interface PlanItem {
  id: string
  school_id: number
  school_name: string
  facility: string
  cost: number
  priority: number
  electricity_state: string
  reason_code?: string
}

export interface BlockedItem {
  school_name: string
  facility: string
  reason_code: string
}

export interface PlanKpis {
  interventions_funded: number
  schools_improved: number
  deferred_count: number
}

export interface PlanResult {
  plan_id: number | null
  budget: number
  budget_used: number
  budget_remaining: number
  objective: number
  selected: PlanItem[]
  deferred: PlanItem[]
  blocked: BlockedItem[]
  kpis: PlanKpis
}

export interface Recommendation {
  id: number
  school_id: number
  school_name: string
  facility_type: string
  cost: number
  priority: number
  status: 'selected' | 'deferred'
  reason_code: string | null
  robustness: number | null
  review_status: 'pending' | 'approved' | 'rejected'
  explanation: string | null
  explanation_source: string
}

export interface StressDetail {
  item_id: string
  robustness: number
  band: 'green' | 'amber' | 'red'
  fragile: boolean
}

export interface StressResult {
  budget: number
  n_scenarios: number
  seed: number
  base_objective: number
  expected_regret_rs: number
  expected_regret_pct: number
  details: StressDetail[]
  provenance: string
}

export interface VoiEntry {
  school_id: number
  school_name: string
  facility: string
  district: string | null
  p_gap: number
  voi_rs: number
  action_text: string
  provenance: string
}

export interface ScenarioSide {
  budget: number
  budget_used: number
  funded: number
  schools: number
  objective: number
}

export interface ScenarioCompare {
  base: ScenarioSide
  low: ScenarioSide
  high: ScenarioSide
  gained_in_high: Array<{ school_name: string; facility: string }>
  lost_in_low: Array<{ school_name: string; facility: string }>
  marginal: { extra_budget: number; new_items: Array<{ school_name: string; facility: string }>; delta_interventions: number }
  provenance: string
}

export interface BaselineRow {
  method: string
  objective: number
  interventions_funded: number
  schools_improved: number
  budget_used: number
  pct_vs_optimiser: number | null
  provenance: string
}

export interface AuditEntry {
  id: number
  actor: string
  action: string
  entity: string
  entity_id: number | null
  before_state: Record<string, unknown> | null
  after_state: Record<string, unknown> | null
  created_at: string
}

export interface ConfigData {
  costs: Record<string, number>
  weights: Record<string, number>
  provenance: string
}
