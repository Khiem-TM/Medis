<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { usePrescriptions, useCreatePrescriptionMutation, useDeletePrescriptionMutation, useCompleteEarlyMutation } from '@/api/prescriptions.api'
import { useRecommendationMutation } from '@/api/recommendations.api'
import type { DrugSuggestion } from '@/api/recommendations.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { prescriptionSchema } from '@/schemas/prescription.schema'
import { formatDate } from '@/utils/format'
import type { PrescriptionSearchParams, MedicationType } from '@/types/prescription.types'
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
const activeTab = ref<'' | MedicationType>('')
const deletingId = ref<string | null>(null)

const queryParams = computed<PrescriptionSearchParams>(() => ({
  ...paginationParams.value,
  search: search.value || undefined,
  status: statusFilter.value || undefined,
  medication_type: activeTab.value || undefined,
}))

const { data, isLoading } = usePrescriptions(queryParams)
const { mutate: createPrescription, isPending: creating } = useCreatePrescriptionMutation()
const { mutate: deletePrescription, isPending: deleting } = useDeletePrescriptionMutation()
const { mutate: completeEarly, isPending: completingEarly } = useCompleteEarlyMutation()
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
  medication_type: 'periodic' as MedicationType,
  start_date: '',
  end_date: '',
  items: [{ market_product_id: undefined as number | undefined, drug_id: undefined as string | undefined, drug_name: '', dosage: '', frequency: '', duration: '', selected_product: null as MarketDrugProduct | null, is_ai_suggestion: false }],
})

function resetForm() {
  form.name = ''
  form.notes = ''
  form.status = 'active'
  form.medication_type = 'periodic'
  form.start_date = ''
  form.end_date = ''
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
    medication_type: form.medication_type,
    start_date: form.start_date || undefined,
    end_date: form.end_date || undefined,
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

function handleCompleteEarly(id: string) {
  completeEarly(id, {
    onSuccess: () => toast.success('Đã kết thúc sớm đơn thuốc'),
    onError: (e) => toast.error((e as { message?: string })?.message || 'Không thể kết thúc sớm'),
  })
}

function ringColor(days: number | null): string {
  if (days === null) return '#10B981'
  if (days <= 3) return '#EF4444'
  if (days <= 7) return '#F59E0B'
  return '#10B981'
}

const statusOptions = [
  { label: 'Tất cả', value: '' },
  { label: 'Đang dùng', value: 'active' },
  { label: 'Hoàn thành', value: 'completed' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-start justify-between flex-wrap gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-widest mb-1" style="color:#00685d;">Đơn thuốc của tôi</p>
        <h1 class="text-3xl font-extrabold" style="color:#0A0F1E;">Đơn Thuốc</h1>
        <p class="text-sm mt-1" style="color:#4B5563;">Theo dõi các đơn đang dùng và lịch sử điều trị</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-semibold transition-all hover:bg-gray-50"
          style="border-color:rgba(15,23,42,0.15);color:#1F2937;"
          @click="router.push('/schedule')"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          Đồng bộ
        </button>
        <button
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-95"
          style="background:linear-gradient(135deg,#00685d,#00897B);box-shadow:0 4px 14px rgba(0,104,93,0.28);"
          @click="showModal = true; resetForm()"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Tạo đơn mới
        </button>
      </div>
    </div>

    <!-- Filters bar -->
    <div class="flex flex-wrap items-center gap-2">
      <!-- Status tabs -->
      <div class="flex gap-1">
        <button
          v-for="[k, l] in [['', 'Tất cả'], ['active', 'Đang dùng'], ['completed', 'Hoàn thành']]"
          :key="k"
          @click="statusFilter = k as '' | 'active' | 'completed'"
          class="px-4 py-2 rounded-full text-sm font-semibold transition-all"
          :style="statusFilter === k
            ? 'background:#00685d;color:white;'
            : 'background:rgba(15,23,42,0.05);color:#4B5563;'"
        >{{ l }}</button>
      </div>

      <!-- Type chips -->
      <div class="flex gap-2">
        <button
          v-for="[k, l] in [['', 'Mọi loại'], ['chronic', 'Mãn tính'], ['periodic', 'Định kỳ']]"
          :key="k"
          @click="activeTab = k as '' | MedicationType"
          class="px-4 py-2 rounded-full text-sm font-medium border transition-all"
          :style="activeTab === k
            ? 'background:rgba(237,233,254,0.6);border-color:rgba(124,58,237,0.35);color:#7C3AED;font-weight:600;'
            : 'background:white;border-color:rgba(15,23,42,0.12);color:#4B5563;'"
        >{{ l }}</button>
      </div>

      <span class="text-sm ml-auto font-medium" style="color:#6B7280;" v-if="!isLoading && data">{{ data.meta.total }} đơn</span>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <AppSkeleton v-for="i in 4" :key="i" class="h-52 rounded-2xl" />
    </div>

    <!-- Empty -->
    <div v-else-if="!data?.items.length" class="flex flex-col items-center justify-center py-20 rounded-2xl border" style="background:white;border-color:rgba(15,23,42,0.08);">
      <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style="background:rgba(0,104,93,0.08);">
        <svg class="w-8 h-8" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      </div>
      <p class="text-base font-semibold mb-1" style="color:#0A0F1E;">Chưa có đơn thuốc nào</p>
      <p class="text-sm mb-4" style="color:#6B7280;">Thêm đơn mới để bắt đầu theo dõi lịch uống và kiểm tra tương tác.</p>
      <button
        class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
        style="background:linear-gradient(135deg,#00685d,#00897B);"
        @click="showModal = true; resetForm()"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Tạo đơn đầu tiên
      </button>
    </div>

    <!-- Card grid — 2 columns -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="row in data.items"
        :key="(row as any).id"
        class="rounded-2xl border bg-white cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5 overflow-hidden"
        style="border-color:rgba(15,23,42,0.1);box-shadow:0 1px 4px rgba(15,23,42,0.05);"
        @click="router.push(`/profile/prescriptions/${(row as any).id}`)"
      >
        <!-- Card body -->
        <div class="p-5">
          <!-- Icon + Name -->
          <div class="flex items-start gap-3 mb-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style="background:#EDE9FE;">
              <svg class="w-6 h-6" style="color:#7C3AED;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <p class="font-bold text-base leading-snug" style="color:#0A0F1E;">{{ (row as any).name }}</p>
                <svg class="w-4 h-4 flex-shrink-0 mt-0.5" style="color:#9CA3AF;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
              </div>
              <div class="flex items-center gap-2 mt-2 flex-wrap">
                <span
                  class="px-2.5 py-0.5 rounded-full text-xs font-semibold border"
                  :style="(row as any).medication_type === 'chronic'
                    ? 'background:rgba(237,233,254,0.7);border-color:rgba(124,58,237,0.3);color:#7C3AED;'
                    : 'background:rgba(219,234,254,0.7);border-color:rgba(59,130,246,0.3);color:#2563EB;'"
                >{{ (row as any).medication_type === 'chronic' ? 'Mãn tính' : 'Định kỳ' }}</span>
                <span
                  class="px-2.5 py-0.5 rounded-full text-xs font-semibold flex items-center gap-1.5"
                  :style="(row as any).status === 'active'
                    ? 'background:rgba(209,250,229,0.8);color:#059669;'
                    : 'background:rgba(243,244,246,1);color:#6B7280;'"
                >
                  <span v-if="(row as any).status === 'active'" class="w-1.5 h-1.5 rounded-full inline-block" style="background:#10B981;" />
                  {{ (row as any).status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Date + count + ring -->
          <div class="flex items-end justify-between gap-3">
            <div class="space-y-1.5 flex-1 min-w-0">
              <div class="flex items-center gap-2 text-sm" style="color:#4B5563;">
                <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                <span v-if="(row as any).end_date">
                  <span class="font-semibold" style="color:#0A0F1E;">{{ formatDate((row as any).start_date) }}</span>
                  <span class="mx-1 text-gray-400">→</span>
                  <span class="font-semibold" style="color:#0A0F1E;">{{ formatDate((row as any).end_date) }}</span>
                </span>
                <span v-else-if="(row as any).start_date">
                  Từ <span class="font-semibold" style="color:#0A0F1E;">{{ formatDate((row as any).start_date) }}</span>
                  <span class="ml-1" style="color:#9CA3AF;">· Không thời hạn</span>
                </span>
                <span v-else style="color:#9CA3AF;">Chưa có thời hạn</span>
              </div>
              <div class="flex items-center gap-2 text-sm" style="color:#4B5563;">
                <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                <span><strong style="color:#0A0F1E;">{{ (row as any).drug_count ?? 0 }} loại thuốc</strong> trong đơn</span>
              </div>
            </div>

            <!-- Progress ring -->
            <div v-if="(row as any).status === 'active' && (row as any).days_remaining !== null" class="flex-shrink-0">
              <svg width="62" height="62" viewBox="0 0 62 62">
                <circle cx="31" cy="31" r="25" fill="white" stroke="rgba(15,23,42,0.07)" stroke-width="5"/>
                <circle
                  cx="31" cy="31" r="25" fill="none"
                  :stroke="ringColor((row as any).days_remaining)"
                  stroke-width="5"
                  stroke-linecap="round"
                  :stroke-dasharray="`${Math.max(0, ((row as any).days_remaining / Math.max((row as any).days_total || 30, 1)) * 157.1).toFixed(1)} 157.1`"
                  transform="rotate(-90 31 31)"
                />
                <text x="31" y="28" text-anchor="middle" font-size="13" font-weight="800" :fill="ringColor((row as any).days_remaining)">{{ (row as any).days_remaining }}</text>
                <text x="31" y="39" text-anchor="middle" font-size="7" fill="#9CA3AF" font-weight="600" letter-spacing="0.3">NGÀY</text>
              </svg>
            </div>
            <div v-else-if="(row as any).status === 'completed'" class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style="background:rgba(16,185,129,0.1);">
              <svg class="w-5 h-5" style="color:#059669;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
            </div>
          </div>
        </div>

        <!-- Card footer -->
        <div class="flex items-center justify-between px-5 py-3 border-t" style="border-color:rgba(15,23,42,0.07);">
          <div>
            <span
              v-if="(row as any).interaction_check?.has_interaction"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border"
              style="background:rgba(254,243,199,0.6);border-color:rgba(245,158,11,0.35);color:#D97706;"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              Có tương tác
            </span>
          </div>
          <span class="text-sm font-medium" style="color:#9CA3AF;">Xem chi tiết →</span>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="data?.meta && data.meta.total_pages > 1" class="bg-white rounded-2xl border px-5" style="border-color:rgba(15,23,42,0.08);">
      <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
    </div>

    <!-- Create modal -->
    <AppModal :open="showModal" title="Tạo đơn thuốc mới" size="lg" @close="showModal = false">
      <form @submit.prevent="submitForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.name" label="Tên đơn thuốc" placeholder="VD: Đơn thuốc tháng 4" :error="formErrors.name" required />
          <AppSelect v-model="form.status" label="Trạng thái" :options="[{ label: 'Đang dùng', value: 'active' }, { label: 'Hoàn thành', value: 'completed' }]" />
        </div>
        <AppSelect
          v-model="form.medication_type"
          label="Loại thuốc"
          :options="[{ label: 'Theo kỳ (điều trị ngắn hạn, có hạn)', value: 'periodic' }, { label: 'Thường xuyên (mạn tính / bổ sung)', value: 'chronic' }]"
        />
        <div v-if="form.medication_type === 'periodic'" class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.start_date" type="date" label="Ngày bắt đầu" />
          <AppInput v-model="form.end_date" type="date" label="Ngày kết thúc" :error="formErrors.end_date" />
        </div>
        <AppTextarea v-model="form.notes" label="Ghi chú" placeholder="Ghi chú thêm..." :rows="2" />

        <!-- AI suggestion panel -->
        <div class="rounded-xl border overflow-hidden" style="border-color:rgba(0,104,93,0.2);background:rgba(0,104,93,0.03);">
          <button
            type="button"
            class="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold transition-colors"
            style="color:#00685d;"
            @click="showSuggestionPanel = !showSuggestionPanel"
          >
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.347.347a3.75 3.75 0 01-5.303 0l-.347-.347z"/></svg>
              Gợi ý thuốc bằng AI
            </span>
            <svg class="w-4 h-4 transition-transform" :class="showSuggestionPanel ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </button>

          <div v-if="showSuggestionPanel" class="px-4 pb-4 space-y-3 border-t" style="border-color:rgba(0,104,93,0.1);">
            <p class="text-xs mt-3" style="color:#6B7280;">Nhập triệu chứng hoặc tên bệnh để AI gợi ý thuốc phù hợp</p>
            <div class="flex gap-2">
              <textarea
                v-model="symptoms"
                rows="2"
                placeholder="VD: Đau đầu, sốt nhẹ, ho khan..."
                class="flex-1 rounded-xl border px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 transition-all"
                style="border-color:rgba(15,23,42,0.12);color:#0A0F1E;"
                @keydown.enter.ctrl.prevent="fetchSuggestions"
              />
              <AppButton type="button" variant="gradient" :loading="loadingSuggestions" :disabled="!symptoms.trim()" class="self-end" @click="fetchSuggestions">Gợi ý</AppButton>
            </div>
            <div v-if="suggestions.length" class="space-y-2">
              <p class="text-xs font-medium" style="color:#4B5563;">{{ suggestions.length }} gợi ý từ AI:</p>
              <div
                v-for="(s, idx) in suggestions"
                :key="idx"
                class="flex items-start gap-3 rounded-xl border p-3 transition-colors"
                :style="addedSuggestionIndices.has(idx)
                  ? 'border-color:rgba(16,185,129,0.3);background:rgba(16,185,129,0.04);'
                  : 'border-color:rgba(15,23,42,0.1);background:white;'"
              >
                <div class="flex-1 min-w-0 space-y-0.5">
                  <p class="text-sm font-semibold truncate" style="color:#0A0F1E;">{{ s.drug_name }}</p>
                  <p class="text-xs truncate" style="color:#6B7280;">{{ s.active_ingredient }}</p>
                  <p class="text-xs truncate" style="color:#00685d;">{{ s.indication }}</p>
                  <p v-if="s.reference_dosage" class="text-xs" style="color:#4B5563;">Liều: {{ s.reference_dosage }}</p>
                  <p v-if="s.warnings" class="text-xs mt-0.5" style="color:#EF4444;">{{ s.warnings }}</p>
                </div>
                <div class="flex flex-col items-end gap-2 flex-shrink-0">
                  <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                    :style="s.suitability_score >= 80 ? 'background:rgba(16,185,129,0.1);color:#059669;' : s.suitability_score >= 60 ? 'background:rgba(245,158,11,0.1);color:#D97706;' : 'background:rgba(107,114,128,0.1);color:#6B7280;'"
                  >{{ s.suitability_score }}%</span>
                  <button v-if="!addedSuggestionIndices.has(idx)" type="button" class="text-xs font-medium px-2.5 py-1 rounded-lg border transition-colors" style="color:#00685d;border-color:rgba(0,104,93,0.25);" @click="addSuggestionToItems(s, idx)">+ Thêm</button>
                  <span v-else class="text-xs font-medium" style="color:#059669;">Đã thêm</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Drug items -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-semibold" style="color:#0A0F1E;">Danh sách thuốc <span style="color:#EF4444;">*</span></label>
            <button type="button" @click="addItem" class="text-sm font-semibold" style="color:#00685d;">+ Thêm thuốc</button>
          </div>
          <p v-if="formErrors.items" class="text-xs mb-2" style="color:#EF4444;">{{ formErrors.items }}</p>
          <div v-for="(item, i) in form.items" :key="i" class="flex gap-2 items-start border rounded-xl p-3 mb-2" style="border-color:rgba(15,23,42,0.1);background:rgba(15,23,42,0.02);">
            <div class="flex-1 grid grid-cols-2 gap-2">
              <div class="col-span-2">
                <div v-if="item.is_ai_suggestion" class="flex items-center gap-2 rounded-xl border px-3 py-2" style="border-color:rgba(0,104,93,0.25);background:rgba(0,104,93,0.04);">
                  <svg class="w-4 h-4 flex-shrink-0" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.347.347a3.75 3.75 0 01-5.303 0l-.347-.347z"/></svg>
                  <span class="text-sm font-semibold flex-1 truncate" style="color:#0A0F1E;">{{ item.drug_name }}</span>
                  <span class="text-xs font-medium px-1.5 py-0.5 rounded-md" style="color:#00685d;background:rgba(0,104,93,0.1);">AI</span>
                  <button type="button" class="text-xs ml-1" style="color:#6B7280;" @click="item.drug_name = ''; item.drug_id = undefined; item.is_ai_suggestion = false">Đổi</button>
                </div>
                <MarketDrugSearchField v-else :model-value="item.selected_product" placeholder="Nhập tên thuốc hoặc chọn từ gợi ý *" @update:model-value="onSelectDrug(i, $event)" @update:customText="item.drug_name = $event; item.market_product_id = undefined" />
                <p v-if="formErrors[`items.${i}.drug_name`]" class="text-xs mt-1" style="color:#EF4444;">{{ formErrors[`items.${i}.drug_name`] }}</p>
              </div>
              <AppInput v-model="item.dosage" placeholder="Liều dùng *" :error="formErrors[`items.${i}.dosage`]" />
              <AppInput v-model="item.frequency" placeholder="Tần suất (VD: 2 lần/ngày)" />
              <AppInput v-model="item.duration" placeholder="Thời gian (VD: 7 ngày)" />
            </div>
            <button type="button" @click="removeItem(i)" class="mt-1 p-1 flex-shrink-0 transition-colors" style="color:#9CA3AF;">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
        </div>
      </form>

      <template #footer>
        <AppButton variant="ghost" @click="showModal = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="creating" @click="submitForm">Tạo đơn thuốc</AppButton>
      </template>
    </AppModal>

    <AppConfirmDialog :open="confirmOpen" title="Xóa đơn thuốc" message="Bạn có chắc muốn xóa đơn thuốc này? Hành động này không thể hoàn tác." danger :loading="deleting" @confirm="onConfirm" @cancel="onCancel" />
  </div>
</template>
