import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { PaginatedResponse } from '@/types/api.types'
import type {
  CreateHealthProfileRequest,
  HealthBaselineStructured,
  HealthProfile,
  HealthProfileSearchParams,
  HealthSummary,
  UpdateHealthBaselineRequest,
} from '@/types/health-profile.types'
import type { HealthBaseline } from '@/types/onboarding.types'

function parseJsonArray<T>(raw: string | null | undefined, fallback: T[] = []): T[] {
  if (!raw) return fallback
  try {
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? parsed as T[] : fallback
  } catch {
    return fallback
  }
}

function toStructuredBaseline(raw: HealthBaseline): HealthBaselineStructured {
  const now = new Date().toISOString()
  return {
    id: raw.id,
    user_id: raw.user_id,
    height_cm: raw.height_cm,
    weight_kg: raw.weight_kg,
    blood_type: raw.blood_type,
    chronic_conditions: parseJsonArray<string>(raw.chronic_conditions),
    allergies: parseJsonArray(raw.allergies),
    current_medications: parseJsonArray(raw.current_medications),
    is_pregnant: raw.is_pregnant,
    is_breastfeeding: raw.is_breastfeeding,
    kidney_function: raw.kidney_function,
    liver_function: raw.liver_function,
    health_goals: parseJsonArray<string>(raw.health_goals),
    onboarding_completed: raw.onboarding_completed,
    onboarding_step: raw.onboarding_step,
    created_at: now,
    updated_at: now,
  }
}

async function getLegacyBaseline() {
  return api.get<HealthBaseline>('/users/me/onboarding').then((r) => toStructuredBaseline(r.data))
}

async function updateLegacyBaseline(data: UpdateHealthBaselineRequest) {
  await api.post<HealthBaseline>('/users/me/onboarding/step1', {
    height_cm: data.height_cm ?? null,
    weight_kg: data.weight_kg ?? null,
    blood_type: data.blood_type ?? null,
    is_pregnant: data.is_pregnant ?? false,
    is_breastfeeding: data.is_breastfeeding ?? false,
    kidney_function: data.kidney_function ?? 'normal',
    liver_function: data.liver_function ?? 'normal',
  })
  await api.post<HealthBaseline>('/users/me/onboarding/step2', {
    conditions: data.chronic_conditions ?? [],
    allergies: data.allergies ?? [],
  })
  const response = await api.post<HealthBaseline>('/users/me/onboarding/step3', {
    medications: data.current_medications ?? [],
    health_goals: data.health_goals ?? [],
  })
  return toStructuredBaseline(response.data)
}

export const healthKeys = {
  all: ['user-health'] as const,
  summary: () => [...healthKeys.all, 'summary'] as const,
  baseline: () => [...healthKeys.all, 'baseline'] as const,
  visits: (params: HealthProfileSearchParams) => [...healthKeys.all, 'visits', params] as const,
}

export const healthApi = {
  summary: async () => {
    const [baseline, visits, activePrescriptions, reminders] = await Promise.all([
      getLegacyBaseline(),
      api.get<PaginatedResponse<HealthProfile>>('/users/me/health-profiles', {
        params: { page: 1, size: 5 },
      }).then((r) => r.data),
      api.get<PaginatedResponse<unknown>>('/users/me/prescriptions', {
        params: { page: 1, size: 1, status: 'active' },
      }).then((r) => r.data),
      api.get<Array<{ is_active: boolean }>>('/users/me/reminders').then((r) => r.data),
    ])

    return {
      baseline,
      recent_visits: visits.items,
      total_visits: visits.meta.total,
      active_prescriptions: activePrescriptions.meta.total,
      active_reminders: reminders.filter((item) => item.is_active).length,
      last_exam_date: visits.items[0]?.exam_date ?? null,
    }
  },
  baseline: getLegacyBaseline,
  updateBaseline: updateLegacyBaseline,
  visits: (params: HealthProfileSearchParams) =>
    api.get<PaginatedResponse<HealthProfile>>('/users/me/health-profiles', { params }).then((r) => r.data),
  createVisit: (data: CreateHealthProfileRequest) =>
    api.post<HealthProfile>('/users/me/health-profiles', data).then((r) => r.data),
  deleteVisit: (id: string) => api.delete(`/users/me/health-profiles/${id}`).then((r) => r.data),
}

export function useHealthSummary() {
  return useQuery({
    queryKey: healthKeys.summary(),
    queryFn: healthApi.summary,
  })
}

export function useHealthBaseline() {
  return useQuery({
    queryKey: healthKeys.baseline(),
    queryFn: healthApi.baseline,
  })
}

export function useHealthVisits(params: Ref<HealthProfileSearchParams>) {
  return useQuery({
    queryKey: computed(() => healthKeys.visits(params.value)),
    queryFn: () => healthApi.visits(params.value),
  })
}

export function useUpdateHealthBaselineMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: healthApi.updateBaseline,
    onSuccess: () => qc.invalidateQueries({ queryKey: healthKeys.all }),
  })
}

export function useCreateHealthVisitMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: healthApi.createVisit,
    onSuccess: () => qc.invalidateQueries({ queryKey: healthKeys.all }),
  })
}

export function useDeleteHealthVisitMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: healthApi.deleteVisit,
    onSuccess: () => qc.invalidateQueries({ queryKey: healthKeys.all }),
  })
}
