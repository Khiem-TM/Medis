<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAdminInteractions, useCreateInteractionMutation, useUpdateInteractionMutation, useDeleteInteractionMutation } from '@/api/interactions.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { getSeverityClasses, getSeverityLabel } from '@/utils/severity'
import type { AdminInteractionSearchParams, CreateInteractionRequest, Severity } from '@/types/interaction.types'
import AppTable from '@/components/ui/AppTable.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'

const toast = useToast()
const { page, size, params: paginationParams, setPage, setSize } = usePagination(20)
const severityFilter = ref<Severity | ''>('')

const queryParams = computed<AdminInteractionSearchParams>(() => ({
  ...paginationParams.value,
  severity: severityFilter.value || undefined,
}))

const { data, isLoading } = useAdminInteractions(queryParams)
const { mutate: createInteraction, isPending: creating } = useCreateInteractionMutation()
const { mutate: updateInteraction, isPending: updating } = useUpdateInteractionMutation()
const { mutate: deleteInteraction, isPending: deleting } = useDeleteInteractionMutation()

const defaultForm = (): CreateInteractionRequest => ({
  drug_id_1: '',
  drug_id_2: '',
  severity: 'moderate',
  interaction_type: '',
  description: '',
  recommendation: '',
})

const showCreate = ref(false)
const showEdit = ref(false)
const editId = ref('')
const form = ref(defaultForm())
const confirmState = ref({ open: false, id: '', label: '' })

const severityOptions = [
  { label: 'Tất cả mức độ', value: '' },
  { label: 'Nhẹ', value: 'minor' },
  { label: 'Trung bình', value: 'moderate' },
  { label: 'Nặng', value: 'major' },
]

const severityFormOptions = [
  { label: 'Nhẹ', value: 'minor' },
  { label: 'Trung bình', value: 'moderate' },
  { label: 'Nặng', value: 'major' },
]

const columns = [
  { key: 'drug_id_1', label: 'Thuốc 1' },
  { key: 'drug_id_2', label: 'Thuốc 2' },
  { key: 'severity', label: 'Mức độ', align: 'center' as const },
  { key: 'interaction_type', label: 'Loại' },
  { key: 'description', label: 'Mô tả' },
  { key: 'actions', label: '', align: 'right' as const },
]

function openCreate() {
  form.value = defaultForm()
  showCreate.value = true
}

function doCreate() {
  createInteraction(form.value, {
    onSuccess: () => { toast.success('Đã tạo tương tác'); showCreate.value = false },
    onError: () => toast.error('Không thể tạo tương tác'),
  })
}

function openEdit(row: any) {
  editId.value = row.id
  form.value = {
    drug_id_1: row.drug_id_1,
    drug_id_2: row.drug_id_2,
    severity: row.severity,
    interaction_type: row.interaction_type ?? '',
    description: row.description ?? '',
    recommendation: row.recommendation ?? '',
  }
  showEdit.value = true
}

function doEdit() {
  updateInteraction({ id: editId.value, data: form.value }, {
    onSuccess: () => { toast.success('Đã cập nhật'); showEdit.value = false },
    onError: () => toast.error('Cập nhật thất bại'),
  })
}

function openDelete(row: any) {
  confirmState.value = { open: true, id: row.id, label: `${row.drug_id_1} ↔ ${row.drug_id_2}` }
}

function doDelete() {
  deleteInteraction(confirmState.value.id, {
    onSuccess: () => { toast.success('Đã xóa'); confirmState.value.open = false },
    onError: () => toast.error('Xóa thất bại'),
  })
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-[#111827]">Quản lý tương tác thuốc</h1>
        <p class="text-sm text-[#6B7280] mt-1">Thêm, sửa, xóa các cặp tương tác thuốc đã biết</p>
      </div>
      <AppButton @click="openCreate">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Thêm tương tác
      </AppButton>
    </div>

    <!-- Filter -->
    <div class="bg-white p-3 rounded-xl border border-[#E5E7EB] flex gap-3">
      <AppSelect v-model="severityFilter" :options="severityOptions" class="w-48" />
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
      <div class="px-4 py-3 border-b border-[#E5E7EB]">
        <p class="text-sm text-[#6B7280]">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} cặp tương tác</template>
          <template v-else>Đang tải...</template>
        </p>
      </div>

      <AppTable :columns="columns" :data="(data?.items ?? []) as any[]" :loading="isLoading" empty-message="Không có tương tác nào">
        <template #drug_id_1="{ row }">
          <span class="text-sm font-mono">{{ row.drug_name_1 || row.drug_id_1 }}</span>
        </template>
        <template #drug_id_2="{ row }">
          <span class="text-sm font-mono">{{ row.drug_name_2 || row.drug_id_2 }}</span>
        </template>
        <template #severity="{ row }">
          <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', getSeverityClasses(row.severity)]">
            {{ getSeverityLabel(row.severity) }}
          </span>
        </template>
        <template #interaction_type="{ row }">{{ row.interaction_type ?? '—' }}</template>
        <template #description="{ row }">
          <span class="text-sm text-[#374151] line-clamp-2">{{ row.description ?? '—' }}</span>
        </template>
        <template #actions="{ row }">
          <div class="flex items-center gap-2 justify-end">
            <AppButton variant="ghost" size="sm" @click="openEdit(row)">Sửa</AppButton>
            <AppButton variant="ghost" size="sm" class="text-red-500 hover:text-red-600" @click="openDelete(row)">Xóa</AppButton>
          </div>
        </template>
      </AppTable>

      <div v-if="data?.meta" class="px-4 border-t border-[#E5E7EB]">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>

    <!-- Create/Edit modal (shared form) -->
    <AppModal :open="showCreate" title="Thêm tương tác thuốc" size="lg" @close="showCreate = false">
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-[#374151]">Mã thuốc 1 *</label>
            <input v-model="form.drug_id_1" placeholder="ID thuốc 1" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
          <div>
            <label class="text-sm font-medium text-[#374151]">Mã thuốc 2 *</label>
            <input v-model="form.drug_id_2" placeholder="ID thuốc 2" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-[#374151]">Mức độ *</label>
            <AppSelect v-model="form.severity" :options="severityFormOptions" class="mt-1 w-full" />
          </div>
          <div>
            <label class="text-sm font-medium text-[#374151]">Loại tương tác</label>
            <input v-model="form.interaction_type" placeholder="vd: Dược lý học" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Mô tả</label>
          <textarea v-model="form.description" rows="3" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981] resize-none" />
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Khuyến nghị</label>
          <textarea v-model="form.recommendation" rows="2" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981] resize-none" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="outline" @click="showCreate = false">Hủy</AppButton>
        <AppButton :disabled="!form.drug_id_1 || !form.drug_id_2" :loading="creating" @click="doCreate">Tạo</AppButton>
      </template>
    </AppModal>

    <AppModal :open="showEdit" title="Sửa tương tác thuốc" size="lg" @close="showEdit = false">
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-[#374151]">Mã thuốc 1</label>
            <input v-model="form.drug_id_1" disabled class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm bg-[#F9FAFB] opacity-60" />
          </div>
          <div>
            <label class="text-sm font-medium text-[#374151]">Mã thuốc 2</label>
            <input v-model="form.drug_id_2" disabled class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm bg-[#F9FAFB] opacity-60" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-[#374151]">Mức độ</label>
            <AppSelect v-model="form.severity" :options="severityFormOptions" class="mt-1 w-full" />
          </div>
          <div>
            <label class="text-sm font-medium text-[#374151]">Loại tương tác</label>
            <input v-model="form.interaction_type" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Mô tả</label>
          <textarea v-model="form.description" rows="3" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981] resize-none" />
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Khuyến nghị</label>
          <textarea v-model="form.recommendation" rows="2" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981] resize-none" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="outline" @click="showEdit = false">Hủy</AppButton>
        <AppButton :loading="updating" @click="doEdit">Lưu thay đổi</AppButton>
      </template>
    </AppModal>

    <AppConfirmDialog
      :open="confirmState.open"
      title="Xóa tương tác thuốc"
      :message="`Bạn có chắc muốn xóa tương tác '${confirmState.label}'?`"
      confirm-label="Xóa"
      :danger="true"
      :loading="deleting"
      @confirm="doDelete"
      @cancel="confirmState.open = false"
    />
  </div>
</template>
