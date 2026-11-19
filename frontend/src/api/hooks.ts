import { useState, useEffect, useCallback } from 'react'
import { api } from './client'
import type { DataSummary, School, QualityEntry, AuditEntry, ConfigData } from './types'

// Generic fetch hook
function useFetch<T>(fetcher: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    fetcher()
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, deps)  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { load() }, [load])
  return { data, loading, error, refetch: load }
}

export function useDataSummary() {
  return useFetch<DataSummary>(() => api.dataSummary())
}

export function useSchools(inCohort?: boolean) {
  return useFetch<School[]>(() => api.schools({ in_cohort: inCohort }), [inCohort])
}

export function useDataQuality() {
  return useFetch<QualityEntry[]>(() => api.dataQuality())
}

export function useAudit() {
  return useFetch<AuditEntry[]>(() => api.getAudit())
}

export function useConfig() {
  return useFetch<ConfigData>(() => api.getConfig())
}

export function usePlan(planId: number | null) {
  return useFetch<any>(() => planId ? api.getPlan(planId) : Promise.resolve(null), [planId])
}
