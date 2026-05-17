import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { IntakeStatsResponse, MedicationIntakeLog } from '@/types/intake.types'
import type { PaginatedResponse } from '@/types/api.types'

export const intakeKeys = {
  all: ['intakes'] as const,
  stats: (period: string) => [...intakeKeys.all, 'stats', period] as const,
  history: (params: { page: number; size: number }) => [...intakeKeys.all, 'history', params] as const,
}

export const intakesApi = {
  getStats: (period: string) =>
    api.get<IntakeStatsResponse>('/users/me/intakes/stats', { params: { period } }).then((r) => r.data),
  getHistory: (page: number, size: number) =>
    api
      .get<PaginatedResponse<MedicationIntakeLog>>('/users/me/intakes/history', { params: { page, size } })
      .then((r) => r.data),
}

export function useIntakeStats(period: Ref<'week' | 'month'>) {
  return useQuery({
    queryKey: computed(() => intakeKeys.stats(period.value)),
    queryFn: () => intakesApi.getStats(period.value),
  })
}

export function useIntakeHistory(page: Ref<number>, size: Ref<number>) {
  return useQuery({
    queryKey: computed(() => intakeKeys.history({ page: page.value, size: size.value })),
    queryFn: () => intakesApi.getHistory(page.value, size.value),
  })
}
