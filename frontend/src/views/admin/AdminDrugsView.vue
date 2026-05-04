<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDrugSearch, useCreateDrugMutation, useUpdateDrugMutation, useDeleteDrugMutation } from '@/api/drugs.api'
import { usePagination } from '@/composables/usePagination'
import { useDebounce } from '@/composables/useDebounce'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import type { DrugSearchParams, CreateDrugRequest, UpdateDrugRequest } from '@/types/drug.types'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppButton from '@/components/ui/AppButton.vue'
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

const showCreate = ref(false)
const createForm = ref<CreateDrugRequest>({ id: '', name: '', atc_code: '', description: '', dosage_form: '', classification: '' })

const showEdit = ref(false)
const editId = ref('')
const editForm = ref<UpdateDrugRequest>({ name: '', atc_code: '', description: '', dosage_form: '', classification: '' })

const confirmState = ref({ open: false, id: '', name: '' })

function openCreate() {
  createForm.value = { id: '', name: '', atc_code: '', description: '', dosage_form: '', classification: '' }
  showCreate.value = true
}

function doCreate() {
  const d = { ...createForm.value }
  if (!d.id || !d.name) return
  createDrug(d, {
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
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-on-surface">Quản lý thuốc</h1>
        <p class="text-sm text-outline mt-0.5">Thêm, sửa, xóa danh mục thuốc</p>
      </div>
      <button
        @click="openCreate"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-gradient-to-r from-primary to-primary-container text-white rounded-xl hover:opacity-90 transition-opacity"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Thêm thuốc
      </button>
    </div>

    <!-- Table card -->
    <div class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
      <!-- Filter bar -->
      <div class="px-5 py-4 border-b border-outline-variant flex flex-wrap gap-3 bg-card">
        <div class="relative flex-1 min-w-48">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-outline pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchInput"
            type="text"
            placeholder="Tìm tên thuốc, mã ATC..."
            class="w-full pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          />
        </div>
        <div class="ml-auto flex items-center text-sm text-outline">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} thuốc</template>
        </div>
      </div>

      <!-- Table -->
      <div v-if="isLoading" class="p-5 space-y-3">
        <AppSkeleton v-for="i in 5" :key="i" class="h-12 rounded-xl" />
      </div>
      <div v-else-if="!data?.items.length" class="text-center py-16">
        <p class="text-sm text-outline">Không tìm thấy thuốc</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Tên thuốc</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Mã ATC</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Dạng bào chế</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Phân loại</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/50">
            <tr
              v-for="row in data.items"
              :key="row.id"
              class="hover:bg-surface-container-low/50 transition-colors"
            >
              <td class="px-5 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-primary-fixed flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
                    </svg>
                  </div>
                  <button
                    class="text-sm font-semibold text-on-surface hover:text-primary transition-colors text-left"
                    @click="router.push(`/drugs/${row.id}`)"
                  >
                    {{ row.name }}
                  </button>
                </div>
              </td>
              <td class="px-5 py-4">
                <code v-if="row.atc_code" class="text-xs bg-surface-container px-2 py-0.5 rounded font-mono text-on-surface-variant">{{ row.atc_code }}</code>
                <span v-else class="text-outline">—</span>
              </td>
              <td class="px-5 py-4">
                <span v-if="row.dosage_form" class="text-xs bg-primary-fixed text-primary px-2.5 py-0.5 rounded-full font-medium">{{ row.dosage_form }}</span>
                <span v-else class="text-sm text-outline">—</span>
              </td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">{{ row.classification ?? '—' }}</td>
              <td class="px-5 py-4">
                <div class="flex items-center gap-2 justify-end">
                  <button
                    @click="openEdit(row)"
                    class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
                  >
                    Sửa
                  </button>
                  <button
                    @click="openDelete(row)"
                    class="px-3 py-1.5 text-xs font-medium text-error border border-error/30 rounded-lg hover:bg-error hover:text-white transition-colors"
                  >
                    Xóa
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="data?.meta" class="px-5 border-t border-outline-variant">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>

    <!-- Create modal -->
    <AppModal :open="showCreate" title="Thêm thuốc mới" size="lg" @close="showCreate = false">
      <div class="space-y-3">
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Mã thuốc (ID) <span class="text-error">*</span></label>
          <input v-model="createForm.id" placeholder="vd: DRUG001" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Tên thuốc <span class="text-error">*</span></label>
          <input v-model="createForm.name" placeholder="Tên hoạt chất" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Mã ATC</label>
            <input v-model="createForm.atc_code" placeholder="vd: A01AA01" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
          </div>
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Dạng bào chế</label>
            <input v-model="createForm.dosage_form" placeholder="vd: Viên nén" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Phân loại</label>
          <input v-model="createForm.classification" placeholder="vd: Thuốc kê đơn" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Mô tả</label>
          <textarea v-model="createForm.description" rows="3" placeholder="Mô tả thuốc..." class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="showCreate = false">Hủy</AppButton>
        <AppButton variant="gradient" :disabled="!createForm.id || !createForm.name" :loading="creating" @click="doCreate">Tạo thuốc</AppButton>
      </template>
    </AppModal>

    <!-- Edit modal -->
    <AppModal :open="showEdit" title="Sửa thông tin thuốc" size="lg" @close="showEdit = false">
      <div class="space-y-3">
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Tên thuốc</label>
          <input v-model="editForm.name" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Mã ATC</label>
            <input v-model="editForm.atc_code" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
          </div>
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Dạng bào chế</label>
            <input v-model="editForm.dosage_form" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Phân loại</label>
          <input v-model="editForm.classification" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Mô tả</label>
          <textarea v-model="editForm.description" rows="3" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="showEdit = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="updating" @click="doEdit">Lưu thay đổi</AppButton>
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
