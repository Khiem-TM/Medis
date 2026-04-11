import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from './axios'
import type { UserResponse } from '@/types/auth.types'
import type { UpdateProfileRequest, ChangePasswordRequest } from '@/types/user.types'

export const userKeys = {
  all: ['users'] as const,
  me: () => [...userKeys.all, 'me'] as const,
}

export const usersApi = {
  getMe: () => api.get<UserResponse>('/users/me').then((r) => r.data),
  updateMe: (data: UpdateProfileRequest) => api.put<UserResponse>('/users/me', data).then((r) => r.data),
  changePassword: (data: ChangePasswordRequest) => api.put('/users/me/password', data).then((r) => r.data),
  uploadAvatar: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<{ avatar_url: string }>('/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },
}

export function useCurrentUserQuery() {
  return useQuery({ queryKey: userKeys.me(), queryFn: usersApi.getMe })
}

export function useUpdateProfileMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: usersApi.updateMe,
    onSuccess: () => qc.invalidateQueries({ queryKey: userKeys.me() }),
  })
}

export function useChangePasswordMutation() {
  return useMutation({ mutationFn: usersApi.changePassword })
}

export function useUploadAvatarMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: usersApi.uploadAvatar,
    onSuccess: () => qc.invalidateQueries({ queryKey: userKeys.me() }),
  })
}
