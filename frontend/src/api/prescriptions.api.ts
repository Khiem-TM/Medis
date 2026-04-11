import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { Prescription, CreatePrescriptionRequest, UpdatePrescriptionRequest, PrescriptionSearchParams } from '@/types/prescription.types'
import type { PaginatedResponse } from '@/types/api.types'
import type { InteractionCheckResult } from '@/types/interaction.types'

export const prescriptionKeys = {
  all: ['prescriptions'] as const,
  list: (params: PrescriptionSearchParams) => [...prescriptionKeys.all, 'list', params] as const,
  detail: (id: string) => [...prescriptionKeys.all, 'detail', id] as const,
  interactions: (id: string) => [...prescriptionKeys.all, id, 'interactions'] as const,
}

export const prescriptionsApi = {
  list: (params: PrescriptionSearchParams) =>
    api.get<PaginatedResponse<Prescription>>('/users/me/prescriptions', { params }).then((r) => r.data),
  get: (id: string) => api.get<Prescription>(`/users/me/prescriptions/${id}`).then((r) => r.data),
  create: (data: CreatePrescriptionRequest) => api.post<Prescription>('/users/me/prescriptions', data).then((r) => r.data),
  update: ({ id, data }: { id: string; data: UpdatePrescriptionRequest }) =>
    api.put<Prescription>(`/users/me/prescriptions/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/users/me/prescriptions/${id}`).then((r) => r.data),
  deleteMany: (ids: string[]) => api.delete('/users/me/prescriptions', { data: { ids } }).then((r) => r.data),
  checkInteractions: (id: string) =>
    api.get<InteractionCheckResult>(`/users/me/prescriptions/${id}/interactions`).then((r) => r.data),
}

export function usePrescriptions(params: Ref<PrescriptionSearchParams>) {
  return useQuery({
    queryKey: computed(() => prescriptionKeys.list(params.value)),
    queryFn: () => prescriptionsApi.list(params.value),
  })
}

export function usePrescriptionDetail(id: Ref<string>) {
  return useQuery({
    queryKey: computed(() => prescriptionKeys.detail(id.value)),
    queryFn: () => prescriptionsApi.get(id.value),
    enabled: computed(() => !!id.value),
  })
}

export function usePrescriptionInteractions(id: Ref<string>) {
  return useQuery({
    queryKey: computed(() => prescriptionKeys.interactions(id.value)),
    queryFn: () => prescriptionsApi.checkInteractions(id.value),
    enabled: computed(() => !!id.value),
  })
}

export function useCreatePrescriptionMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: prescriptionsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: prescriptionKeys.all }),
  })
}

export function useUpdatePrescriptionMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: prescriptionsApi.update,
    onSuccess: () => qc.invalidateQueries({ queryKey: prescriptionKeys.all }),
  })
}

export function useDeletePrescriptionMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: prescriptionsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: prescriptionKeys.all }),
  })
}
