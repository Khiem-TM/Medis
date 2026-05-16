<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { usePrescriptions, useCreatePrescriptionMutation, useDeletePrescriptionMutation } from '@/api/prescriptions.api'
import { useRecommendationMutation } from '@/api/recommendations.api'
import type { DrugSuggestion } from '@/api/recommendations.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { prescriptionSchema } from '@/schemas/prescription.schema'
import { formatDate } from '@/utils/format'
import type { PrescriptionSearchParams } from '@/types/prescription.types'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
import MarketDrugSearchField from '@/components/drug/MarketDrugSearchField.vue'
import type { MarketDrugProduct } from '@/types/market-drug.types'

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
const { mutate: getRecommendations, isPending: loadingSuggestions } = useRecommendationMutation()

const showModal = ref(false)
const formErrors = reactive<Record<string, string>>({})
const symptoms = ref('')
const suggestions = ref<DrugSuggestion[]>([])
const showSuggestionPanel = ref(false)
const addedSuggestionIndices = ref<Set<number>>(new Set())
const form = reactive({
  name: '',
  notes: '',
  status: 'active' as 'active' | 'completed',
  items: [{ market_product_id: undefined as number | undefined, drug_id: undefined as string | undefined, drug_name: '', dosage: '', frequency: '', duration: '', selected_product: null as MarketDrugProduct | null, is_ai_suggestion: false }],
})

function resetForm() {
  form.name = ''
  form.notes = ''
  form.status = 'active'
  form.items = [{ market_product_id: undefined, drug_id: undefined, drug_name: '', dosage: '', frequency: '', duration: '', selected_product: null, is_ai_suggestion: false }]
  Object.keys(formErrors).forEach((k) => delete formErrors[k])
  symptoms.value = ''
  suggestions.value = []
  showSuggestionPanel.value = false
  addedSuggestionIndices.value = new Set()
}

function fetchSuggestions() {
  if (!symptoms.value.trim()) return
  getRecommendations({ symptoms: symptoms.value }, {
    onSuccess: (result) => {
      suggestions.value = result.suggestions
      addedSuggestionIndices.value = new Set()
    },
    onError: () => toast.error('Không thể lấy gợi ý thuốc. Vui lòng thử lại.'),
  })
}

function addSuggestionToItems(s: DrugSuggestion, idx: number) {
  const emptyIdx = form.items.findIndex(it => !it.drug_name && !it.market_product_id)
  const item = {
    market_product_id: undefined as number | undefined,
    drug_id: s.drug_id ?? undefined,
    drug_name: s.drug_name,
    dosage: s.reference_dosage || '',
    frequency: '',
    duration: '',
    selected_product: null as MarketDrugProduct | null,
    is_ai_suggestion: true,
  }
  if (emptyIdx >= 0) {
    form.items[emptyIdx] = item
  } else {
    form.items.push(item)
  }
  addedSuggestionIndices.value = new Set([...addedSuggestionIndices.value, idx])
}

function addItem() {
  form.items.push({ market_product_id: undefined, drug_id: undefined, drug_name: '', dosage: '', frequency: '', duration: '', selected_product: null, is_ai_suggestion: false })
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
    if (e instanceof z.ZodError) {
      e.issues.forEach((err) => {
        if (err.path.length) formErrors[err.path.join('.')] = err.message
      })
    }
    return false
  }
}

function submitForm() {
  if (!validateForm()) return
  const payload = {
    name: form.name,
    notes: form.notes,
    status: form.status,
    items: form.items.map((item) => ({
      market_product_id: item.market_product_id,
      drug_id: item.drug_id,
      drug_name: item.drug_name,
      dosage: item.dosage,
      frequency: item.frequency,
      duration: item.duration,
    })),
  }
  createPrescription(payload, {
    onSuccess: (response) => {
      if (response.interaction_check?.has_interaction) {
        toast.warning(`Đơn thuốc đã tạo. Phát hiện ${response.interaction_check.interactions.length} tương tác cần lưu ý.`)
      } else if (response.interaction_check?.message) {
        toast.info(response.interaction_check.message)
      } else {
        toast.success('Tạo đơn thuốc thành công')
      }
      showModal.value = false
      resetForm()
    },
    onError: (e) => toast.error((e as { message?: string })?.message || 'Tạo đơn thuốc thất bại'),
  })
}

function onSelectDrug(index: number, product: MarketDrugProduct | null) {
  const item = form.items[index]
  if (!item) return
  item.selected_product = product
  item.market_product_id = product?.id
  item.drug_name = product?.product_name ?? ''
  item.drug_id = product?.resolved_drug_ids.length === 1 ? product.resolved_drug_ids[0] : undefined
  item.is_ai_suggestion = false
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

const statusOptions = [
  { label: 'Tất cả', value: '' },
  { label: 'Đang dùng', value: 'active' },
  { label: 'Hoàn thành', value: 'completed' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-on-surface">Đơn thuốc</h1>
        <p class="text-sm text-outline mt-0.5">Quản lý các đơn thuốc của bạn</p>
      </div>
      <AppButton variant="gradient" @click="showModal = true; resetForm()">
        <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Tạo đơn thuốc
      </AppButton>
    </div>

    <!-- Schedule quick-link banner -->
    <div
      class="bg-gradient-to-r from-primary-fixed to-surface-container-high rounded-2xl border border-primary/20 p-4 flex items-center gap-4 cursor-pointer hover:shadow-md transition-shadow"
      @click="router.push('/schedule')"
    >
      <div class="w-10 h-10 rounded-xl bg-primary flex items-center justify-center flex-shrink-0">
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-semibold text-on-surface">Lịch uống thuốc</p>
        <p class="text-xs text-outline mt-0.5">Đặt nhắc nhở uống thuốc theo đơn của bạn</p>
      </div>
      <svg class="w-4 h-4 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
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
            v-model="search"
            type="text"
            placeholder="Tìm kiếm đơn thuốc..."
            class="w-full pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          />
        </div>
        <select
          v-model="statusFilter"
          class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <div class="ml-auto flex items-center text-sm text-outline">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} đơn thuốc</template>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="p-5 space-y-3">
        <AppSkeleton v-for="i in 4" :key="i" class="h-14 rounded-xl" />
      </div>

      <!-- Empty -->
      <div v-else-if="!data?.items.length" class="text-center py-16">
        <svg class="w-10 h-10 text-outline/40 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-sm text-outline">Chưa có đơn thuốc nào</p>
        <button class="mt-2 text-sm text-primary hover:underline" @click="showModal = true; resetForm()">Tạo đơn thuốc đầu tiên</button>
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Tên đơn thuốc</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-center">Số thuốc</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-center">Trạng thái</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Ngày tạo</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/50">
            <tr
              v-for="row in data.items"
              :key="(row as any).id"
              class="hover:bg-surface-container-low/50 transition-colors"
            >
              <td class="px-5 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-secondary-container flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <span class="text-sm font-semibold text-on-surface">{{ (row as any).name }}</span>
                </div>
              </td>
              <td class="px-5 py-4 text-center">
                <span class="text-sm font-bold text-on-surface-variant">{{ (row as any).drug_count ?? 0 }}</span>
              </td>
              <td class="px-5 py-4 text-center">
                <span :class="[
                  'px-2.5 py-0.5 rounded-full text-xs font-bold',
                  (row as any).status === 'active'
                    ? 'bg-tertiary-fixed text-tertiary'
                    : 'bg-surface-container text-outline',
                ]">
                  {{ (row as any).status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}
                </span>
              </td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">{{ formatDate((row as any).created_at) }}</td>
              <td class="px-5 py-4">
                <div class="flex items-center gap-2 justify-end">
                  <button
                    @click="router.push(`/profile/prescriptions/${(row as any).id}`)"
                    class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
                  >
                    Xem
                  </button>
                  <button
                    @click="deleteItem((row as any).id)"
                    :disabled="deleting && deletingId === (row as any).id"
                    class="px-3 py-1.5 text-xs font-medium text-error border border-error/30 rounded-lg hover:bg-error hover:text-white transition-colors disabled:opacity-50"
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
    <AppModal :open="showModal" title="Tạo đơn thuốc mới" size="lg" @close="showModal = false">
      <form @submit.prevent="submitForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.name" label="Tên đơn thuốc" placeholder="VD: Đơn thuốc tháng 4" :error="formErrors.name" required />
          <AppSelect v-model="form.status" label="Trạng thái" :options="[{ label: 'Đang dùng', value: 'active' }, { label: 'Hoàn thành', value: 'completed' }]" />
        </div>
        <AppTextarea v-model="form.notes" label="Ghi chú" placeholder="Ghi chú thêm..." :rows="2" />

        <!-- AI suggestion panel -->
        <div class="rounded-xl border border-primary/20 bg-primary-fixed/30 overflow-hidden">
          <button
            type="button"
            class="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-primary hover:bg-primary/5 transition-colors"
            @click="showSuggestionPanel = !showSuggestionPanel"
          >
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.347.347a3.75 3.75 0 01-5.303 0l-.347-.347z" />
              </svg>
              Gợi ý thuốc bằng AI
            </span>
            <svg
              class="w-4 h-4 transition-transform"
              :class="showSuggestionPanel ? 'rotate-180' : ''"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-if="showSuggestionPanel" class="px-4 pb-4 space-y-3 border-t border-primary/10">
            <p class="text-xs text-outline mt-3">Nhập triệu chứng hoặc tên bệnh để AI gợi ý thuốc phù hợp</p>
            <div class="flex gap-2">
              <textarea
                v-model="symptoms"
                rows="2"
                placeholder="VD: Đau đầu, sốt nhẹ, ho khan..."
                class="flex-1 rounded-xl border border-outline-variant bg-surface px-3 py-2 text-sm text-on-surface placeholder:text-outline resize-none focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                @keydown.enter.ctrl.prevent="fetchSuggestions"
              />
              <AppButton
                type="button"
                variant="gradient"
                :loading="loadingSuggestions"
                :disabled="!symptoms.trim()"
                class="self-end"
                @click="fetchSuggestions"
              >
                Gợi ý
              </AppButton>
            </div>

            <!-- Suggestion results -->
            <div v-if="suggestions.length" class="space-y-2">
              <p class="text-xs font-medium text-on-surface-variant">{{ suggestions.length }} gợi ý từ AI:</p>
              <div
                v-for="(s, idx) in suggestions"
                :key="idx"
                class="flex items-start gap-3 rounded-xl border p-3 transition-colors"
                :class="addedSuggestionIndices.has(idx)
                  ? 'border-tertiary/30 bg-tertiary-fixed/20'
                  : 'border-outline-variant bg-surface hover:bg-surface-container-low'"
              >
                <div class="flex-1 min-w-0 space-y-0.5">
                  <p class="text-sm font-semibold text-on-surface truncate">{{ s.drug_name }}</p>
                  <p class="text-xs text-outline truncate">{{ s.active_ingredient }}</p>
                  <p class="text-xs text-primary truncate">{{ s.indication }}</p>
                  <p v-if="s.reference_dosage" class="text-xs text-on-surface-variant">Liều: {{ s.reference_dosage }}</p>
                  <p v-if="s.warnings" class="text-xs text-error mt-0.5">⚠ {{ s.warnings }}</p>
                </div>
                <div class="flex flex-col items-end gap-2 flex-shrink-0">
                  <span
                    class="text-xs font-bold px-2 py-0.5 rounded-full"
                    :class="s.suitability_score >= 80
                      ? 'bg-tertiary-fixed text-tertiary'
                      : s.suitability_score >= 60
                        ? 'bg-secondary-container text-secondary'
                        : 'bg-surface-container text-outline'"
                  >
                    {{ s.suitability_score }}%
                  </span>
                  <button
                    v-if="!addedSuggestionIndices.has(idx)"
                    type="button"
                    class="text-xs font-medium text-primary border border-primary/30 rounded-lg px-2.5 py-1 hover:bg-primary hover:text-white transition-colors"
                    @click="addSuggestionToItems(s, idx)"
                  >
                    + Thêm
                  </button>
                  <span v-else class="text-xs text-tertiary font-medium">✓ Đã thêm</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Drug items -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-medium text-on-surface">Danh sách thuốc <span class="text-error">*</span></label>
            <button type="button" @click="addItem" class="text-sm text-primary hover:underline font-medium">+ Thêm thuốc</button>
          </div>
          <p v-if="formErrors.items" class="text-xs text-error mb-2">{{ formErrors.items }}</p>

          <div v-for="(item, i) in form.items" :key="i" class="flex gap-2 items-start border border-outline-variant rounded-xl p-3 mb-2 bg-surface-container-low">
            <div class="flex-1 grid grid-cols-2 gap-2">
              <div class="col-span-2">
                <!-- AI-suggested drug (no market product linked yet) -->
                <div v-if="item.is_ai_suggestion" class="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary-fixed/20 px-3 py-2">
                  <svg class="w-4 h-4 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.347.347a3.75 3.75 0 01-5.303 0l-.347-.347z" />
                  </svg>
                  <span class="text-sm font-semibold text-on-surface flex-1 truncate">{{ item.drug_name }}</span>
                  <span class="text-xs text-primary bg-primary/10 px-1.5 py-0.5 rounded-md font-medium">AI</span>
                  <button type="button" class="text-xs text-outline hover:text-primary ml-1" @click="item.drug_name = ''; item.drug_id = undefined; item.is_ai_suggestion = false">Đổi</button>
                </div>
                <MarketDrugSearchField
                  v-else
                  :model-value="item.selected_product"
                  placeholder="Nhập tên thuốc hoặc chọn từ gợi ý *"
                  @update:model-value="onSelectDrug(i, $event)"
                  @update:customText="item.drug_name = $event; item.market_product_id = undefined"
                />
                <p v-if="formErrors[`items.${i}.drug_name`]" class="text-xs text-error mt-1">{{ formErrors[`items.${i}.drug_name`] }}</p>
              </div>
              <AppInput v-model="item.dosage" placeholder="Liều dùng *" :error="formErrors[`items.${i}.dosage`]" />
              <AppInput v-model="item.frequency" placeholder="Tần suất (VD: 2 lần/ngày)" />
              <AppInput v-model="item.duration" placeholder="Thời gian (VD: 7 ngày)" />
            </div>
            <button type="button" @click="removeItem(i)" class="mt-1 text-outline hover:text-error p-1 flex-shrink-0 transition-colors">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </form>

      <template #footer>
        <AppButton variant="ghost" @click="showModal = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="creating" @click="submitForm">Tạo đơn thuốc</AppButton>
      </template>
    </AppModal>

    <!-- Confirm delete -->
    <AppConfirmDialog :open="confirmOpen" title="Xóa đơn thuốc" message="Bạn có chắc muốn xóa đơn thuốc này? Hành động này không thể hoàn tác." danger :loading="deleting" @confirm="onConfirm" @cancel="onCancel" />
  </div>
</template>
