import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from './axios'
import type { MedicationReminder, CreateReminderRequest, UpdateReminderRequest } from '@/types/reminder.types'

export const reminderKeys = {
  all: ['reminders'] as const,
  list: () => [...reminderKeys.all, 'list'] as const,
  today: () => [...reminderKeys.all, 'today'] as const,
}

export const remindersApi = {
  list: () => api.get<MedicationReminder[]>('/users/me/reminders').then((r) => r.data),
  today: () => api.get<MedicationReminder[]>('/users/me/reminders/today').then((r) => r.data),
  create: (data: CreateReminderRequest) =>
    api.post<MedicationReminder>('/users/me/reminders', data).then((r) => r.data),
  update: ({ id, data }: { id: number; data: UpdateReminderRequest }) =>
    api.put<MedicationReminder>(`/users/me/reminders/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/users/me/reminders/${id}`).then((r) => r.data),
}

export function useReminders() {
  return useQuery({ queryKey: reminderKeys.list(), queryFn: remindersApi.list })
}

export function useTodaySchedule() {
  return useQuery({ queryKey: reminderKeys.today(), queryFn: remindersApi.today })
}

export function useCreateReminderMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: remindersApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: reminderKeys.all }),
  })
}

export function useUpdateReminderMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: remindersApi.update,
    onSuccess: () => qc.invalidateQueries({ queryKey: reminderKeys.all }),
  })
}

export function useDeleteReminderMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: remindersApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: reminderKeys.all }),
  })
}
