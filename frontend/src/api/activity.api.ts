import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { ActivityLog, ActivityLogSearchParams } from '@/types/activity.types'
import type { PaginatedResponse } from '@/types/api.types'
import { downloadBlob } from '@/utils/download'

export const activityKeys = {
  all: ['activity'] as const,
  list: (params: ActivityLogSearchParams) => [...activityKeys.all, 'list', params] as const,
}

export const activityApi = {
  list: (params: ActivityLogSearchParams) =>
    api.get<PaginatedResponse<ActivityLog>>('/activity', { params }).then((r) => r.data),
  delete: (id: string) => api.delete(`/activity/${id}`).then((r) => r.data),
  deleteMany: (ids: string[]) => api.delete('/activity', { data: { ids } }).then((r) => r.data),
  deleteAll: () => api.delete('/activity', { data: { delete_all: true } }).then((r) => r.data),
  export: () => api.get('/activity/export', { responseType: 'blob' }).then((r) => r.data as Blob),
}

export function useActivityLogs(params: Ref<ActivityLogSearchParams>) {
  return useQuery({
    queryKey: computed(() => activityKeys.list(params.value)),
    queryFn: () => activityApi.list(params.value),
  })
}

export function useDeleteActivityMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: activityApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: activityKeys.all }),
  })
}
