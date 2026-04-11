import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { InteractionCheckResult, CreateInteractionRequest, DrugInteraction, AdminInteractionSearchParams } from '@/types/interaction.types'
import type { PaginatedResponse } from '@/types/api.types'

export const interactionKeys = {
  all: ['interactions'] as const,
  adminList: (params: AdminInteractionSearchParams) => [...interactionKeys.all, 'admin', params] as const,
}

export const interactionsApi = {
  check: (drug_ids: string[]) =>
    api.post<InteractionCheckResult>('/interactions/check', { drug_ids }).then((r) => r.data),
  export: (drug_ids: string[]) =>
    api.post('/interactions/check/export', { drug_ids }, { responseType: 'blob' }).then((r) => r.data),

  // Admin
  adminList: (params: AdminInteractionSearchParams) =>
    api.get<PaginatedResponse<DrugInteraction>>('/admin/interactions', { params }).then((r) => r.data),
  adminCreate: (data: CreateInteractionRequest) =>
    api.post<DrugInteraction>('/admin/interactions', data).then((r) => r.data),
  adminUpdate: ({ id, data }: { id: string; data: Partial<CreateInteractionRequest> }) =>
    api.put<DrugInteraction>(`/admin/interactions/${id}`, data).then((r) => r.data),
  adminDelete: (id: string) => api.delete(`/admin/interactions/${id}`).then((r) => r.data),
}

export function useInteractionCheckMutation() {
  return useMutation({ mutationFn: interactionsApi.check })
}

export function useAdminInteractions(params: Ref<AdminInteractionSearchParams>) {
  return useQuery({
    queryKey: computed(() => interactionKeys.adminList(params.value)),
    queryFn: () => interactionsApi.adminList(params.value),
  })
}

export function useCreateInteractionMutation() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: interactionsApi.adminCreate, onSuccess: () => qc.invalidateQueries({ queryKey: interactionKeys.all }) })
}

export function useUpdateInteractionMutation() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: interactionsApi.adminUpdate, onSuccess: () => qc.invalidateQueries({ queryKey: interactionKeys.all }) })
}

export function useDeleteInteractionMutation() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: interactionsApi.adminDelete, onSuccess: () => qc.invalidateQueries({ queryKey: interactionKeys.all }) })
}
