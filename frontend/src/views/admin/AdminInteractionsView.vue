<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAdminInteractions, useCreateInteractionMutation, useUpdateInteractionMutation, useDeleteInteractionMutation } from '@/api/interactions.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import type { AdminInteractionSearchParams, CreateInteractionRequest, DrugInteraction } from '@/types/interaction.types'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'

const toast = useToast()
const { page, size, params: paginationParams, setPage, setSize } = usePagination(20)
const drugIdFilter = ref('')

const queryParams = computed<AdminInteractionSearchParams>(() => ({
  ...paginationParams.value,
  drug_id: drugIdFilter.value || undefined,
}))

const { data, isLoading } = useAdminInteractions(queryParams)
const { mutate: createInteraction, isPending: creating } = useCreateInteractionMutation()
const { mutate: updateInteraction, isPending: updating } = useUpdateInteractionMutation()
const { mutate: deleteInteraction, isPending: deleting } = useDeleteInteractionMutation()

const defaultForm = (): CreateInteractionRequest => ({
  drug_id: '',
  interacts_with_id: '',
  interacts_with_name: '',
})

const showCreate = ref(false)
const showEdit = ref(false)
const editingPair = ref({ drug_id: '', interacts_with_id: '' })
const form = ref(defaultForm())
const confirmState = ref({ open: false, drug_id: '', interacts_with_id: '', label: '' })

function interactionKey(row: DrugInteraction) {
  return `${row.drug_id}:${row.interacts_with_id}`
}

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

function openEdit(row: DrugInteraction) {
  editingPair.value = { drug_id: row.drug_id, interacts_with_id: row.interacts_with_id }
  form.value = {
    drug_id: row.drug_id,
    interacts_with_id: row.interacts_with_id,
    interacts_with_name: row.interacts_with_name ?? '',
  }
  showEdit.value = true
}

function doEdit() {
  updateInteraction({
    drug_id: editingPair.value.drug_id,
    interacts_with_id: editingPair.value.interacts_with_id,
    data: { interacts_with_name: form.value.interacts_with_name },
  }, {
    onSuccess: () => { toast.success('Đã cập nhật'); showEdit.value = false },
    onError: () => toast.error('Cập nhật thất bại'),
  })
}

function openDelete(row: DrugInteraction) {
  confirmState.value = {
    open: true,
    drug_id: row.drug_id,
    interacts_with_id: row.interacts_with_id,
    label: `${row.drug_id} ↔ ${row.interacts_with_id}`,
  }
}

function doDelete() {
  deleteInteraction({
    drug_id: confirmState.value.drug_id,
    interacts_with_id: confirmState.value.interacts_with_id,
  }, {
    onSuccess: () => { toast.success('Đã xóa'); confirmState.value.open = false },
    onError: () => toast.error('Xóa thất bại'),
  })
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-on-surface">Quản lý tương tác thuốc</h1>
        <p class="text-sm text-outline mt-0.5">Thêm, sửa, xóa các cặp tương tác thuốc đã biết</p>
      </div>
      <button
        @click="openCreate"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-gradient-to-r from-primary to-primary-container text-white rounded-xl hover:opacity-90 transition-opacity"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Thêm tương tác
      </button>
    </div>

    <!-- Table card -->
    <div class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
      <!-- Filter bar -->
      <div class="px-5 py-4 border-b border-outline-variant flex flex-wrap gap-3 bg-card">
        <select
          v-model="drugIdFilter"
          class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          <option value="">Tất cả thuốc</option>
        </select>
        <input
          v-model="drugIdFilter"
          placeholder="Lọc theo DrugBank ID"
          class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
        <div class="ml-auto flex items-center text-sm text-outline">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} cặp tương tác</template>
        </div>
      </div>

      <!-- Table -->
      <div v-if="isLoading" class="p-5 space-y-3">
        <AppSkeleton v-for="i in 5" :key="i" class="h-12 rounded-xl" />
      </div>
      <div v-else-if="!data?.items.length" class="text-center py-16">
        <p class="text-sm text-outline">Không có tương tác nào</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Thuốc nguồn</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Tương tác với</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Nhãn tương tác</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Nguồn</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Độ tin cậy</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/50">
            <tr
              v-for="row in data.items"
              :key="interactionKey(row)"
              class="hover:bg-surface-container-low/50 transition-colors"
            >
              <td class="px-5 py-4">
                <span class="text-sm font-mono font-medium text-on-surface">{{ row.drug_name || row.drug_id }}</span>
              </td>
              <td class="px-5 py-4">
                <span class="text-sm font-mono font-medium text-on-surface">{{ row.interacts_with_name || row.interacts_with_id }}</span>
              </td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">
                {{ row.interaction_label ?? '—' }}
              </td>
              <td class="px-5 py-4">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-surface-container text-outline">
                  {{ row.source ?? 'database' }}
                </span>
              </td>
              <td class="px-5 py-4">
                <span class="text-sm text-on-surface-variant">
                  {{ row.confidence_score != null ? `${(row.confidence_score * 100).toFixed(1)}%` : '—' }}
                </span>
              </td>
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
    <AppModal :open="showCreate" title="Thêm tương tác thuốc" size="lg" @close="showCreate = false">
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Mã thuốc nguồn <span class="text-error">*</span></label>
            <input v-model="form.drug_id" placeholder="ID thuốc nguồn" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
          </div>
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Mã thuốc tương tác <span class="text-error">*</span></label>
            <input v-model="form.interacts_with_id" placeholder="ID thuốc tương tác" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Tên thuốc tương tác</label>
          <input v-model="form.interacts_with_name" placeholder="Tên hiển thị" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="showCreate = false">Hủy</AppButton>
        <AppButton variant="gradient" :disabled="!form.drug_id || !form.interacts_with_id" :loading="creating" @click="doCreate">Tạo</AppButton>
      </template>
    </AppModal>

    <!-- Edit modal -->
    <AppModal :open="showEdit" title="Sửa tương tác thuốc" size="lg" @close="showEdit = false">
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Mã thuốc nguồn</label>
            <input v-model="form.drug_id" disabled class="w-full rounded-xl border border-outline-variant bg-surface-container px-3 py-2.5 text-sm text-outline opacity-70" />
          </div>
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Mã thuốc tương tác</label>
            <input v-model="form.interacts_with_id" disabled class="w-full rounded-xl border border-outline-variant bg-surface-container px-3 py-2.5 text-sm text-outline opacity-70" />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Tên thuốc tương tác</label>
          <input v-model="form.interacts_with_name" class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
        </div>
      </div>
      <template #footer>
        <AppButton variant="ghost" @click="showEdit = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="updating" @click="doEdit">Lưu thay đổi</AppButton>
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
