import type { HealthResponse, DataSummary, QualityEntry, School, PlanResult, AuditEntry, ConfigData, StressResult, VoiEntry, ScenarioCompare, BaselineRow } from './types'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API error ${res.status}: ${err}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<HealthResponse>('/health'),

  dataSummary: () => request<DataSummary>('/api/data/summary'),
  dataQuality: () => request<QualityEntry[]>('/api/data/quality'),
  schools: (params?: { district?: string; in_cohort?: boolean }) => {
    const q = new URLSearchParams()
    if (params?.district) q.set('district', params.district)
    if (params?.in_cohort !== undefined) q.set('in_cohort', String(params.in_cohort))
    return request<School[]>(`/api/schools?${q}`)
  },

  runPlan: (body: { budget: number; cohort_only?: boolean }) =>
    request<PlanResult>('/api/plan', { method: 'POST', body: JSON.stringify(body) }),
  getPlan: (id: number) => request<any>(`/api/plan/${id}`),
  listPlans: () => request<any[]>('/api/plans'),

  runStress: (body: { budget: number; n_scenarios?: number; seed?: number; cohort_only?: boolean }) =>
    request<StressResult>('/api/plan/stress', { method: 'POST', body: JSON.stringify(body) }),
  getVerifyFirst: (planId: number) => request<VoiEntry[]>(`/api/plan/${planId}/verify-first`),
  compareScenarios: (body: { budget: number; cohort_only?: boolean }) =>
    request<ScenarioCompare>('/api/plan/compare', { method: 'POST', body: JSON.stringify(body) }),
  getBaselines: (planId: number) => request<BaselineRow[]>(`/api/plan/${planId}/baselines`),
  getExplanations: (planId: number) => request<any>(`/api/plan/${planId}/explanations`),

  submitReview: (recId: number, body: { decision: string; note?: string; reviewer: string }) =>
    request<any>(`/api/reviews/${recId}`, { method: 'POST', body: JSON.stringify(body) }),
  finalizePlan: (planId: number, reviewer: string) =>
    request<any>(`/api/plan/${planId}/finalize?reviewer=${encodeURIComponent(reviewer)}`, { method: 'POST' }),
  getAudit: () => request<AuditEntry[]>('/api/audit'),

  getConfig: () => request<ConfigData>('/api/config'),
  updateConfig: (body: { costs?: Record<string, number>; weights?: Record<string, number> }) =>
    request<any>('/api/config', { method: 'PUT', body: JSON.stringify(body) }),

  copilot: (body: { instruction: string; budget: number; cohort_only?: boolean }) =>
    request<any>('/api/copilot', { method: 'POST', body: JSON.stringify(body) }),
}
