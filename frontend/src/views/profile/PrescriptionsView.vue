<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { usePrescriptions, useCreatePrescriptionMutation, useDeletePrescriptionMutation } from '@/api/prescriptions.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { prescriptionSchema } from '@/schemas/prescription.schema'
import { formatDate } from '@/utils/format'
import type { PrescriptionSearchParams } from '@/types/prescription.types'
import AppTable from '@/components/ui/AppTable.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'

const router = useRouter()
const toast = useToast()
const { open: confirmOpen, onConfirm, onCancel, confirm } = useConfirm()
const { page, size, params: paginationParams, setPage, setSize } = usePagination()

const search = ref('')
const statusFilter = ref<'' | 'active' | 'completed'>('')
const deletingId = ref<string | null>(null)

const queryParams = computed<PrescriptionSearchParams>(() => ({
  ...paginationParams.value,
  search: search.value || undefined,
  status: statusFilter.value || undefined,
}))

const { data, isLoading } = usePrescriptions(queryParams)
const { mutate: createPrescription, isPending: creating } = useCreatePrescriptionMutation()
const { mutate: deletePrescription, isPending: deleting } = useDeletePrescriptionMutation()

const showModal = ref(false)
const formErrors = reactive<Record<string, string>>({})
const form = reactive({
  name: '',
  notes: '',
  status: 'active' as 'active' | 'completed',
  items: [{ drug_name: '', dosage: '', frequency: '', duration: '' }],
})

function resetForm() {
  form.name = ''
  form.notes = ''
  form.status = 'active'
  form.items = [{ drug_name: '', dosage: '', frequency: '', duration: '' }]
  Object.keys(formErrors).forEach((k) => delete formErrors[k])
}

function addItem() {
  form.items.push({ drug_name: '', dosage: '', frequency: '', duration: '' })
}

function removeItem(i: number) {
  if (form.items.length > 1) form.items.splice(i, 1)
}

function validateForm() {
  Object.keys(formErrors).forEach((k) => delete formErrors[k])
  try {
    prescriptionSchema.parse(form)
    return true
  } catch (e) {
    if (e instanceof z.ZodError) e.issues.forEach((err) => { if (err.path[0]) formErrors[err.path[0] as string] = err.message })
    return false
  }
}

function submitForm() {
  if (!validateForm()) return
  createPrescription(form, {
    onSuccess: () => {
      toast.success('Tạo đơn thuốc thành công')
      showModal.value = false
      resetForm()
    },
    onError: (e) => toast.error((e as { message?: string })?.message || 'Tạo đơn thuốc thất bại'),
  })
}

async function deleteItem(id: string) {
  deletingId.value = id
  const confirmed = await confirm()
  if (!confirmed) { deletingId.value = null; return }
  deletePrescription(id, {
    onSuccess: () => toast.success('Đã xóa đơn thuốc'),
    onError: (e) => toast.error((e as { message?: string })?.message || 'Không thể xóa đơn thuốc này'),
    onSettled: () => { deletingId.value = null },
  })
}

const columns = [
  { key: 'name', label: 'Tên đơn thuốc' },
  { key: 'items_count', label: 'Số thuốc', align: 'center' as const },
  { key: 'status', label: 'Trạng thái', align: 'center' as const },
  { key: 'created_at', label: 'Ngày tạo' },
  { key: 'actions', label: '', align: 'right' as const, width: '120px' },
]

const statusOptions = [
  { label: 'Tất cả', value: '' },
  { label: 'Đang dùng', value: 'active' },
  { label: 'Hoàn thành', value: 'completed' },
]
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-[#111827]">Đơn thuốc</h1>
      <AppButton @click="showModal = true; resetForm()">+ Tạo đơn thuốc</AppButton>
    </div>

    <!-- Filters -->
    <div class="flex items-center gap-3 bg-white p-3 rounded-xl border border-[#E5E7EB]">
      <AppInput v-model="search" placeholder="Tìm kiếm đơn thuốc..." class="flex-1" />
      <AppSelect v-model="statusFilter" :options="statusOptions" placeholder="Trạng thái" class="w-40" />
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
      <AppTable :columns="columns" :data="(data?.items ?? []) as any[]" :loading="isLoading" empty-message="Chưa có đơn thuốc nào">
        <template #status="{ row }">
          <AppBadge :variant="row.status === 'active' ? 'success' : 'default'">
            {{ row.status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}
          </AppBadge>
        </template>
        <template #items_count="{ row }">
          {{ row.items?.length ?? 0 }}
        </template>
        <template #created_at="{ row }">
          {{ formatDate(row.created_at as string) }}
        </template>
        <template #actions="{ row }">
          <div class="flex items-center gap-1 justify-end">
            <AppButton variant="ghost" size="sm" @click="router.push(`/profile/prescriptions/${row.id}`)">Xem</AppButton>
            <AppButton variant="ghost" size="sm" class="text-red-500 hover:text-red-700" :loading="deleting && deletingId === row.id" @click="deleteItem(row.id as string)">Xóa</AppButton>
          </div>
        </template>
      </AppTable>

      <div v-if="data?.meta" class="px-4 border-t border-[#E5E7EB]">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>

    <!-- Create modal -->
    <AppModal :open="showModal" title="Tạo đơn thuốc mới" size="lg" @close="showModal = false">
      <form @submit.prevent="submitForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.name" label="Tên đơn thuốc" placeholder="VD: Đơn thuốc tháng 4" :error="formErrors.name" required />
          <AppSelect v-model="form.status" label="Trạng thái" :options="[{ label: 'Đang dùng', value: 'active' }, { label: 'Hoàn thành', value: 'completed' }]" />
        </div>
        <AppTextarea v-model="form.notes" label="Ghi chú" placeholder="Ghi chú thêm..." :rows="2" />

        <!-- Drug items -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-medium text-[#374151]">Danh sách thuốc <span class="text-red-500">*</span></label>
            <AppButton variant="ghost" size="sm" type="button" @click="addItem">+ Thêm thuốc</AppButton>
          </div>
          <p v-if="formErrors.items" class="text-xs text-red-500 mb-2">{{ formErrors.items }}</p>

          <div v-for="(item, i) in form.items" :key="i" class="flex gap-2 items-start border border-[#E5E7EB] rounded-xl p-3 mb-2">
            <div class="flex-1 grid grid-cols-2 gap-2">
              <AppInput v-model="item.drug_name" placeholder="Tên thuốc *" :error="formErrors[`items.${i}.drug_name`]" />
              <AppInput v-model="item.dosage" placeholder="Liều dùng *" :error="formErrors[`items.${i}.dosage`]" />
              <AppInput v-model="item.frequency" placeholder="Tần suất (VD: 2 lần/ngày)" />
              <AppInput v-model="item.duration" placeholder="Thời gian (VD: 7 ngày)" />
            </div>
            <button type="button" @click="removeItem(i)" class="mt-1 text-[#9CA3AF] hover:text-red-500 p-1 flex-shrink-0">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </form>

      <template #footer>
        <AppButton variant="ghost" @click="showModal = false">Hủy</AppButton>
        <AppButton :loading="creating" @click="submitForm">Tạo đơn thuốc</AppButton>
      </template>
    </AppModal>

    <!-- Confirm delete -->
    <AppConfirmDialog :open="confirmOpen" title="Xóa đơn thuốc" message="Bạn có chắc muốn xóa đơn thuốc này? Hành động này không thể hoàn tác." danger :loading="deleting" @confirm="onConfirm" @cancel="onCancel" />
  </div>
</template>
