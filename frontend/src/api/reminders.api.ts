import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { MedicationReminder, CreateReminderRequest, UpdateReminderRequest } from '@/types/reminder.types'
import type { MedicationIntakeLog } from '@/types/intake.types'
import { intakeKeys } from './intakes.api'

export const reminderKeys = {
  all: ['reminders'] as const,
  list: () => [...reminderKeys.all, 'list'] as const,
  today: (date?: string) => [...reminderKeys.all, 'today', date ?? 'now'] as const,
}

export const remindersApi = {
  list: () => api.get<MedicationReminder[]>('/users/me/reminders').then((r) => r.data),
  today: (date?: string) =>
    api.get<MedicationReminder[]>('/users/me/reminders/today', { params: date ? { target_date: date } : {} }).then((r) => r.data),
  create: (data: CreateReminderRequest) =>
    api.post<MedicationReminder>('/users/me/reminders', data).then((r) => r.data),
  update: ({ id, data }: { id: number; data: UpdateReminderRequest }) =>
    api.put<MedicationReminder>(`/users/me/reminders/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/users/me/reminders/${id}`).then((r) => r.data),
  confirmIntake: (reminderId: number, notes?: string) =>
    api.post<MedicationIntakeLog>(`/users/me/reminders/${reminderId}/confirm`, { notes }).then((r) => r.data),
}

export function useReminders() {
  return useQuery({ queryKey: reminderKeys.list(), queryFn: remindersApi.list })
}

export function useTodaySchedule(date?: Ref<string | undefined>) {
  return useQuery({
    queryKey: computed(() => reminderKeys.today(date?.value)),
    queryFn: () => remindersApi.today(date?.value),
  })
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

export function useConfirmIntakeMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ reminderId, notes }: { reminderId: number; notes?: string }) =>
      remindersApi.confirmIntake(reminderId, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: reminderKeys.all })
      qc.invalidateQueries({ queryKey: intakeKeys.all })
    },
  })
}
