<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReminders, useTodaySchedule, useCreateReminderMutation, useUpdateReminderMutation, useDeleteReminderMutation, useConfirmIntakeMutation } from '@/api/reminders.api'
import { useIntakesByDate } from '@/api/intakes.api'
import { useToast } from '@/composables/useToast'
import type { MedicationReminder, CreateReminderRequest } from '@/types/reminder.types'
import type { IntakeStatus } from '@/types/intake.types'
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
const { mutate: confirmIntake, isPending: confirming, variables: confirmingVar } = useConfirmIntakeMutation()

const todayStr = new Date().toISOString().slice(0, 10)
const { data: todayLogs } = useIntakesByDate(ref(todayStr))
const intakeStatusMap = computed<Record<number, IntakeStatus | null>>(() => {
  const map: Record<number, IntakeStatus | null> = {}
  todayLogs.value
    ?.filter((lg) => lg.reminder_id !== null)
    .forEach((lg) => { map[lg.reminder_id!] = lg.status })
  return map
})

const takenCount = computed(() =>
  Object.values(intakeStatusMap.value).filter(s => s === 'taken' || s === 'late').length
)
const totalToday = computed(() => todaySchedule.value?.length ?? 0)
const adherencePct = computed(() => totalToday.value > 0 ? Math.round((takenCount.value / totalToday.value) * 100) : 0)

function doConfirm(reminderId: number) {
  confirmIntake({ reminderId }, {
    onSuccess: () => toast.success('Đã xác nhận uống thuốc'),
    onError: () => toast.error('Xác nhận thất bại'),
  })
}

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
  updateReminder({ id, data: { is_active: isActive } }, { onError: () => toast.error('Cập nhật thất bại') })
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
    <!-- Page header -->
    <div class="flex items-start justify-between flex-wrap gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-widest mb-1" style="color:#00685d;">Theo dõi hôm nay</p>
        <h1 class="text-3xl font-extrabold" style="color:#0A0F1E;">Lịch Uống Thuốc</h1>
        <p class="text-sm mt-1 capitalize" style="color:#4B5563;">{{ todayLabel }}</p>
      </div>
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-95"
        style="background:linear-gradient(135deg,#00685d,#00897B);box-shadow:0 4px 14px rgba(0,104,93,0.28);"
        @click="openCreate"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Thêm nhắc nhở
      </button>
    </div>

    <!-- Today hero + adherence -->
    <div class="rounded-2xl overflow-hidden" style="background:linear-gradient(135deg,rgba(0,104,93,0.08),rgba(0,104,93,0.04));border:1px solid rgba(0,104,93,0.15);">
      <div class="p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-semibold" style="color:#0A0F1E;">Tiến độ hôm nay</h2>
          <span class="text-sm font-bold" :style="adherencePct === 100 ? 'color:#059669;' : adherencePct >= 50 ? 'color:#D97706;' : 'color:#EF4444;'">
            {{ takenCount }} / {{ totalToday }} liều
          </span>
        </div>
        <div class="w-full h-2.5 rounded-full overflow-hidden mb-4" style="background:rgba(15,23,42,0.08);">
          <div
            class="h-full rounded-full transition-all duration-700"
            :style="`width:${adherencePct}%;background:${adherencePct === 100 ? '#10B981' : adherencePct >= 50 ? '#F59E0B' : '#EF4444'};`"
          />
        </div>

        <!-- Today's schedule timeline -->
        <div v-if="loadingToday" class="flex gap-3 overflow-x-auto pb-1">
          <AppSkeleton v-for="i in 4" :key="i" class="flex-none w-40 h-24 rounded-xl" />
        </div>

        <div v-else-if="!todaySchedule?.length" class="flex flex-col items-center py-8">
          <svg class="w-10 h-10 mb-3" style="color:rgba(0,104,93,0.25);" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <p class="text-sm" style="color:#6B7280;">Không có lịch uống thuốc hôm nay</p>
        </div>

        <div v-else class="flex gap-3 overflow-x-auto pb-2 no-scrollbar">
          <div
            v-for="r in todaySchedule"
            :key="r.id"
            class="flex-none w-44 p-4 rounded-xl transition-all"
            :style="intakeStatusMap[r.id] === 'taken' || intakeStatusMap[r.id] === 'late'
              ? 'background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);'
              : intakeStatusMap[r.id] === 'missed'
              ? 'background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);'
              : r.is_active
              ? 'background:white;border:1px solid rgba(0,104,93,0.22);box-shadow:0 2px 8px rgba(0,104,93,0.1);'
              : 'background:rgba(15,23,42,0.03);border:1px solid rgba(15,23,42,0.08);'"
          >
            <p class="text-2xl font-extrabold mb-1" style="color:#0A0F1E;">{{ r.reminder_time }}</p>
            <p class="text-sm font-semibold truncate mb-2" style="color:#1F2937;">{{ r.drug_name }}</p>
            <div class="flex items-center gap-1.5">
              <span v-if="intakeStatusMap[r.id] === 'taken' || intakeStatusMap[r.id] === 'late'" class="text-xs font-bold flex items-center gap-1" style="color:#059669;">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                Đã uống
              </span>
              <span v-else-if="intakeStatusMap[r.id] === 'missed'" class="text-xs font-bold" style="color:#EF4444;">Bỏ lỡ</span>
              <button
                v-else-if="r.is_active"
                class="text-xs font-semibold px-2.5 py-1 rounded-lg text-white transition-all"
                style="background:linear-gradient(135deg,#00685d,#00897B);"
                :disabled="confirming && confirmingVar?.reminderId === r.id"
                @click="doConfirm(r.id)"
              >Xác nhận</button>
              <span v-else class="text-xs" style="color:#9CA3AF;">Tắt</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- All reminders -->
    <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
      <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:rgba(15,23,42,0.06);">
        <h2 class="font-semibold" style="color:#0A0F1E;">
          Tất cả nhắc nhở
          <span v-if="reminders?.length" class="ml-1.5 text-sm font-normal" style="color:#6B7280;">· {{ reminders.length }}</span>
        </h2>
      </div>

      <div class="p-5">
        <div v-if="isLoading" class="space-y-3">
          <AppSkeleton v-for="i in 4" :key="i" class="h-16 rounded-xl" />
        </div>

        <div v-else-if="!reminders?.length" class="flex flex-col items-center py-12">
          <div class="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style="background:rgba(0,104,93,0.08);">
            <svg class="w-7 h-7" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
          </div>
          <p class="text-base font-semibold mb-1" style="color:#0A0F1E;">Chưa có nhắc nhở nào</p>
          <p class="text-sm mb-4" style="color:#6B7280;">Thêm nhắc nhở để không bỏ lỡ liều thuốc</p>
          <button
            class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
            style="background:linear-gradient(135deg,#00685d,#00897B);"
            @click="openCreate"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Thêm nhắc nhở đầu tiên
          </button>
        </div>

        <div v-else class="space-y-3">
          <MedicationCard
            v-for="r in reminders"
            :key="r.id"
            :reminder="r"
            :intake-status="intakeStatusMap[r.id] ?? null"
            :confirm-loading="confirming && confirmingVar?.reminderId === r.id"
            @toggle="doToggle"
            @edit="openEdit"
            @delete="doDelete"
            @confirm="doConfirm"
          />
        </div>
      </div>
    </div>

    <!-- Add/Edit modal -->
    <AppModal :open="showModal" :title="editingReminder ? 'Sửa nhắc nhở' : 'Thêm nhắc nhở mới'" @close="showModal = false">
      <form @submit.prevent="doSubmit" class="space-y-4">
        <AppInput v-model="form.drug_name" label="Tên thuốc" placeholder="Ví dụ: Metformin 500mg" required />
        <AppInput v-model="form.reminder_time" type="time" label="Giờ uống thuốc" required />
        <div>
          <label class="text-sm font-semibold block mb-1.5" style="color:#0A0F1E;">Tần suất</label>
          <select
            v-model="form.frequency"
            class="w-full px-3 py-2.5 rounded-xl text-sm focus:outline-none"
            style="background:rgba(15,23,42,0.04);border:1px solid rgba(15,23,42,0.1);color:#0A0F1E;"
          >
            <option v-for="opt in frequencyOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <AppInput v-model="form.notes" label="Ghi chú (tuỳ chọn)" placeholder="Ví dụ: Uống sau bữa ăn sáng" />
      </form>
      <template #footer>
        <AppButton variant="ghost" @click="showModal = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="creating || updating" @click="doSubmit">
          {{ editingReminder ? 'Lưu thay đổi' : 'Thêm nhắc nhở' }}
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>
