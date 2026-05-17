import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from './axios'

export interface VitalRecord {
  id: number
  user_id: number
  heart_rate: number | null
  systolic_bp: number | null
  diastolic_bp: number | null
  blood_glucose: number | null
  notes: string | null
  recorded_at: string
  created_at: string
}

export interface VitalRecordCreate {
  heart_rate?: number | null
  systolic_bp?: number | null
  diastolic_bp?: number | null
  blood_glucose?: number | null
  notes?: string | null
  recorded_at?: string | null
}

export const vitalKeys = {
  all: ['vitals'] as const,
  latest: () => [...vitalKeys.all, 'latest'] as const,
  list: (limit: number) => [...vitalKeys.all, 'list', limit] as const,
}

export const vitalsApi = {
  getLatest: () => api.get<VitalRecord | null>('/users/me/vitals/latest').then((r) => r.data),
  list: (limit = 30) =>
    api.get<VitalRecord[]>('/users/me/vitals', { params: { limit } }).then((r) => r.data),
  create: (data: VitalRecordCreate) =>
    api.post<VitalRecord>('/users/me/vitals', data).then((r) => r.data),
}

export function useLatestVital() {
  return useQuery({ queryKey: vitalKeys.latest(), queryFn: vitalsApi.getLatest })
}

export function useCreateVitalMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: vitalsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: vitalKeys.all }),
  })
}
