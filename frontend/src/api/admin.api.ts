import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { AdminStats, AdminUserDetail, UpdateAdminUserRequest, AdminUserSearchParams, SystemLog, SystemLogSearchParams, AdminActivityLogSearchParams } from '@/types/admin.types'
import type { ActivityLog } from '@/types/activity.types'
import type { PaginatedResponse } from '@/types/api.types'
import type { UserResponse } from '@/types/auth.types'

export const adminKeys = {
  all: ['admin'] as const,
  stats: () => [...adminKeys.all, 'stats'] as const,
  users: (params: AdminUserSearchParams) => [...adminKeys.all, 'users', params] as const,
  userDetail: (id: string) => [...adminKeys.all, 'users', id] as const,
  systemLogs: (params: SystemLogSearchParams) => [...adminKeys.all, 'systemLogs', params] as const,
  activityLogs: (params: AdminActivityLogSearchParams) => [...adminKeys.all, 'activityLogs', params] as const,
}

export const adminApi = {
  getStats: () => api.get<AdminStats>('/admin/stats').then((r) => r.data),

  // Users
  listUsers: (params: AdminUserSearchParams) =>
    api.get<PaginatedResponse<UserResponse>>('/admin/users', { params }).then((r) => r.data),
  getUser: (id: string) => api.get<AdminUserDetail>(`/admin/users/${id}`).then((r) => r.data),
  updateUser: ({ id, data }: { id: string; data: UpdateAdminUserRequest }) =>
    api.put<UserResponse>(`/admin/users/${id}`, data).then((r) => r.data),
  toggleActive: (id: string) =>
    api.patch<UserResponse>(`/admin/users/${id}/toggle-active`).then((r) => r.data),

  // Logs
  systemLogs: (params: SystemLogSearchParams) =>
    api.get<PaginatedResponse<SystemLog>>('/admin/logs/system', { params }).then((r) => r.data),
  activityLogs: (params: AdminActivityLogSearchParams) =>
    api.get<PaginatedResponse<ActivityLog>>('/admin/logs/activity', { params }).then((r) => r.data),
  exportSystemLogs: () =>
    api.get('/admin/logs/system/export', { responseType: 'blob' }).then((r) => r.data as Blob),
  exportActivityLogs: () =>
    api.get('/admin/logs/activity/export', { responseType: 'blob' }).then((r) => r.data as Blob),
}

export function useAdminStats() {
  return useQuery({ queryKey: adminKeys.stats(), queryFn: adminApi.getStats })
}

export function useAdminUsers(params: Ref<AdminUserSearchParams>) {
  return useQuery({
    queryKey: computed(() => adminKeys.users(params.value)),
    queryFn: () => adminApi.listUsers(params.value),
  })
}

export function useAdminUserDetail(id: Ref<string>) {
  return useQuery({
    queryKey: computed(() => adminKeys.userDetail(id.value)),
    queryFn: () => adminApi.getUser(id.value),
    enabled: computed(() => !!id.value),
  })
}

export function useUpdateAdminUserMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: adminApi.updateUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.all }),
  })
}

export function useToggleUserActiveMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: adminApi.toggleActive,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.all }),
  })
}

export function useSystemLogs(params: Ref<SystemLogSearchParams>) {
  return useQuery({
    queryKey: computed(() => adminKeys.systemLogs(params.value)),
    queryFn: () => adminApi.systemLogs(params.value),
  })
}

export function useAdminActivityLogs(params: Ref<AdminActivityLogSearchParams>) {
  return useQuery({
    queryKey: computed(() => adminKeys.activityLogs(params.value)),
    queryFn: () => adminApi.activityLogs(params.value),
  })
}
