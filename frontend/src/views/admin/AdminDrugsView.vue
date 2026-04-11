<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDrugSearch, useDrugDetail, useCreateDrugMutation, useUpdateDrugMutation, useDeleteDrugMutation } from '@/api/drugs.api'
import { usePagination } from '@/composables/usePagination'
import { useDebounce } from '@/composables/useDebounce'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import type { DrugSearchParams, CreateDrugRequest, UpdateDrugRequest } from '@/types/drug.types'
import AppTable from '@/components/ui/AppTable.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'

const router = useRouter()
const toast = useToast()
const confirm = useConfirm()

const { page, size, params: paginationParams, setPage, setSize } = usePagination(20)
const searchInput = ref('')
const debouncedSearch = useDebounce(searchInput, 400)

const queryParams = computed<DrugSearchParams>(() => ({
  ...paginationParams.value,
  search: debouncedSearch.value || undefined,
}))

const { data, isLoading } = useDrugSearch(queryParams)
const { mutate: createDrug, isPending: creating } = useCreateDrugMutation()
const { mutate: updateDrug, isPending: updating } = useUpdateDrugMutation()
const { mutate: deleteDrug, isPending: deleting } = useDeleteDrugMutation()

// Create modal
const showCreate = ref(false)
const createForm = ref<CreateDrugRequest>({ id: '', name: '', atc_code: '', description: '', dosage_form: '', classification: '' })

// Edit modal
const showEdit = ref(false)
const editId = ref('')
const editForm = ref<UpdateDrugRequest>({ name: '', atc_code: '', description: '', dosage_form: '', classification: '' })

// Confirm delete
const confirmState = ref({ open: false, id: '', name: '' })

const columns = [
  { key: 'name', label: 'Tên thuốc' },
  { key: 'atc_code', label: 'Mã ATC' },
  { key: 'dosage_form', label: 'Dạng bào chế' },
  { key: 'classification', label: 'Phân loại' },
  { key: 'actions', label: '', align: 'right' as const },
]

function openCreate() {
  createForm.value = { id: '', name: '', atc_code: '', description: '', dosage_form: '', classification: '' }
  showCreate.value = true
}

function doCreate() {
  const data = { ...createForm.value }
  if (!data.id || !data.name) return
  createDrug(data, {
    onSuccess: () => { toast.success('Đã tạo thuốc'); showCreate.value = false },
    onError: () => toast.error('Không thể tạo thuốc'),
  })
}

function openEdit(row: any) {
  editId.value = row.id
  editForm.value = { name: row.name, atc_code: row.atc_code, description: row.description, dosage_form: row.dosage_form, classification: row.classification }
  showEdit.value = true
}

function doEdit() {
  updateDrug({ id: editId.value, data: editForm.value }, {
    onSuccess: () => { toast.success('Đã cập nhật'); showEdit.value = false },
    onError: () => toast.error('Không thể cập nhật'),
  })
}

function openDelete(row: any) {
  confirmState.value = { open: true, id: row.id, name: row.name }
}

function doDelete() {
  deleteDrug(confirmState.value.id, {
    onSuccess: () => { toast.success('Đã xóa thuốc'); confirmState.value.open = false },
    onError: () => toast.error('Không thể xóa'),
  })
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-[#111827]">Quản lý thuốc</h1>
        <p class="text-sm text-[#6B7280] mt-1">Thêm, sửa, xóa danh mục thuốc</p>
      </div>
      <AppButton @click="openCreate">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Thêm thuốc
      </AppButton>
    </div>

    <!-- Search -->
    <div class="bg-white p-3 rounded-xl border border-[#E5E7EB]">
      <AppInput v-model="searchInput" placeholder="Tìm tên thuốc, mã ATC..." class="w-full max-w-md">
        <template #prefix>
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </template>
      </AppInput>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
      <div class="px-4 py-3 border-b border-[#E5E7EB]">
        <p class="text-sm text-[#6B7280]">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} thuốc</template>
          <template v-else>Đang tải...</template>
        </p>
      </div>

      <AppTable :columns="columns" :data="(data?.items ?? []) as any[]" :loading="isLoading" empty-message="Không tìm thấy thuốc">
        <template #name="{ row }">
          <button class="text-left hover:text-[#10B981] font-medium transition-colors text-sm" @click="router.push(`/drugs/${row.id}`)">
            {{ row.name }}
          </button>
        </template>
        <template #atc_code="{ row }">
          <span class="font-mono text-xs">{{ row.atc_code ?? '—' }}</span>
        </template>
        <template #dosage_form="{ row }">{{ row.dosage_form ?? '—' }}</template>
        <template #classification="{ row }">{{ row.classification ?? '—' }}</template>
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

    <!-- Create modal -->
    <AppModal :open="showCreate" title="Thêm thuốc mới" size="lg" @close="showCreate = false">
      <div class="space-y-3">
        <div>
          <label class="text-sm font-medium text-[#374151]">Mã thuốc (ID) *</label>
          <input v-model="createForm.id" placeholder="vd: DRUG001" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Tên thuốc *</label>
          <input v-model="createForm.name" placeholder="Tên hoạt chất" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-[#374151]">Mã ATC</label>
            <input v-model="createForm.atc_code" placeholder="vd: A01AA01" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
          <div>
            <label class="text-sm font-medium text-[#374151]">Dạng bào chế</label>
            <input v-model="createForm.dosage_form" placeholder="vd: Viên nén" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Phân loại</label>
          <input v-model="createForm.classification" placeholder="vd: Thuốc kê đơn" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Mô tả</label>
          <textarea v-model="createForm.description" rows="3" placeholder="Mô tả thuốc..." class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981] resize-none" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="outline" @click="showCreate = false">Hủy</AppButton>
        <AppButton :disabled="!createForm.id || !createForm.name" :loading="creating" @click="doCreate">Tạo thuốc</AppButton>
      </template>
    </AppModal>

    <!-- Edit modal -->
    <AppModal :open="showEdit" title="Sửa thông tin thuốc" size="lg" @close="showEdit = false">
      <div class="space-y-3">
        <div>
          <label class="text-sm font-medium text-[#374151]">Tên thuốc</label>
          <input v-model="editForm.name" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-[#374151]">Mã ATC</label>
            <input v-model="editForm.atc_code" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
          <div>
            <label class="text-sm font-medium text-[#374151]">Dạng bào chế</label>
            <input v-model="editForm.dosage_form" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Phân loại</label>
          <input v-model="editForm.classification" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
        </div>
        <div>
          <label class="text-sm font-medium text-[#374151]">Mô tả</label>
          <textarea v-model="editForm.description" rows="3" class="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981] resize-none" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="outline" @click="showEdit = false">Hủy</AppButton>
        <AppButton :loading="updating" @click="doEdit">Lưu thay đổi</AppButton>
      </template>
    </AppModal>

    <!-- Confirm delete -->
    <AppConfirmDialog
      :open="confirmState.open"
      title="Xóa thuốc"
      :message="`Bạn có chắc muốn xóa thuốc '${confirmState.name}'? Hành động này không thể hoàn tác.`"
      confirm-label="Xóa"
      :danger="true"
      :loading="deleting"
      @confirm="doDelete"
      @cancel="confirmState.open = false"
    />
  </div>
</template>
