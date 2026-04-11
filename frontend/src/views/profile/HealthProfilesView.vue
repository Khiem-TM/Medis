<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { useHealthProfiles, useCreateHealthProfileMutation, useDeleteHealthProfileMutation } from '@/api/health-profiles.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { healthProfileSchema } from '@/schemas/health-profile.schema'
import { formatDate } from '@/utils/format'
import type { HealthProfileSearchParams } from '@/types/health-profile.types'
import AppTable from '@/components/ui/AppTable.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'

const router = useRouter()
const toast = useToast()
const { open: confirmOpen, onConfirm, onCancel, confirm } = useConfirm()
const { page, size, params: paginationParams, setPage, setSize } = usePagination()

const search = ref('')
const deletingId = ref<string | null>(null)

const queryParams = computed<HealthProfileSearchParams>(() => ({
  ...paginationParams.value,
  search: search.value || undefined,
}))

const { data, isLoading } = useHealthProfiles(queryParams)
const { mutate: createHealthProfile, isPending: creating } = useCreateHealthProfileMutation()
const { mutate: deleteHealthProfile, isPending: deleting } = useDeleteHealthProfileMutation()

const showModal = ref(false)
const formErrors = reactive<Record<string, string>>({})
const form = reactive({
  diagnosis_name: '',
  exam_date: '',
  facility: '',
  doctor: '',
  symptoms: '',
  conclusion: '',
  notes: '',
})

function resetForm() {
  Object.keys(form).forEach((k) => (form as Record<string, string>)[k] = '')
  Object.keys(formErrors).forEach((k) => delete formErrors[k])
}

function validateForm() {
  Object.keys(formErrors).forEach((k) => delete formErrors[k])
  try { healthProfileSchema.parse(form); return true }
  catch (e) {
    if (e instanceof z.ZodError) e.issues.forEach((err) => { if (err.path[0]) formErrors[err.path[0] as string] = err.message })
    return false
  }
}

function submitForm() {
  if (!validateForm()) return
  const payload = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ''))
  createHealthProfile(payload as any, {
    onSuccess: () => { toast.success('Tạo hồ sơ khám bệnh thành công'); showModal.value = false; resetForm() },
    onError: (e) => toast.error((e as { message?: string })?.message || 'Tạo hồ sơ thất bại'),
  })
}

async function deleteItem(id: string) {
  deletingId.value = id
  const confirmed = await confirm()
  if (!confirmed) { deletingId.value = null; return }
  deleteHealthProfile(id, {
    onSuccess: () => toast.success('Đã xóa hồ sơ'),
    onError: () => toast.error('Không thể xóa hồ sơ này'),
    onSettled: () => { deletingId.value = null },
  })
}

const columns = [
  { key: 'diagnosis_name', label: 'Chẩn đoán' },
  { key: 'exam_date', label: 'Ngày khám' },
  { key: 'facility', label: 'Cơ sở y tế' },
  { key: 'doctor', label: 'Bác sĩ' },
  { key: 'actions', label: '', align: 'right' as const, width: '100px' },
]
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-[#111827]">Hồ sơ khám bệnh</h1>
      <AppButton @click="showModal = true; resetForm()">+ Thêm hồ sơ</AppButton>
    </div>

    <div class="flex items-center gap-3 bg-white p-3 rounded-xl border border-[#E5E7EB]">
      <AppInput v-model="search" placeholder="Tìm kiếm hồ sơ..." class="flex-1" />
    </div>

    <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
      <AppTable :columns="columns" :data="(data?.items ?? []) as any[]" :loading="isLoading" empty-message="Chưa có hồ sơ khám bệnh nào">
        <template #exam_date="{ row }">{{ formatDate(row.exam_date as string) }}</template>
        <template #facility="{ row }">{{ row.facility ?? '—' }}</template>
        <template #doctor="{ row }">{{ row.doctor ?? '—' }}</template>
        <template #actions="{ row }">
          <div class="flex items-center gap-1 justify-end">
            <AppButton variant="ghost" size="sm" @click="router.push(`/profile/health/${row.id}`)">Xem</AppButton>
            <AppButton variant="ghost" size="sm" class="text-red-500" :loading="deleting && deletingId === row.id" @click="deleteItem(row.id as string)">Xóa</AppButton>
          </div>
        </template>
      </AppTable>
      <div v-if="data?.meta" class="px-4 border-t border-[#E5E7EB]">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>

    <AppModal :open="showModal" title="Thêm hồ sơ khám bệnh" size="lg" @close="showModal = false">
      <form @submit.prevent="submitForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.diagnosis_name" label="Chẩn đoán" placeholder="VD: Viêm họng cấp" :error="formErrors.diagnosis_name" required />
          <AppInput v-model="form.exam_date" type="date" label="Ngày khám" :error="formErrors.exam_date" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.facility" label="Cơ sở y tế" placeholder="Bệnh viện..." />
          <AppInput v-model="form.doctor" label="Bác sĩ" placeholder="BS. Nguyễn..." />
        </div>
        <AppTextarea v-model="form.symptoms" label="Triệu chứng" placeholder="Mô tả triệu chứng..." :rows="2" />
        <AppTextarea v-model="form.conclusion" label="Kết luận" placeholder="Kết luận khám..." :rows="2" />
        <AppTextarea v-model="form.notes" label="Ghi chú" placeholder="Ghi chú thêm..." :rows="2" />
      </form>
      <template #footer>
        <AppButton variant="ghost" @click="showModal = false">Hủy</AppButton>
        <AppButton :loading="creating" @click="submitForm">Lưu hồ sơ</AppButton>
      </template>
    </AppModal>

    <AppConfirmDialog :open="confirmOpen" title="Xóa hồ sơ" message="Bạn có chắc muốn xóa hồ sơ khám bệnh này?" danger :loading="deleting" @confirm="onConfirm" @cancel="onCancel" />
  </div>
</template>
