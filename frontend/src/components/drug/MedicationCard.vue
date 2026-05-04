<script setup lang="ts">
import type { MedicationReminder } from '@/types/reminder.types'

const props = defineProps<{
  reminder: MedicationReminder
  compact?: boolean
}>()

const emit = defineEmits<{
  toggle: [id: number, active: boolean]
  edit: [reminder: MedicationReminder]
  delete: [id: number]
}>()

function getFrequencyLabel(freq: string, days: string | null) {
  if (freq === 'daily') return 'Hàng ngày'
  if (days) {
    const map: Record<string, string> = {
      mon: 'T2', tue: 'T3', wed: 'T4', thu: 'T5',
      fri: 'T6', sat: 'T7', sun: 'CN',
    }
    return days.split(',').map((d) => map[d.trim()] || d).join(', ')
  }
  return freq
}
</script>

<template>
  <div :class="[
    'bg-card rounded-2xl border transition-all',
    reminder.is_active ? 'border-outline-variant' : 'border-outline-variant/50 opacity-60',
  ]">
    <div class="p-4 flex items-start gap-3">
      <!-- Time badge -->
      <div class="flex-shrink-0 bg-primary-fixed rounded-xl px-3 py-2 text-center min-w-16">
        <p class="text-lg font-bold text-primary leading-none">{{ reminder.reminder_time }}</p>
        <p class="text-xs text-primary/70 mt-0.5">{{ getFrequencyLabel(reminder.frequency, reminder.days_of_week) }}</p>
      </div>

      <!-- Drug info -->
      <div class="flex-1 min-w-0">
        <p class="text-sm font-semibold text-on-surface truncate">{{ reminder.drug_name }}</p>
        <p v-if="reminder.notes" class="text-xs text-outline truncate mt-0.5">{{ reminder.notes }}</p>
      </div>

      <!-- Status + actions -->
      <div class="flex items-center gap-2 flex-shrink-0">
        <!-- Active toggle -->
        <button
          @click="emit('toggle', reminder.id, !reminder.is_active)"
          :class="[
            'w-10 h-6 rounded-full relative transition-colors',
            reminder.is_active ? 'bg-primary' : 'bg-surface-container-high',
          ]"
        >
          <span :class="[
            'absolute top-1 w-4 h-4 bg-white rounded-full transition-all',
            reminder.is_active ? 'right-1' : 'left-1',
          ]" />
        </button>

        <!-- Edit -->
        <button
          @click="emit('edit', reminder)"
          class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-container-low transition-colors"
        >
          <svg class="w-4 h-4 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>

        <!-- Delete -->
        <button
          @click="emit('delete', reminder.id)"
          class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-error-container/30 transition-colors"
        >
          <svg class="w-4 h-4 text-outline hover:text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
