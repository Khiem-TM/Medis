<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReminders, useTodaySchedule, useCreateReminderMutation, useUpdateReminderMutation, useDeleteReminderMutation } from '@/api/reminders.api'
import { useToast } from '@/composables/useToast'
import type { MedicationReminder, CreateReminderRequest } from '@/types/reminder.types'
import MedicationCard from '@/components/drug/MedicationCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppInput from '@/components/ui/AppInput.vue'

const toast = useToast()
const showModal = ref(false)
const editingReminder = ref<MedicationReminder | null>(null)

const { data: reminders, isLoading } = useReminders()
const { data: todaySchedule, isLoading: loadingToday } = useTodaySchedule()
const { mutate: createReminder, isPending: creating } = useCreateReminderMutation()
const { mutate: updateReminder, isPending: updating } = useUpdateReminderMutation()
const { mutate: deleteReminder } = useDeleteReminderMutation()

const form = ref<CreateReminderRequest>({
  drug_name: '',
  reminder_time: '08:00',
  frequency: 'daily',
  notes: '',
})

const frequencyOptions = [
  { label: 'Hàng ngày', value: 'daily' },
  { label: 'Tùy chỉnh ngày', value: 'custom' },
]

function openCreate() {
  editingReminder.value = null
  form.value = { drug_name: '', reminder_time: '08:00', frequency: 'daily', notes: '' }
  showModal.value = true
}

function openEdit(reminder: MedicationReminder) {
  editingReminder.value = reminder
  form.value = {
    drug_name: reminder.drug_name,
    reminder_time: reminder.reminder_time,
    frequency: reminder.frequency,
    notes: reminder.notes ?? '',
  }
  showModal.value = true
}

function doSubmit() {
  if (!form.value.drug_name.trim()) return

  if (editingReminder.value) {
    updateReminder(
      { id: editingReminder.value.id, data: form.value },
      {
        onSuccess: () => { toast.success('Đã cập nhật nhắc nhở'); showModal.value = false },
        onError: () => toast.error('Cập nhật thất bại'),
      },
    )
  } else {
    createReminder(form.value, {
      onSuccess: () => { toast.success('Đã tạo nhắc nhở'); showModal.value = false },
      onError: () => toast.error('Tạo nhắc nhở thất bại'),
    })
  }
}

function doToggle(id: number, isActive: boolean) {
  updateReminder(
    { id, data: { is_active: isActive } },
    { onError: () => toast.error('Cập nhật thất bại') },
  )
}

function doDelete(id: number) {
  deleteReminder(id, {
    onSuccess: () => toast.success('Đã xóa nhắc nhở'),
    onError: () => toast.error('Xóa thất bại'),
  })
}

const now = new Date()
const todayLabel = now.toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-on-surface">Lịch uống thuốc</h1>
        <p class="text-sm text-outline mt-0.5 capitalize">{{ todayLabel }}</p>
      </div>
      <AppButton variant="gradient" @click="openCreate">
        <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Thêm nhắc nhở
      </AppButton>
    </div>

    <!-- Today's schedule -->
    <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
      <h2 class="text-base font-semibold text-on-surface mb-4">Hôm nay</h2>

      <div v-if="loadingToday" class="space-y-3">
        <AppSkeleton v-for="i in 3" :key="i" class="h-16 rounded-xl" />
      </div>
      <div v-else-if="!todaySchedule?.length" class="text-center py-8">
        <svg class="w-12 h-12 text-outline/40 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-sm text-outline">Không có lịch uống thuốc hôm nay</p>
      </div>
      <div v-else class="flex gap-3 overflow-x-auto pb-2 no-scrollbar">
        <div
          v-for="r in todaySchedule"
          :key="r.id"
          :class="[
            'flex-none w-44 p-4 rounded-xl transition-all',
            r.is_active ? 'bg-primary text-white shadow-md shadow-primary/20' : 'bg-surface-container-low',
          ]"
        >
          <p :class="['text-xs font-bold uppercase tracking-wider mb-1', r.is_active ? 'opacity-80' : 'text-outline']">
            Hoạt động
          </p>
          <p :class="['text-xl font-bold leading-none', r.is_active ? '' : 'text-on-surface']">
            {{ r.reminder_time }}
          </p>
          <p :class="['text-sm mt-1 font-medium truncate', r.is_active ? 'opacity-90' : 'text-on-surface-variant']">
            {{ r.drug_name }}
          </p>
        </div>
      </div>
    </div>

    <!-- All reminders management -->
    <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-semibold text-on-surface">Tất cả nhắc nhở</h2>
        <span v-if="reminders?.length" class="text-xs text-outline">{{ reminders.length }} nhắc nhở</span>
      </div>

      <div v-if="isLoading" class="space-y-3">
        <AppSkeleton v-for="i in 4" :key="i" class="h-16 rounded-xl" />
      </div>
      <div v-else-if="!reminders?.length" class="text-center py-10">
        <p class="text-sm text-outline">Chưa có nhắc nhở nào</p>
        <button class="mt-2 text-sm text-primary hover:underline" @click="openCreate">Thêm nhắc nhở đầu tiên</button>
      </div>
      <div v-else class="space-y-3">
        <MedicationCard
          v-for="r in reminders"
          :key="r.id"
          :reminder="r"
          @toggle="doToggle"
          @edit="openEdit"
          @delete="doDelete"
        />
      </div>
    </div>

    <!-- Add/Edit modal -->
    <AppModal v-model="showModal" :title="editingReminder ? 'Sửa nhắc nhở' : 'Thêm nhắc nhở mới'">
      <form @submit.prevent="doSubmit" class="space-y-4">
        <AppInput
          v-model="form.drug_name"
          label="Tên thuốc"
          placeholder="Ví dụ: Metformin 500mg"
          required
        />
        <AppInput
          v-model="form.reminder_time"
          type="time"
          label="Giờ uống thuốc"
          required
        />
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Tần suất</label>
          <select
            v-model="form.frequency"
            class="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
          >
            <option v-for="opt in frequencyOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <AppInput
          v-model="form.notes"
          label="Ghi chú (tuỳ chọn)"
          placeholder="Ví dụ: Uống sau bữa ăn sáng"
        />
        <div class="flex justify-end gap-3 pt-2">
          <AppButton type="button" variant="ghost" @click="showModal = false">Hủy</AppButton>
          <AppButton type="submit" variant="gradient" :loading="creating || updating">
            {{ editingReminder ? 'Lưu thay đổi' : 'Thêm nhắc nhở' }}
          </AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>
