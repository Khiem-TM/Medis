import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { HealthProfile, CreateHealthProfileRequest, UpdateHealthProfileRequest, HealthProfileSearchParams } from '@/types/health-profile.types'
import type { PaginatedResponse } from '@/types/api.types'

export const healthProfileKeys = {
  all: ['health-profiles'] as const,
  list: (params: HealthProfileSearchParams) => [...healthProfileKeys.all, 'list', params] as const,
  detail: (id: string) => [...healthProfileKeys.all, 'detail', id] as const,
}

export const healthProfilesApi = {
  list: (params: HealthProfileSearchParams) =>
    api.get<PaginatedResponse<HealthProfile>>('/users/me/health-profiles', { params }).then((r) => r.data),
  get: (id: string) => api.get<HealthProfile>(`/users/me/health-profiles/${id}`).then((r) => r.data),
  create: (data: CreateHealthProfileRequest) => api.post<HealthProfile>('/users/me/health-profiles', data).then((r) => r.data),
  update: ({ id, data }: { id: string; data: UpdateHealthProfileRequest }) =>
    api.put<HealthProfile>(`/users/me/health-profiles/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/users/me/health-profiles/${id}`).then((r) => r.data),
}

export function useHealthProfiles(params: Ref<HealthProfileSearchParams>) {
  return useQuery({
    queryKey: computed(() => healthProfileKeys.list(params.value)),
    queryFn: () => healthProfilesApi.list(params.value),
  })
}

export function useHealthProfileDetail(id: Ref<string>) {
  return useQuery({
    queryKey: computed(() => healthProfileKeys.detail(id.value)),
    queryFn: () => healthProfilesApi.get(id.value),
    enabled: computed(() => !!id.value),
  })
}

export function useCreateHealthProfileMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: healthProfilesApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: healthProfileKeys.all }),
  })
}

export function useUpdateHealthProfileMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: healthProfilesApi.update,
    onSuccess: () => qc.invalidateQueries({ queryKey: healthProfileKeys.all }),
  })
}

export function useDeleteHealthProfileMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: healthProfilesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: healthProfileKeys.all }),
  })
}
