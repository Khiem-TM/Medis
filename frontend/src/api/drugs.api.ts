import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { DrugListItem, DrugDetail, DrugSearchParams, CreateDrugRequest, UpdateDrugRequest, CreateDrugProductRequest } from '@/types/drug.types'
import type { PaginatedResponse } from '@/types/api.types'
import type { DrugInteraction, AdminInteractionSearchParams } from '@/types/interaction.types'

export const drugKeys = {
  all: ['drugs'] as const,
  list: (params: DrugSearchParams) => [...drugKeys.all, 'list', params] as const,
  detail: (id: string) => [...drugKeys.all, 'detail', id] as const,
  interactions: (id: string, params?: AdminInteractionSearchParams) => [...drugKeys.all, id, 'interactions', params] as const,
}

export const drugsApi = {
  search: (params: DrugSearchParams) =>
    api.get<PaginatedResponse<DrugListItem>>('/drugs', { params }).then((r) => r.data),
  get: (id: string) => api.get<DrugDetail>(`/drugs/${id}`).then((r) => r.data),
  getDrugInteractions: (id: string, params?: AdminInteractionSearchParams) =>
    api.get<PaginatedResponse<DrugInteraction>>(`/drugs/${id}/interactions`, { params }).then((r) => r.data),

  // Admin
  create: (data: CreateDrugRequest) => api.post<DrugListItem>('/admin/drugs', data).then((r) => r.data),
  update: ({ id, data }: { id: string; data: UpdateDrugRequest }) =>
    api.put<DrugListItem>(`/admin/drugs/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/admin/drugs/${id}`).then((r) => r.data),
  addProduct: ({ id, data }: { id: string; data: CreateDrugProductRequest }) =>
    api.post(`/admin/drugs/${id}/products`, data).then((r) => r.data),
  updateProduct: ({ id, pid, data }: { id: string; pid: string; data: CreateDrugProductRequest }) =>
    api.put(`/admin/drugs/${id}/products/${pid}`, data).then((r) => r.data),
  deleteProduct: ({ id, pid }: { id: string; pid: string }) =>
    api.delete(`/admin/drugs/${id}/products/${pid}`).then((r) => r.data),
  addWarning: ({ id, text }: { id: string; text: string }) =>
    api.post(`/admin/drugs/${id}/warnings`, { warning_text: text }).then((r) => r.data),
  deleteWarning: ({ id, wid }: { id: string; wid: string }) =>
    api.delete(`/admin/drugs/${id}/warnings/${wid}`).then((r) => r.data),
}

export function useDrugSearch(params: Ref<DrugSearchParams>) {
  return useQuery({
    queryKey: computed(() => drugKeys.list(params.value)),
    queryFn: () => drugsApi.search(params.value),
  })
}

export function useDrugDetail(id: Ref<string>) {
  return useQuery({
    queryKey: computed(() => drugKeys.detail(id.value)),
    queryFn: () => drugsApi.get(id.value),
    enabled: computed(() => !!id.value),
  })
}

export function useDrugInteractions(id: Ref<string>, params?: Ref<AdminInteractionSearchParams>) {
  return useQuery({
    queryKey: computed(() => drugKeys.interactions(id.value, params?.value)),
    queryFn: () => drugsApi.getDrugInteractions(id.value, params?.value),
    enabled: computed(() => !!id.value),
  })
}

export function useCreateDrugMutation() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: drugsApi.create, onSuccess: () => qc.invalidateQueries({ queryKey: drugKeys.all }) })
}

export function useUpdateDrugMutation() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: drugsApi.update, onSuccess: () => qc.invalidateQueries({ queryKey: drugKeys.all }) })
}

export function useDeleteDrugMutation() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: drugsApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: drugKeys.all }) })
}
