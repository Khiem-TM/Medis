<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useInteractionCheckMutation } from '@/api/interactions.api'
import { marketDrugsApi } from '@/api/market-drugs.api'
import type { MarketInteractionCheckResult } from '@/api/market-drugs.api'
import { drugsApi } from '@/api/drugs.api'
import { useExcelExport } from '@/composables/useExcelExport'
import { useDebounce } from '@/composables/useDebounce'
import type { DrugListItem } from '@/types/drug.types'
import type { InteractionCheckResult } from '@/types/interaction.types'
import type { MarketDrugProduct } from '@/types/market-drug.types'
import DrugSearchCombobox from '@/components/drug/DrugSearchCombobox.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'

const route = useRoute()

// ── Mode ─────────────────────────────────────────────────────────────────────
type Mode = 'market' | 'generic'
const mode = ref<Mode>('market')

// ── Generic mode state ────────────────────────────────────────────────────────
const selectedDrugs = ref<DrugListItem[]>([])
const genericResult = ref<InteractionCheckResult | null>(null)
const { mutate: checkGeneric, isPending: checkingGeneric, error: genericError } = useInteractionCheckMutation()
const { exporting, exportExcel } = useExcelExport()

// ── Market mode state ─────────────────────────────────────────────────────────
const selectedProducts = ref<MarketDrugProduct[]>([])
const marketQuery = ref('')
const marketDebounced = useDebounce(marketQuery, 300)
const marketSearchResults = ref<MarketDrugProduct[]>([])
const marketSearchLoading = ref(false)
const marketSearchOpen = ref(false)
const marketResult = ref<MarketInteractionCheckResult | null>(null)
const marketChecking = ref(false)
const marketError = ref<string | null>(null)

// ── Computed ──────────────────────────────────────────────────────────────────
const canCheckGeneric = computed(() => selectedDrugs.value.length >= 2)
const canCheckMarket = computed(() => selectedProducts.value.length >= 2)
const genericErrorMessage = computed(() => {
  const e = genericError.value as { message?: string } | null
  return e?.message || null
})

// Unified result for display — both modes produce InteractionCheckResult-shaped data
const activeResult = computed<InteractionCheckResult | null>(() => {
  if (mode.value === 'generic') return genericResult.value
  return marketResult.value?.ddi_result ?? null
})

const interactionCount = computed(() => activeResult.value?.interactions.length ?? 0)
const safeCount = computed(() => activeResult.value?.safe_pairs.length ?? 0)
const mlCount = computed(() => activeResult.value?.prediction_count ?? 0)

// ── onMounted: read query params ──────────────────────────────────────────────
onMounted(async () => {
  const queryMode = route.query.mode as string | undefined
  const drugId = route.query.drug as string | undefined
  const productId = route.query.product_id as string | undefined

  if (queryMode === 'market' || productId) {
    mode.value = 'market'
    if (productId) {
      try {
        const product = await marketDrugsApi.get(Number(productId))
        if (!selectedProducts.value.find((p) => p.id === product.id)) {
          selectedProducts.value.push(product as MarketDrugProduct)
        }
      } catch { /* ignore */ }
    }
  } else if (drugId) {
    mode.value = 'generic'
    try {
      const drug = await drugsApi.get(drugId)
      selectedDrugs.value = [{
        id: drug.id,
        generic_name: drug.generic_name,
        name: drug.generic_name,
        atc_code: drug.atc_codes?.[0] ?? null,
        description: drug.description,
        dosage_form: drug.dosage_forms?.[0] ?? null,
        classification: drug.categories?.[0] ?? null,
      }]
    } catch { /* ignore */ }
  }
})

// ── Market search ─────────────────────────────────────────────────────────────
watch(marketDebounced, async (q) => {
  if (!q || q.length < 1) {
    marketSearchResults.value = []
    marketSearchOpen.value = false
    return
  }
  marketSearchLoading.value = true
  try {
    const data = await marketDrugsApi.search({ search: q, size: 8 })
    marketSearchResults.value = data.items.filter(
      (p) => !selectedProducts.value.find((s) => s.id === p.id),
    )
    marketSearchOpen.value = marketSearchResults.value.length > 0
  } catch {
    marketSearchResults.value = []
  } finally {
    marketSearchLoading.value = false
  }
})

function addProduct(product: MarketDrugProduct) {
  if (selectedProducts.value.length >= 10) return
  if (!selectedProducts.value.find((p) => p.id === product.id)) {
    selectedProducts.value.push(product)
  }
  marketQuery.value = ''
  marketSearchResults.value = []
  marketSearchOpen.value = false
}

function removeProduct(id: number) {
  selectedProducts.value = selectedProducts.value.filter((p) => p.id !== id)
}

function onMarketBlur() {
  setTimeout(() => { marketSearchOpen.value = false }, 150)
}

// ── Actions ───────────────────────────────────────────────────────────────────
function doGenericCheck() {
  genericResult.value = null
  checkGeneric(selectedDrugs.value.map((d) => d.id), {
    onSuccess: (data) => { genericResult.value = data },
  })
}

function getErrorMessage(error: unknown) {
  if (typeof error === 'object' && error !== null) {
    const maybeAxios = error as { response?: { data?: { detail?: string } }; message?: string }
    return maybeAxios.response?.data?.detail || maybeAxios.message || 'Đã xảy ra lỗi'
  }
  return 'Đã xảy ra lỗi'
}

async function doMarketCheck() {
  if (!canCheckMarket.value) return
  marketChecking.value = true
  marketError.value = null
  marketResult.value = null
  try {
    marketResult.value = await marketDrugsApi.checkInteractions(
      selectedProducts.value.map((p) => p.id),
    )
  } catch (error) {
    marketError.value = getErrorMessage(error)
  } finally {
    marketChecking.value = false
  }
}

function doExport() {
  exportExcel('/interactions/check/export', { drug_ids: selectedDrugs.value.map((d) => d.id) }, 'tuong-tac-thuoc.xlsx')
}

function formatConfidence(score: number | undefined) {
  if (!score) return ''
  return `${(score * 100).toFixed(1)}%`
}

function printResult() {
  window.print()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-on-surface">Kiểm tra tương tác thuốc</h1>
      <p class="text-sm text-outline mt-0.5">Chọn từ 2 thuốc trở lên để kiểm tra tương tác. Hệ thống tích hợp AI dự đoán tương tác.</p>
    </div>

    <!-- Mode tabs -->
    <div class="flex gap-1 p-1 rounded-xl w-fit" style="background: #F3F5F7;">
      <button
        type="button"
        class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
        :class="mode === 'market'
          ? 'bg-white shadow-sm text-on-surface'
          : 'text-outline hover:text-on-surface'"
        @click="mode = 'market'; activeResult"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
        Thuốc thương mại
      </button>
      <button
        type="button"
        class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
        :class="mode === 'generic'
          ? 'bg-white shadow-sm text-on-surface'
          : 'text-outline hover:text-on-surface'"
        @click="mode = 'generic'"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
        </svg>
        Hoạt chất (generic)
      </button>
    </div>

    <!-- ── Market mode input ── -->
    <div v-if="mode === 'market'" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
      <div class="flex items-center gap-4 mb-5">
        <div class="w-10 h-10 bg-primary-fixed rounded-xl flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-bold text-on-surface">Thuốc thương mại</h2>
          <p class="text-sm text-outline">Tìm theo tên thương mại hoặc số đăng ký (tối đa 10 sản phẩm)</p>
        </div>
      </div>

      <!-- Selected products -->
      <div v-if="selectedProducts.length > 0" class="space-y-2 mb-4">
        <div
          v-for="product in selectedProducts"
          :key="product.id"
          class="flex items-center gap-3 rounded-xl border border-outline-variant bg-surface px-3 py-2"
        >
          <img
            v-if="product.image_url"
            :src="product.image_url"
            :alt="product.product_name"
            class="w-10 h-10 rounded-lg object-contain border border-outline-variant bg-white flex-shrink-0"
          />
          <div class="w-10 h-10 rounded-lg border border-outline-variant bg-surface-container-low flex-shrink-0 flex items-center justify-center" v-else>
            <svg class="w-5 h-5 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-on-surface truncate">{{ product.product_name }}</p>
            <p class="text-xs text-outline truncate">{{ [product.registration_number, product.dosage_form].filter(Boolean).join(' · ') }}</p>
          </div>
          <button type="button" class="p-1 rounded-lg hover:bg-error-container text-outline hover:text-error transition-colors flex-shrink-0" @click="removeProduct(product.id)">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Search field -->
      <div v-if="selectedProducts.length < 10" class="relative">
        <div class="flex items-center gap-2 rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2 focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary transition-all">
          <svg class="w-4 h-4 text-outline flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="marketQuery"
            class="flex-1 bg-transparent outline-none text-sm text-on-surface placeholder:text-outline"
            placeholder="Tìm thuốc thương mại để thêm..."
            @focus="marketSearchOpen = marketSearchResults.length > 0"
            @blur="onMarketBlur"
          />
          <AppSpinner v-if="marketSearchLoading" size="sm" class="text-primary" />
        </div>

        <div v-if="marketSearchOpen" class="absolute top-full left-0 right-0 mt-1 bg-card border border-outline-variant rounded-xl shadow-lg z-30 overflow-hidden max-h-64 overflow-y-auto">
          <button
            v-for="product in marketSearchResults"
            :key="product.id"
            type="button"
            class="w-full text-left px-4 py-3 hover:bg-surface-container-low transition-colors"
            @mousedown.prevent="addProduct(product)"
          >
            <div class="flex gap-3 items-center">
              <img v-if="product.image_url" :src="product.image_url" :alt="product.product_name" class="w-9 h-9 rounded-lg object-contain border border-outline-variant bg-white flex-shrink-0" />
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-on-surface truncate">{{ product.product_name }}</p>
                <p class="text-xs text-outline truncate">{{ [product.registration_number, product.dosage_form].filter(Boolean).join(' · ') }}</p>
              </div>
              <span v-if="product.is_expired" class="text-xs text-error flex-shrink-0">Hết hạn</span>
            </div>
          </button>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap items-center gap-3">
        <AppButton variant="gradient" :disabled="!canCheckMarket" :loading="marketChecking" size="lg" @click="doMarketCheck">
          <template v-if="!marketChecking">
            <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Chạy phân tích tương tác
          </template>
        </AppButton>
      </div>

      <div v-if="marketError" class="mt-4 p-3 bg-error-container border border-error/20 rounded-xl text-sm text-error">{{ marketError }}</div>

      <!-- Unmapped warning -->
      <div
        v-if="marketResult && marketResult.unmapped_products.length > 0"
        class="mt-4 p-3 rounded-xl text-sm flex items-start gap-2"
        style="background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E;"
      >
        <svg class="w-4 h-4 flex-shrink-0 mt-0.5" style="color: #D97706;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        {{ marketResult.unmapped_products.length }} sản phẩm chưa được mapping sang DDI, bỏ qua khỏi phân tích.
      </div>
    </div>

    <!-- ── Generic mode input ── -->
    <div v-else class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
      <div class="flex items-center gap-4 mb-6">
        <div class="w-10 h-10 bg-primary-fixed rounded-xl flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-bold text-on-surface">Hoạt chất (generic drug)</h2>
          <p class="text-sm text-outline">Thêm các hoạt chất từ cơ sở dữ liệu DDI để phân tích tương tác</p>
        </div>
      </div>

      <DrugSearchCombobox v-model="selectedDrugs" :max="20" placeholder="Tìm và thêm hoạt chất..." />

      <div class="mt-6 flex flex-wrap items-center gap-3">
        <AppButton variant="gradient" :disabled="!canCheckGeneric" :loading="checkingGeneric" size="lg" @click="doGenericCheck">
          <template v-if="!checkingGeneric">
            <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Chạy phân tích tương tác
          </template>
        </AppButton>
        <AppButton v-if="genericResult" variant="outline" :loading="exporting" @click="doExport">
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Xuất Excel
        </AppButton>
      </div>

      <div v-if="genericErrorMessage" class="mt-4 p-3 bg-error-container border border-error/20 rounded-xl text-sm text-error">{{ genericErrorMessage }}</div>
    </div>

    <!-- Loading -->
    <div v-if="checkingGeneric || marketChecking" class="bg-card rounded-2xl border border-outline-variant p-12 flex flex-col items-center gap-4">
      <AppSpinner size="lg" class="text-primary" />
      <p class="text-sm text-outline">Đang phân tích tương tác thuốc. Vui lòng đợi...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="!activeResult" class="bg-card rounded-2xl border border-outline-variant p-12 text-center">
      <div class="w-16 h-16 bg-surface-container rounded-2xl flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      </div>
      <p class="text-sm font-medium text-on-surface">Chọn ít nhất 2 thuốc để kiểm tra</p>
      <p class="text-xs text-outline mt-1">Kết quả phân tích tương tác sẽ hiển thị tại đây</p>
    </div>

    <!-- ── Shared results ── -->
    <template v-else>
      <div class="flex flex-wrap items-center justify-between gap-4">
        <h3 class="text-lg font-bold text-on-surface">Kết quả phân tích</h3>
        <div class="flex flex-wrap gap-3">
          <div v-if="interactionCount > 0" class="flex items-center gap-2 px-3 py-1 bg-error-container text-error rounded-full text-xs font-bold uppercase tracking-wider">
            <span class="w-2 h-2 rounded-full bg-error" />
            {{ interactionCount }} Tương tác
          </div>
          <div v-if="safeCount > 0" class="flex items-center gap-2 px-3 py-1 bg-tertiary-fixed text-tertiary rounded-full text-xs font-bold uppercase tracking-wider">
            <span class="w-2 h-2 rounded-full bg-tertiary" />
            {{ safeCount }} An toàn
          </div>
          <div v-if="mlCount > 0" class="flex items-center gap-2 px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-bold uppercase tracking-wider border border-primary/20">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {{ mlCount }} AI Dự đoán
          </div>
        </div>
      </div>

      <!-- Summary card -->
      <div :class="['rounded-2xl border p-5 flex items-center gap-4', activeResult.has_interaction ? 'bg-error-container/40 border-error/20' : 'bg-tertiary-fixed/40 border-tertiary/20']">
        <div :class="['w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-bold flex-shrink-0', activeResult.has_interaction ? 'bg-error-container text-error' : 'bg-tertiary-fixed text-tertiary']">
          {{ interactionCount }}
        </div>
        <div>
          <p class="font-semibold text-on-surface">{{ activeResult.has_interaction ? 'Phát hiện tương tác thuốc!' : 'Không có tương tác đáng lo ngại' }}</p>
          <p class="text-sm text-outline mt-0.5">{{ interactionCount }} / {{ activeResult.total_pairs }} cặp có tương tác</p>
        </div>
      </div>

      <!-- Interaction cards -->
      <div class="space-y-4">
        <div
          v-for="interaction in activeResult.interactions"
          :key="`${interaction.drug_id}-${interaction.interacts_with_id}`"
          class="bg-card rounded-2xl overflow-hidden border border-outline-variant shadow-sm flex"
        >
          <div class="w-1.5 flex-shrink-0 bg-error" />
          <div class="p-5 flex-1">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div class="flex items-center gap-3">
                <div class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 bg-error-container text-error">
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h4 class="text-base font-extrabold text-error">
                    {{ interaction.drug_name || interaction.drug_id }} × {{ interaction.interacts_with_name || interaction.interacts_with_id }}
                  </h4>
                  <div class="flex items-center gap-2 mt-1">
                    <p class="text-xs font-bold uppercase tracking-wider text-error">Cảnh báo tương tác</p>
                    <span v-if="interaction.source === 'model_predicted'" class="inline-flex items-center gap-1 text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded font-semibold">
                      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      AI Dự đoán ({{ formatConfidence(interaction.confidence_score) }})
                    </span>
                    <span v-else class="inline-flex items-center gap-1 text-[10px] bg-outline-variant/30 text-outline px-2 py-0.5 rounded font-semibold">
                      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                      </svg>
                      Cơ sở dữ liệu
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <p class="text-sm text-on-surface-variant mb-4 leading-relaxed font-medium">{{ interaction.interaction_label }}</p>
            <div v-if="interaction.event_type?.description" class="bg-surface-container-low rounded-xl p-4 flex items-start gap-3 border-l-4 border-outline-variant">
              <svg class="w-4 h-4 text-outline mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <span class="text-xs font-bold text-on-surface block mb-1">Mô tả loại tương tác:</span>
                <span class="text-sm text-on-surface-variant">{{ interaction.event_type.description }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Safe pairs -->
      <details v-if="safeCount > 0" class="bg-card rounded-2xl border border-outline-variant overflow-hidden">
        <summary class="px-5 py-4 cursor-pointer text-sm font-semibold text-on-surface select-none list-none flex items-center justify-between hover:bg-surface-container-low transition-colors">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Cặp thuốc an toàn ({{ safeCount }})
          </div>
          <svg class="w-4 h-4 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="px-5 pb-4 space-y-1 border-t border-outline-variant">
          <div
            v-for="pair in activeResult.safe_pairs"
            :key="`${pair.drug_id_1}-${pair.drug_id_2}`"
            class="flex items-center gap-2 py-2 text-sm text-on-surface-variant"
          >
            <svg class="w-4 h-4 text-tertiary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {{ pair.drug_1_name || pair.drug_id_1 }} ↔ {{ pair.drug_2_name || pair.drug_id_2 }}
          </div>
        </div>
      </details>
    </template>

    <!-- Print FAB -->
    <Teleport to="body">
      <button
        v-if="activeResult"
        class="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-br from-primary to-primary-container text-white rounded-full shadow-lg flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-50"
        title="In kết quả"
        @click="printResult"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
      </button>
    </Teleport>
  </div>
</template>
