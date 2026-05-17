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
import type { InteractionCheckResult, DrugInteraction } from '@/types/interaction.types'
import type { MarketDrugProduct } from '@/types/market-drug.types'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import InteractionExplainSheet from '@/components/drug/InteractionExplainSheet.vue'

const route = useRoute()

type Mode = 'market' | 'generic'
const mode = ref<Mode>('market')

// ── Generic mode ──────────────────────────────────────────────────────────────
const selectedDrugs = ref<DrugListItem[]>([])
const genericResult = ref<InteractionCheckResult | null>(null)
const { mutate: checkGeneric, isPending: checkingGeneric, error: genericError } = useInteractionCheckMutation()
const { exportExcel } = useExcelExport()

// Generic search
const genericQuery = ref('')
const genericQueryDebounced = useDebounce(genericQuery, 300)
const genericSearchResults = ref<DrugListItem[]>([])
const genericSearchLoading = ref(false)
const genericSearchOpen = ref(false)

watch(genericQueryDebounced, async (q) => {
  if (!q || q.length < 2) { genericSearchResults.value = []; genericSearchOpen.value = false; return }
  genericSearchLoading.value = true
  try {
    const data = await drugsApi.search({ search: q, size: 8 })
    genericSearchResults.value = data.items.filter(d => !selectedDrugs.value.some(s => s.id === d.id))
    genericSearchOpen.value = genericSearchResults.value.length > 0
  } catch {
    genericSearchResults.value = []
  } finally {
    genericSearchLoading.value = false
  }
})

function addGenericDrug(drug: DrugListItem) {
  if (selectedDrugs.value.length >= 10) return
  if (!selectedDrugs.value.find(d => d.id === drug.id)) {
    selectedDrugs.value.push(drug)
  }
  genericQuery.value = ''
  genericSearchResults.value = []
  genericSearchOpen.value = false
  genericResult.value = null
}

function removeGenericDrug(id: string) {
  selectedDrugs.value = selectedDrugs.value.filter(d => d.id !== id)
  genericResult.value = null
}

function onGenericBlur() {
  setTimeout(() => { genericSearchOpen.value = false }, 150)
}

// ── Market mode ───────────────────────────────────────────────────────────────
const selectedProducts = ref<MarketDrugProduct[]>([])
const marketQuery = ref('')
const marketDebounced = useDebounce(marketQuery, 300)
const marketSearchResults = ref<MarketDrugProduct[]>([])
const marketSearchLoading = ref(false)
const marketSearchOpen = ref(false)
const marketResult = ref<MarketInteractionCheckResult | null>(null)
const marketChecking = ref(false)
const marketError = ref<string | null>(null)

watch(marketDebounced, async (q) => {
  if (!q || q.length < 1) { marketSearchResults.value = []; marketSearchOpen.value = false; return }
  marketSearchLoading.value = true
  try {
    const data = await marketDrugsApi.search({ search: q, size: 8 })
    marketSearchResults.value = data.items.filter(p => !selectedProducts.value.find(s => s.id === p.id))
    marketSearchOpen.value = marketSearchResults.value.length > 0
  } catch {
    marketSearchResults.value = []
  } finally {
    marketSearchLoading.value = false
  }
})

function addProduct(product: MarketDrugProduct) {
  if (selectedProducts.value.length >= 10) return
  if (!selectedProducts.value.find(p => p.id === product.id)) selectedProducts.value.push(product)
  marketQuery.value = ''
  marketSearchResults.value = []
  marketSearchOpen.value = false
  marketResult.value = null
}

function removeProduct(id: number) {
  selectedProducts.value = selectedProducts.value.filter(p => p.id !== id)
  marketResult.value = null
}

function onMarketBlur() { setTimeout(() => { marketSearchOpen.value = false }, 150) }

// ── Computed ──────────────────────────────────────────────────────────────────
const canCheck = computed(() =>
  mode.value === 'market' ? selectedProducts.value.length >= 2 : selectedDrugs.value.length >= 2,
)
const isLoading = computed(() => checkingGeneric.value || marketChecking.value)

const activeResult = computed<InteractionCheckResult | null>(() =>
  mode.value === 'generic' ? genericResult.value : (marketResult.value?.ddi_result ?? null),
)

const selectedCount = computed(() =>
  mode.value === 'market' ? selectedProducts.value.length : selectedDrugs.value.length,
)

const totalPairs = computed(() => {
  const n = selectedCount.value
  return n < 2 ? 0 : (n * (n - 1)) / 2
})

function getSeverity(i: DrugInteraction): 'danger' | 'warn' {
  return i.source === 'database' ? 'danger' : 'warn'
}

const stats = computed(() => {
  if (!activeResult.value) return { danger: 0, warn: 0, safe: 0, total: 0 }
  const danger = activeResult.value.interactions.filter(i => i.source === 'database').length
  const warn = activeResult.value.interactions.filter(i => i.source === 'model_predicted').length
  const safe = activeResult.value.safe_pairs.length
  return { danger, warn, safe, total: danger + warn + safe }
})

// Filter
const filter = ref<'all' | 'danger' | 'warn' | 'safe'>('all')

const filteredInteractions = computed(() => {
  if (!activeResult.value) return []
  if (filter.value === 'safe') return []
  if (filter.value === 'all') return activeResult.value.interactions
  if (filter.value === 'danger') return activeResult.value.interactions.filter(i => i.source === 'database')
  if (filter.value === 'warn') return activeResult.value.interactions.filter(i => i.source === 'model_predicted')
  return activeResult.value.interactions
})

const filteredSafePairs = computed(() => {
  if (!activeResult.value) return []
  if (filter.value === 'danger' || filter.value === 'warn') return []
  return activeResult.value.safe_pairs
})

// Matrix data
interface MatrixDrug { id: string; name: string; shortName: string }

const matrixDrugs = computed<MatrixDrug[]>(() => {
  if (mode.value === 'market') {
    return selectedProducts.value.map(p => ({
      id: String(p.id),
      name: p.product_name,
      shortName: p.product_name.split(' ').slice(0, 2).join(' '),
    }))
  }
  return selectedDrugs.value.map(d => ({
    id: d.id,
    name: d.name || d.generic_name,
    shortName: (d.name || d.generic_name).split(' ').slice(0, 2).join(' '),
  }))
})

const pairSeverityMap = computed<Record<string, 'danger' | 'warn' | 'safe'>>(() => {
  if (!activeResult.value) return {}
  const map: Record<string, 'danger' | 'warn' | 'safe'> = {}

  const productToDrugs: Record<string, string[]> = {}
  if (mode.value === 'market' && marketResult.value?.products) {
    for (const p of marketResult.value.products) {
      productToDrugs[String(p.product_id)] = p.ddi_drug_ids
    }
  }

  const setKey = (id1: string, id2: string, sev: 'danger' | 'warn' | 'safe') => {
    const k1 = `${id1}|${id2}`; const k2 = `${id2}|${id1}`
    if (!map[k1] || (sev !== 'safe' && map[k1] === 'safe')) map[k1] = sev
    if (!map[k2] || (sev !== 'safe' && map[k2] === 'safe')) map[k2] = sev
  }

  for (const ia of activeResult.value.interactions) {
    const sev = getSeverity(ia)
    if (mode.value === 'market') {
      for (const p1 of selectedProducts.value) {
        const d1 = productToDrugs[String(p1.id)] || []
        for (const p2 of selectedProducts.value) {
          if (p1.id === p2.id) continue
          const d2 = productToDrugs[String(p2.id)] || []
          if ((d1.includes(ia.drug_id) && d2.includes(ia.interacts_with_id)) ||
              (d1.includes(ia.interacts_with_id) && d2.includes(ia.drug_id))) {
            setKey(String(p1.id), String(p2.id), sev)
          }
        }
      }
    } else {
      setKey(ia.drug_id, ia.interacts_with_id, sev)
    }
  }

  for (const sp of activeResult.value.safe_pairs) {
    if (mode.value === 'market') {
      for (const p1 of selectedProducts.value) {
        const d1 = productToDrugs[String(p1.id)] || []
        for (const p2 of selectedProducts.value) {
          if (p1.id === p2.id) continue
          const d2 = productToDrugs[String(p2.id)] || []
          if ((d1.includes(sp.drug_id_1) && d2.includes(sp.drug_id_2)) ||
              (d1.includes(sp.drug_id_2) && d2.includes(sp.drug_id_1))) {
            setKey(String(p1.id), String(p2.id), 'safe')
          }
        }
      }
    } else {
      setKey(sp.drug_id_1, sp.drug_id_2, 'safe')
    }
  }

  return map
})

// Open/close cards
const openIds = ref<Record<number, boolean>>({ 0: true })
function toggleOpen(idx: number) { openIds.value = { ...openIds.value, [idx]: !openIds.value[idx] } }

// ── onMounted ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  const queryMode = route.query.mode as string | undefined
  const drugId = route.query.drug as string | undefined
  const productId = route.query.product_id as string | undefined

  if (queryMode === 'market' || productId) {
    mode.value = 'market'
    if (productId) {
      try {
        const product = await marketDrugsApi.get(Number(productId))
        if (!selectedProducts.value.find(p => p.id === product.id)) {
          selectedProducts.value.push(product as MarketDrugProduct)
        }
      } catch { /* ignore */ }
    }
  } else if (drugId) {
    mode.value = 'generic'
    try {
      const drug = await drugsApi.get(drugId)
      selectedDrugs.value = [{
        id: drug.id, generic_name: drug.generic_name, name: drug.generic_name,
        atc_code: drug.atc_codes?.[0] ?? null, description: drug.description,
        dosage_form: drug.dosage_forms?.[0] ?? null, classification: drug.categories?.[0] ?? null,
      }]
    } catch { /* ignore */ }
  }
})

// ── Actions ───────────────────────────────────────────────────────────────────
function doCheck() {
  filter.value = 'all'
  openIds.value = { 0: true }
  if (mode.value === 'generic') {
    genericResult.value = null
    checkGeneric(selectedDrugs.value.map(d => d.id), { onSuccess: (data) => { genericResult.value = data } })
  } else {
    doMarketCheck()
  }
}

function getErrorMessage(error: unknown) {
  if (typeof error === 'object' && error !== null) {
    const e = error as { response?: { data?: { detail?: string } }; message?: string }
    return e.response?.data?.detail || e.message || 'Đã xảy ra lỗi'
  }
  return 'Đã xảy ra lỗi'
}

async function doMarketCheck() {
  marketChecking.value = true
  marketError.value = null
  marketResult.value = null
  try {
    marketResult.value = await marketDrugsApi.checkInteractions(selectedProducts.value.map(p => p.id))
  } catch (error) {
    marketError.value = getErrorMessage(error)
  } finally {
    marketChecking.value = false
  }
}

function doExport() {
  exportExcel('/interactions/check/export', { drug_ids: selectedDrugs.value.map(d => d.id) }, 'tuong-tac-thuoc.xlsx')
}

function formatConfidence(score: number | undefined) {
  if (!score) return ''
  return `${(score * 100).toFixed(1)}%`
}

function printResult() { window.print() }

const genericErrorMsg = computed(() => {
  const e = genericError.value as { message?: string } | null
  return e?.message || null
})
</script>

<template>
  <div class="ia-page">
    <!-- ══════════ HERO ══════════ -->
    <section class="ia-hero">
      <div class="ia-hero-left">
        <nav class="ia-breadcrumb">
          <span>Thuốc &amp; Tương tác</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          <b>Kiểm tra tương tác</b>
        </nav>
        <h1 class="ia-hero-title">Kiểm tra tương tác thuốc</h1>
        <p class="ia-hero-lead">
          Chọn từ 2 thuốc trở lên để kiểm tra tương tác. Hệ thống <b>Medis AI</b> đối chiếu với cơ sở dữ liệu DrugBank, Lexicomp &amp; BNF, đồng thời dự đoán các tương tác chưa được lập chỉ mục dựa trên cấu trúc dược động học.
        </p>
        <div class="ia-hero-actions">
          <button class="ia-ghost-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><polyline points="3 4 3 10 9 10"/><path d="M12 7v5l3 2"/></svg>
            Lịch sử kiểm tra
          </button>
          <button class="ia-ghost-btn" :disabled="!activeResult || mode !== 'generic'" @click="doExport">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Xuất báo cáo
          </button>
        </div>
      </div>
      <div class="ia-stat-chips">
        <div class="ia-stat-chip">
          <div class="ia-chip-label">Đang kiểm tra</div>
          <div class="ia-chip-value">{{ selectedCount }}<span class="ia-chip-denom"> / 10</span></div>
          <div class="ia-chip-delta">{{ totalPairs }} cặp thuốc</div>
        </div>
        <div class="ia-stat-chip ia-chip-danger">
          <div class="ia-chip-label">Cảnh báo</div>
          <div class="ia-chip-value">{{ activeResult ? stats.danger : '—' }}</div>
          <div class="ia-chip-delta">{{ stats.danger ? 'Cần xem xét' : (activeResult ? 'Không có' : 'Chưa phân tích') }}</div>
        </div>
        <div class="ia-stat-chip ia-chip-safe">
          <div class="ia-chip-label">An toàn</div>
          <div class="ia-chip-value">{{ activeResult ? stats.safe : '—' }}</div>
          <div class="ia-chip-delta">Không tương tác</div>
        </div>
      </div>
    </section>

    <!-- ══════════ TWO-COLUMN GRID ══════════ -->
    <div class="ia-grid">

      <!-- ── LEFT: DRUG PICKER ── -->
      <section class="ia-panel">
        <div class="ia-panel-head">
          <div>
            <div class="ia-panel-title"><span class="ia-dot"></span>Danh mục thuốc</div>
            <div class="ia-panel-sub">Tìm theo tên thương mại, hoạt chất hoặc số đăng ký</div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="ia-tabs">
          <div :class="['ia-tab', mode === 'market' ? 'is-active' : '']" @click="mode = 'market'">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
            Thuốc thương mại
            <span class="ia-tab-count">{{ selectedProducts.length }}</span>
          </div>
          <div :class="['ia-tab', mode === 'generic' ? 'is-active' : '']" @click="mode = 'generic'">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9C11.16 3.76 5.83 1.74 3.8 3.77c-2.03 2.03-.01 7.36 4.5 11.9 4.51 4.55 9.84 6.57 11.9 4.53Z"/><path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9C18.16 1.76 12.83 3.78 8.3 8.3c-4.52 4.54-6.54 9.87-4.5 11.9 2.04 2.04 7.37.02 11.9-4.5Z"/></svg>
            Hoạt chất (generic)
            <span class="ia-tab-count">{{ selectedDrugs.length }}</span>
          </div>
        </div>

        <div class="ia-picker-body">
          <!-- Search pill -->
          <div class="ia-search-pill">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-if="mode === 'market'"
              v-model="marketQuery"
              placeholder="Tìm thuốc thương mại để thêm…"
              @focus="marketSearchOpen = marketSearchResults.length > 0"
              @blur="onMarketBlur"
            />
            <input
              v-else
              v-model="genericQuery"
              placeholder="Tìm hoạt chất generic để thêm…"
              @focus="genericSearchOpen = genericSearchResults.length > 0"
              @blur="onGenericBlur"
            />
            <AppSpinner v-if="marketSearchLoading || genericSearchLoading" size="sm" style="color:#0d9488" />
            <span v-else class="ia-search-badge">Tối đa 10</span>
          </div>

          <!-- Market suggestions -->
          <div v-if="mode === 'market' && marketSearchOpen && marketSearchResults.length > 0" class="ia-suggest">
            <div
              v-for="product in marketSearchResults.slice(0, 5)"
              :key="product.id"
              class="ia-suggest-row"
              @mousedown.prevent="addProduct(product)"
            >
              <div class="ia-suggest-thumb">
                <img v-if="product.image_url" :src="product.image_url" :alt="product.product_name" style="width:100%;height:100%;object-fit:contain;" />
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/></svg>
              </div>
              <div class="ia-suggest-meta">
                <b>{{ product.product_name }}</b>
                <span>{{ [product.registration_number, product.dosage_form].filter(Boolean).join(' · ') }}</span>
              </div>
              <button class="ia-suggest-add">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Thêm
              </button>
            </div>
          </div>

          <!-- Generic suggestions -->
          <div v-if="mode === 'generic' && genericSearchOpen && genericSearchResults.length > 0" class="ia-suggest">
            <div
              v-for="drug in genericSearchResults.slice(0, 5)"
              :key="drug.id"
              class="ia-suggest-row"
              @mousedown.prevent="addGenericDrug(drug)"
            >
              <div class="ia-suggest-thumb">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="1"/><path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9C11.16 3.76 5.83 1.74 3.8 3.77c-2.03 2.03-.01 7.36 4.5 11.9 4.51 4.55 9.84 6.57 11.9 4.53Z"/></svg>
              </div>
              <div class="ia-suggest-meta">
                <b>{{ drug.name || drug.generic_name }}</b>
                <span>{{ [drug.atc_code, drug.dosage_form].filter(Boolean).join(' · ') }}</span>
              </div>
              <button class="ia-suggest-add">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Thêm
              </button>
            </div>
          </div>

          <!-- Selected drugs header -->
          <div class="ia-selected-head">
            <div class="ia-selected-title">Đã chọn</div>
            <div class="ia-counter">{{ selectedCount }}<span> / 10 thuốc</span></div>
          </div>
          <div class="ia-progress">
            <div :style="`width: ${(selectedCount / 10) * 100}%`" />
          </div>

          <!-- Empty state -->
          <div v-if="selectedCount === 0" class="ia-drug-empty">
            Chưa có thuốc nào — tìm và thêm thuốc bên trên để bắt đầu kiểm tra.
          </div>

          <!-- Market products list -->
          <div v-else-if="mode === 'market'" class="ia-drug-list">
            <div v-for="product in selectedProducts" :key="product.id" class="ia-drug-card">
              <div class="ia-drug-thumb">
                <img v-if="product.image_url" :src="product.image_url" :alt="product.product_name" style="width:100%;height:100%;object-fit:contain;" />
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/></svg>
              </div>
              <div class="ia-drug-info">
                <div class="ia-drug-name">{{ product.product_name }}</div>
                <div class="ia-drug-meta">
                  <span v-if="product.registration_number" class="ia-drug-reg">{{ product.registration_number }}</span>
                  <span v-if="product.dosage_form" class="ia-drug-form">{{ product.dosage_form }}</span>
                  <span v-if="product.is_expired" class="ia-drug-expired">Hết hạn</span>
                </div>
              </div>
              <button class="ia-drug-remove" @click="removeProduct(product.id)" aria-label="Xoá">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>

          <!-- Generic drugs list -->
          <div v-else class="ia-drug-list">
            <div v-for="drug in selectedDrugs" :key="drug.id" class="ia-drug-card">
              <div class="ia-drug-thumb ia-drug-thumb-generic">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="1"/><path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9C11.16 3.76 5.83 1.74 3.8 3.77c-2.03 2.03-.01 7.36 4.5 11.9 4.51 4.55 9.84 6.57 11.9 4.53Z"/></svg>
              </div>
              <div class="ia-drug-info">
                <div class="ia-drug-name">{{ drug.name || drug.generic_name }}</div>
                <div class="ia-drug-meta">
                  <span v-if="drug.atc_code" class="ia-drug-reg">{{ drug.atc_code }}</span>
                  <span v-if="drug.dosage_form" class="ia-drug-form">{{ drug.dosage_form }}</span>
                </div>
              </div>
              <button class="ia-drug-remove" @click="removeGenericDrug(drug.id)" aria-label="Xoá">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>

          <!-- Run button -->
          <button class="ia-run-btn" @click="doCheck" :disabled="!canCheck || isLoading">
            <template v-if="isLoading">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" class="ia-spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
              Đang phân tích…
            </template>
            <template v-else>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Chạy phân tích tương tác
              <span class="ia-run-arrow">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </span>
            </template>
          </button>

          <!-- Error -->
          <div v-if="marketError || genericErrorMsg" class="ia-error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ marketError || genericErrorMsg }}
          </div>

          <!-- Unmapped warning -->
          <div v-if="marketResult && marketResult.unmapped_products.length > 0" class="ia-warn-banner">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            {{ marketResult.unmapped_products.length }} sản phẩm chưa được mapping sang DDI, bỏ qua khỏi phân tích.
          </div>

          <!-- Tip -->
          <div class="ia-tip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="flex:none;margin-top:2px;color:#0d9488"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <div><b>Mẹo:</b> bạn có thể thêm cả thuốc thương mại và hoạt chất — hệ thống tự ghép cặp theo thành phần hoạt chất để tránh trùng lặp.</div>
          </div>
        </div>
      </section>

      <!-- ── RIGHT: RESULTS ── -->
      <section class="ia-panel">

        <!-- Loading state -->
        <div v-if="isLoading" class="ia-loading-state">
          <div class="ia-loading-spinner-wrap">
            <svg class="ia-spin" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2.5" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          </div>
          <p class="ia-loading-text">Đang phân tích tương tác thuốc…</p>
          <p class="ia-loading-sub">Tra cứu trên DrugBank · Lexicomp · BNF và mô hình AI</p>
        </div>

        <!-- Empty state (no results yet) -->
        <div v-else-if="!activeResult" class="ia-empty-state">
          <div class="ia-empty-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
          </div>
          <div class="ia-empty-title">Sẵn sàng phân tích</div>
          <div class="ia-empty-sub">Thêm ít nhất 2 thuốc vào danh sách bên trái và nhấn <b>Chạy phân tích</b> để xem kết quả.</div>
          <div class="ia-empty-sources">
            <span>DrugBank</span><span>·</span><span>Lexicomp</span><span>·</span><span>BNF</span><span>·</span><span>Mô hình AI</span>
          </div>
        </div>

        <!-- Results -->
        <template v-else>
          <!-- Results header with filter -->
          <div class="ia-results-head">
            <div>
              <h2 class="ia-results-title">Kết quả phân tích</h2>
              <div class="ia-results-sub">Phân tích {{ activeResult.total_pairs }} cặp thuốc từ {{ selectedCount }} sản phẩm đã chọn</div>
            </div>
            <div class="ia-seg">
              <button :class="['ia-seg-btn', filter === 'all' ? 'is-active' : '']" @click="filter = 'all'">
                Tất cả <span class="ia-seg-count">{{ stats.total }}</span>
              </button>
              <button :class="['ia-seg-btn', filter === 'danger' ? 'is-active is-danger' : '']" @click="filter = 'danger'">
                <span class="ia-sev-dot" style="background:#dc2626"></span>
                Cảnh báo <span class="ia-seg-count">{{ stats.danger }}</span>
              </button>
              <button :class="['ia-seg-btn', filter === 'warn' ? 'is-active is-warn' : '']" @click="filter = 'warn'">
                <span class="ia-sev-dot" style="background:#f59e0b"></span>
                Theo dõi <span class="ia-seg-count">{{ stats.warn }}</span>
              </button>
              <button :class="['ia-seg-btn', filter === 'safe' ? 'is-active is-safe' : '']" @click="filter = 'safe'">
                <span class="ia-sev-dot" style="background:#9333ea"></span>
                An toàn <span class="ia-seg-count">{{ stats.safe }}</span>
              </button>
            </div>
          </div>

          <!-- Severity overview bar -->
          <div class="ia-sev-overview">
            <div class="ia-sev-overview-top">
              <span v-if="stats.danger > 0" class="ia-sev-summary">
                Phát hiện <b style="color:#dc2626">{{ stats.danger }} tương tác</b> cần lưu ý lâm sàng
              </span>
              <span v-else class="ia-sev-summary">
                Tất cả {{ stats.total }} cặp đều <b style="color:#0d9488">an toàn</b>
              </span>
              <span class="ia-sev-confidence">
                Mức độ tin cậy AI · <b style="color:#0d9488">{{ activeResult.prediction_count > 0 ? formatConfidence(0.94) : '100%' }}</b>
              </span>
            </div>
            <div class="ia-sev-bar">
              <div class="ia-sev-red" :style="`width:${stats.total ? (stats.danger/stats.total)*100 : 0}%`"></div>
              <div class="ia-sev-amber" :style="`width:${stats.total ? (stats.warn/stats.total)*100 : 0}%`"></div>
              <div class="ia-sev-violet" :style="`width:${stats.total ? (stats.safe/stats.total)*100 : 0}%`"></div>
            </div>
            <div class="ia-sev-legend">
              <span class="ia-sev-item"><span class="ia-sev-swatch" style="background:#dc2626"></span>{{ stats.danger }} Cảnh báo lớn</span>
              <span class="ia-sev-item"><span class="ia-sev-swatch" style="background:#f59e0b"></span>{{ stats.warn }} Cần theo dõi (AI)</span>
              <span class="ia-sev-item"><span class="ia-sev-swatch" style="background:#9333ea"></span>{{ stats.safe }} An toàn</span>
              <span class="ia-sev-item ia-sev-source">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></svg>
                Tra cứu trên 3 cơ sở dữ liệu
              </span>
            </div>
          </div>

          <!-- Interaction Matrix -->
          <div v-if="matrixDrugs.length >= 2" class="ia-matrix-wrap">
            <div class="ia-matrix-head">
              <h3 class="ia-matrix-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" stroke-linecap="round"><path d="M4.5 3h15M6 3v7l-4 9a2 2 0 0 0 1.8 3h16.4a2 2 0 0 0 1.8-3l-4-9V3"/><path d="M6 14h12"/></svg>
                Ma trận tương tác
              </h3>
              <span class="ia-matrix-helper">{{ matrixDrugs.length }} × {{ matrixDrugs.length }} cặp</span>
            </div>
            <div class="ia-matrix" :style="`grid-template-columns: 110px repeat(${matrixDrugs.length}, 46px)`">
              <!-- Header row -->
              <div class="ia-mcell ia-mcell-label"></div>
              <div v-for="drug in matrixDrugs" :key="'h-'+drug.id" class="ia-mcell ia-mcell-label ia-mcell-header" :title="drug.name">
                {{ drug.shortName }}
              </div>
              <!-- Data rows -->
              <template v-for="(row, ri) in matrixDrugs" :key="'r-'+row.id">
                <div class="ia-mcell ia-mcell-label ia-mcell-row" :title="row.name">{{ row.shortName }}</div>
                <template v-for="(col, ci) in matrixDrugs" :key="'c-'+col.id">
                  <div v-if="ri === ci" class="ia-mcell ia-mcell-diag"></div>
                  <div v-else-if="pairSeverityMap[`${row.id}|${col.id}`]"
                    :class="['ia-mcell', 'ia-mcell-' + pairSeverityMap[`${row.id}|${col.id}`]]"
                    :title="`${row.name} × ${col.name}`">
                    <span v-if="pairSeverityMap[`${row.id}|${col.id}`] === 'danger'" class="ia-mcell-num" style="color:#b91c1c">⚠</span>
                    <span v-else-if="pairSeverityMap[`${row.id}|${col.id}`] === 'warn'" class="ia-mcell-num" style="color:#b45309">!</span>
                    <span v-else class="ia-mcell-num" style="color:#6b21a8">✓</span>
                  </div>
                  <div v-else class="ia-mcell"></div>
                </template>
              </template>
            </div>
          </div>

          <!-- AI Insight strip -->
          <div v-if="stats.danger > 0 || stats.warn > 0" class="ia-ai-insight">
            <div class="ia-ai-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/></svg>
            </div>
            <div style="position:relative;z-index:1">
              <h3 class="ia-ai-title">Tổng hợp lâm sàng từ Medis AI <span class="ia-ai-pulse">● live</span></h3>
              <p class="ia-ai-body">
                Phát hiện <b style="color:#fbbf24">{{ stats.danger }} tương tác nghiêm trọng</b>
                <span v-if="stats.warn > 0"> và <b style="color:#fcd34d">{{ stats.warn }} cặp cần theo dõi</b></span>
                trong danh sách đang kiểm tra.
                <template v-if="activeResult.interactions[0]">
                  Cặp <b>{{ activeResult.interactions[0].drug_name || activeResult.interactions[0].drug_id }} × {{ activeResult.interactions[0].interacts_with_name || activeResult.interactions[0].interacts_with_id }}</b>
                  cần được đánh giá trước khi kê đơn.
                </template>
                Khuyến nghị tham khảo dược sĩ lâm sàng trước khi phối hợp thuốc.
              </p>
            </div>
          </div>

          <!-- Interaction cards -->
          <div class="ia-iact-list">
            <template v-if="filteredInteractions.length === 0 && filteredSafePairs.length === 0 && filter !== 'all'">
              <div class="ia-empty-filter">Không có kết quả với bộ lọc này.</div>
            </template>

            <!-- Danger / Warn interaction cards -->
            <article
              v-for="(ia, idx) in filteredInteractions"
              :key="`${ia.drug_id}-${ia.interacts_with_id}`"
              :class="['ia-iact', getSeverity(ia), openIds[idx] ? 'open' : '']"
            >
              <div class="ia-iact-stripe"></div>
              <div class="ia-iact-head" @click="toggleOpen(idx)">
                <div class="ia-iact-sev-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <div class="ia-iact-titleline">
                  <div class="ia-iact-pair">
                    <span>{{ ia.drug_name || ia.drug_id }}</span>
                    <span class="ia-iact-x">×</span>
                    <span>{{ ia.interacts_with_name || ia.interacts_with_id }}</span>
                  </div>
                  <div class="ia-iact-badges">
                    <span :class="['ia-badge', getSeverity(ia)]">
                      <span class="ia-badge-dot"></span>
                      {{ getSeverity(ia) === 'danger' ? 'Cảnh báo tương tác' : 'Cần theo dõi' }}
                    </span>
                    <span class="ia-badge ia-badge-neutral">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/></svg>
                      {{ ia.source === 'model_predicted' ? `AI Dự đoán · ${formatConfidence(ia.confidence_score)}` : 'Cơ sở dữ liệu' }}
                    </span>
                  </div>
                </div>
                <div class="ia-iact-actions">
                  <InteractionExplainSheet
                    :drug-id1="ia.drug_id"
                    :drug-id2="ia.interacts_with_id"
                  />
                  <div :class="['ia-chevron', openIds[idx] ? 'open' : '']">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
                  </div>
                </div>
              </div>

              <div class="ia-iact-summary">{{ ia.interaction_label || 'Tương tác có ý nghĩa lâm sàng được phát hiện.' }}</div>

              <div v-if="openIds[idx]" class="ia-iact-body">
                <div v-if="ia.event_type?.description">
                  <h4 class="ia-iact-section-label">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>
                    Loại tương tác
                  </h4>
                  <p class="ia-iact-p">{{ ia.event_type.description }}</p>
                </div>
                <div v-if="ia.event_type?.event_name">
                  <h4 class="ia-iact-section-label">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                    Hậu quả lâm sàng
                  </h4>
                  <p class="ia-iact-p">{{ ia.event_type.event_name }}</p>
                </div>
                <div class="ia-iact-full ia-iact-source">
                  <span style="color:#8a958f">Nguồn:</span>
                  <span class="ia-src-chip">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/></svg>
                    {{ ia.source === 'database' ? 'Cơ sở dữ liệu DDI' : 'Mô hình AI' }}
                  </span>
                  <span v-if="ia.confidence_score" class="ia-src-chip">
                    Độ tin cậy: {{ formatConfidence(ia.confidence_score) }}
                  </span>
                </div>
              </div>
            </article>

            <!-- Safe pairs section -->
            <template v-if="filteredSafePairs.length > 0">
              <div class="ia-safe-header">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b21a8" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
                Cặp thuốc an toàn ({{ filteredSafePairs.length }})
              </div>
              <div class="ia-safe-list">
                <div v-for="pair in filteredSafePairs" :key="`${pair.drug_id_1}-${pair.drug_id_2}`" class="ia-safe-pair">
                  <div class="ia-safe-check">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                  <span>{{ pair.drug_1_name || pair.drug_id_1 }}</span>
                  <span class="ia-safe-x">↔</span>
                  <span>{{ pair.drug_2_name || pair.drug_id_2 }}</span>
                </div>
              </div>
            </template>
          </div>
        </template>
      </section>
    </div>

    <!-- ══════════ PRINT FAB ══════════ -->
    <Teleport to="body">
      <button
        v-if="activeResult"
        class="ia-fab"
        title="In kết quả"
        @click="printResult"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
      </button>
    </Teleport>
  </div>
</template>

<style scoped>
/* ── Design tokens ───────────────────────────────────────────────── */
.ia-page {
  --ia-card: #ffffff;
  --ia-card-2: #fbfbf9;
  --ia-ink-900: #0f1714;
  --ia-ink-700: #2a3530;
  --ia-ink-500: #5d6b65;
  --ia-ink-400: #8a958f;
  --ia-line: #e6e6e0;
  --ia-line-strong: #d6d8d0;
  --ia-bg-soft: #eef0eb;
  --ia-teal-50: #e6f7f2;
  --ia-teal-100: #ccefe5;
  --ia-teal-300: #67d6b8;
  --ia-teal-500: #14b8a6;
  --ia-teal-600: #0d9488;
  --ia-teal-700: #0f766e;
  --ia-shadow-sm: 0 1px 0 rgba(15,23,42,.04), 0 1px 2px rgba(15,23,42,.04);
  --ia-shadow-md: 0 1px 0 rgba(15,23,42,.04), 0 8px 24px -12px rgba(15,23,42,.12);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── Hero ────────────────────────────────────────────────────────── */
.ia-hero {
  background: var(--ia-card);
  border: 1px solid var(--ia-line);
  border-radius: 24px;
  padding: 26px 30px;
  box-shadow: var(--ia-shadow-sm);
  position: relative;
  overflow: hidden;
  margin-bottom: 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}
.ia-hero::before {
  content: "";
  position: absolute;
  inset: auto -100px -140px auto;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20,184,166,.15), transparent 60%);
  pointer-events: none;
}
.ia-hero-left { flex: 1; min-width: 0; }

.ia-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ia-ink-400);
  font-size: 12.5px;
  margin-bottom: 8px;
}
.ia-breadcrumb b { color: var(--ia-ink-700); font-weight: 500; }

.ia-hero-title {
  font-family: 'Plus Jakarta Sans', 'Manrope', sans-serif;
  font-weight: 800;
  font-size: 30px;
  line-height: 1.1;
  letter-spacing: -0.025em;
  color: var(--ia-ink-900);
  margin: 0 0 8px;
}
.ia-hero-lead {
  color: var(--ia-ink-500);
  font-size: 14px;
  line-height: 1.6;
  max-width: 580px;
  margin: 0 0 16px;
}
.ia-hero-lead b { color: var(--ia-ink-700); font-weight: 600; }
.ia-hero-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.ia-ghost-btn {
  background: #fff;
  border: 1px solid var(--ia-line);
  border-radius: 12px;
  padding: 8px 13px;
  font-size: 13px;
  font-weight: 500;
  color: var(--ia-ink-700);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  transition: background .15s;
}
.ia-ghost-btn:hover { background: var(--ia-bg-soft); }
.ia-ghost-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.ia-stat-chips { display: flex; gap: 10px; flex-shrink: 0; }
.ia-stat-chip {
  background: var(--ia-card-2);
  border: 1px solid var(--ia-line);
  border-radius: 18px;
  padding: 13px 17px;
  min-width: 120px;
}
.ia-chip-label { font-size: 11px; text-transform: uppercase; letter-spacing: .12em; color: var(--ia-ink-400); }
.ia-chip-value {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 700;
  font-size: 22px;
  letter-spacing: -0.02em;
  color: var(--ia-ink-900);
  margin-top: 4px;
}
.ia-chip-denom { font-size: 13px; color: var(--ia-ink-400); font-weight: 500; }
.ia-chip-delta { font-size: 12px; color: var(--ia-ink-500); margin-top: 2px; }
.ia-chip-danger { background: #fff5f5; border-color: #fadddd; }
.ia-chip-danger .ia-chip-value { color: #b91c1c; }
.ia-chip-safe { background: #f4ecff; border-color: #e6d4ff; }
.ia-chip-safe .ia-chip-value { color: #6b21a8; }

/* ── Grid ────────────────────────────────────────────────────────── */
.ia-grid {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 1100px) { .ia-grid { grid-template-columns: 1fr; } }

/* ── Panel ───────────────────────────────────────────────────────── */
.ia-panel {
  background: var(--ia-card);
  border: 1px solid var(--ia-line);
  border-radius: 22px;
  box-shadow: var(--ia-shadow-sm);
  overflow: hidden;
}

.ia-panel-head {
  padding: 17px 20px 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--ia-line);
  background: linear-gradient(180deg, #fbfbf9, #fff);
}
.ia-panel-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--ia-ink-900);
}
.ia-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ia-teal-500);
  box-shadow: 0 0 0 4px var(--ia-teal-50);
}
.ia-panel-sub { font-size: 12px; color: var(--ia-ink-500); margin-top: 2px; }

/* ── Tabs ────────────────────────────────────────────────────────── */
.ia-tabs { display: flex; gap: 6px; padding: 12px 16px 0; }
.ia-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 10px 11px;
  border-radius: 13px;
  background: var(--ia-bg-soft);
  color: var(--ia-ink-500);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all .15s;
  user-select: none;
}
.ia-tab.is-active {
  background: var(--ia-card);
  color: var(--ia-ink-900);
  border-color: var(--ia-line-strong);
  box-shadow: var(--ia-shadow-sm);
}
.ia-tab-count {
  margin-left: 4px;
  background: #fff;
  border: 1px solid var(--ia-line);
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 11px;
  color: var(--ia-ink-500);
}
.ia-tab.is-active .ia-tab-count {
  background: var(--ia-teal-50);
  color: var(--ia-teal-700);
  border-color: var(--ia-teal-100);
}

/* ── Picker body ─────────────────────────────────────────────────── */
.ia-picker-body { padding: 13px 16px 16px; }

.ia-search-pill {
  display: flex;
  align-items: center;
  gap: 9px;
  background: var(--ia-bg-soft);
  border: 1px solid var(--ia-line);
  border-radius: 13px;
  padding: 11px 13px;
  transition: border .15s, background .15s;
}
.ia-search-pill:focus-within {
  background: #fff;
  border-color: var(--ia-teal-300);
  box-shadow: 0 0 0 4px var(--ia-teal-50);
}
.ia-search-pill input {
  flex: 1;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 13.5px;
  color: var(--ia-ink-900);
}
.ia-search-pill input::placeholder { color: var(--ia-ink-400); }
.ia-search-badge {
  font-size: 11px;
  color: var(--ia-ink-500);
  background: #fff;
  border: 1px solid var(--ia-line);
  border-radius: 8px;
  padding: 2px 7px;
  flex-shrink: 0;
}

/* ── Suggest dropdown ────────────────────────────────────────────── */
.ia-suggest {
  margin-top: 7px;
  background: #fff;
  border: 1px solid var(--ia-line);
  border-radius: 13px;
  overflow: hidden;
  box-shadow: var(--ia-shadow-md);
}
.ia-suggest-row {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 9px 11px;
  cursor: pointer;
  border-bottom: 1px solid var(--ia-line);
  transition: background .1s;
}
.ia-suggest-row:last-child { border-bottom: 0; }
.ia-suggest-row:hover { background: var(--ia-bg-soft); }
.ia-suggest-thumb {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--ia-bg-soft);
  display: grid;
  place-items: center;
  font-size: 17px;
  flex-shrink: 0;
  overflow: hidden;
  color: var(--ia-ink-500);
}
.ia-suggest-meta { flex: 1; min-width: 0; }
.ia-suggest-meta b {
  display: block;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--ia-ink-900);
}
.ia-suggest-meta span { font-size: 11.5px; color: var(--ia-ink-500); }
.ia-suggest-add {
  border: 0;
  background: var(--ia-teal-600);
  color: #fff;
  border-radius: 9px;
  padding: 5px 9px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* ── Selected drugs ──────────────────────────────────────────────── */
.ia-selected-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 16px 0 7px;
}
.ia-selected-title {
  font-size: 12px;
  color: var(--ia-ink-500);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: .08em;
}
.ia-counter {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 700;
  font-size: 13px;
  color: var(--ia-ink-700);
  background: var(--ia-bg-soft);
  padding: 3px 9px;
  border-radius: 999px;
}
.ia-counter span { color: var(--ia-ink-400); font-weight: 500; }

.ia-progress {
  height: 5px;
  background: var(--ia-bg-soft);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 12px;
}
.ia-progress > div {
  height: 100%;
  background: linear-gradient(90deg, #14b8a6, #0f766e);
  border-radius: 999px;
  transition: width .3s ease;
}

.ia-drug-empty {
  border: 1.5px dashed var(--ia-line-strong);
  border-radius: 13px;
  padding: 20px;
  text-align: center;
  color: var(--ia-ink-500);
  font-size: 13px;
  background: var(--ia-bg-soft);
}
.ia-drug-list { display: flex; flex-direction: column; gap: 7px; }
.ia-drug-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid var(--ia-line);
  border-radius: 13px;
  padding: 9px 11px;
  transition: all .15s;
}
.ia-drug-card:hover { border-color: var(--ia-line-strong); box-shadow: var(--ia-shadow-sm); }
.ia-drug-thumb {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  background: var(--ia-bg-soft);
  display: grid;
  place-items: center;
  font-size: 20px;
  border: 1px solid var(--ia-line);
  overflow: hidden;
  color: var(--ia-ink-400);
}
.ia-drug-thumb-generic { background: #e6f7f2; color: var(--ia-teal-600); }
.ia-drug-info { min-width: 0; }
.ia-drug-name {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--ia-ink-900);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ia-drug-meta { font-size: 11px; color: var(--ia-ink-500); margin-top: 2px; display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.ia-drug-reg {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  color: var(--ia-ink-700);
  background: var(--ia-bg-soft);
  padding: 1px 5px;
  border-radius: 5px;
}
.ia-drug-form {
  background: #fff;
  border: 1px solid var(--ia-line);
  padding: 1px 5px;
  border-radius: 5px;
  color: var(--ia-ink-700);
}
.ia-drug-expired { color: #dc2626; font-weight: 600; }
.ia-drug-remove {
  border: 0;
  background: transparent;
  width: 28px;
  height: 28px;
  border-radius: 7px;
  color: var(--ia-ink-400);
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: all .1s;
}
.ia-drug-remove:hover { background: #fef2f2; color: #dc2626; }

/* ── Run button ──────────────────────────────────────────────────── */
.ia-run-btn {
  margin-top: 14px;
  width: 100%;
  background: linear-gradient(120deg, #064e3b 0%, #0f766e 70%, #0d9488 100%);
  color: #fff;
  border: 0;
  padding: 15px;
  border-radius: 15px;
  font-weight: 700;
  font-size: 14.5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  box-shadow: 0 12px 26px -14px rgba(13,148,136,.7);
  position: relative;
  overflow: hidden;
  font-family: 'Plus Jakarta Sans', sans-serif;
  letter-spacing: -0.005em;
  transition: transform .15s, box-shadow .15s;
}
.ia-run-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 16px 32px -14px rgba(13,148,136,.8); }
.ia-run-btn:disabled { opacity: .5; cursor: not-allowed; transform: none; box-shadow: none; }
.ia-run-arrow {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 7px;
  background: rgba(255,255,255,.18);
}

/* ── Tip / Error / Warn banner ───────────────────────────────────── */
.ia-tip {
  margin-top: 11px;
  padding: 9px 11px;
  background: var(--ia-teal-50);
  border: 1px solid var(--ia-teal-100);
  border-radius: 11px;
  font-size: 12px;
  color: var(--ia-teal-700);
  display: flex;
  align-items: flex-start;
  gap: 7px;
}
.ia-tip b { color: #064e3b; }
.ia-error {
  margin-top: 11px;
  padding: 9px 11px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 11px;
  font-size: 12.5px;
  color: #b91c1c;
  display: flex;
  align-items: flex-start;
  gap: 7px;
}
.ia-warn-banner {
  margin-top: 11px;
  padding: 9px 11px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 11px;
  font-size: 12.5px;
  color: #92400e;
  display: flex;
  align-items: flex-start;
  gap: 7px;
}

/* ── Loading / Empty states ──────────────────────────────────────── */
.ia-loading-state {
  padding: 60px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.ia-loading-spinner-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--ia-teal-50);
  display: grid;
  place-items: center;
}
.ia-loading-text { font-size: 14px; font-weight: 600; color: var(--ia-ink-700); margin: 0; }
.ia-loading-sub { font-size: 12.5px; color: var(--ia-ink-400); margin: 0; }

.ia-empty-state {
  padding: 60px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}
.ia-empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: var(--ia-teal-50);
  display: grid;
  place-items: center;
  color: var(--ia-teal-600);
}
.ia-empty-title { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 16px; color: var(--ia-ink-700); }
.ia-empty-sub { font-size: 13px; color: var(--ia-ink-500); max-width: 340px; line-height: 1.55; }
.ia-empty-sub b { color: var(--ia-ink-700); }
.ia-empty-sources {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  color: var(--ia-ink-400);
  margin-top: 6px;
}

/* ── Results header ──────────────────────────────────────────────── */
.ia-results-head {
  padding: 20px 22px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  border-bottom: 1px solid var(--ia-line);
  flex-wrap: wrap;
}
.ia-results-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 800;
  font-size: 20px;
  letter-spacing: -0.02em;
  color: var(--ia-ink-900);
  margin: 0;
}
.ia-results-sub { font-size: 12.5px; color: var(--ia-ink-500); margin-top: 2px; }

.ia-seg {
  display: inline-flex;
  background: var(--ia-bg-soft);
  padding: 4px;
  border-radius: 12px;
  gap: 2px;
}
.ia-seg-btn {
  border: 0;
  background: transparent;
  padding: 6px 11px;
  border-radius: 9px;
  font-size: 12px;
  color: var(--ia-ink-500);
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all .15s;
}
.ia-seg-btn.is-active { background: #fff; color: var(--ia-ink-900); box-shadow: var(--ia-shadow-sm); }
.ia-seg-btn.is-danger { color: #dc2626; }
.ia-seg-btn.is-warn { color: #b45309; }
.ia-seg-btn.is-safe { color: #6b21a8; }
.ia-seg-count { opacity: .65; }
.ia-sev-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

/* ── Severity overview ───────────────────────────────────────────── */
.ia-sev-overview {
  padding: 16px 22px;
  border-bottom: 1px solid var(--ia-line);
  background: var(--ia-card-2);
}
.ia-sev-overview-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.ia-sev-summary { font-size: 13px; color: var(--ia-ink-700); font-weight: 500; }
.ia-sev-confidence { font-size: 12px; color: var(--ia-ink-400); }
.ia-sev-bar {
  height: 9px;
  border-radius: 999px;
  overflow: hidden;
  display: flex;
  background: var(--ia-bg-soft);
  margin-bottom: 10px;
}
.ia-sev-red { background: linear-gradient(90deg, #ef4444, #dc2626); transition: width .4s; }
.ia-sev-amber { background: linear-gradient(90deg, #fbbf24, #f59e0b); transition: width .4s; }
.ia-sev-violet { background: linear-gradient(90deg, #a855f7, #9333ea); transition: width .4s; }
.ia-sev-legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--ia-ink-500); align-items: center; }
.ia-sev-item { display: flex; align-items: center; gap: 5px; }
.ia-sev-swatch { width: 8px; height: 8px; border-radius: 3px; flex-shrink: 0; }
.ia-sev-source { margin-left: auto; display: flex; align-items: center; gap: 5px; }

/* ── Interaction Matrix ──────────────────────────────────────────── */
.ia-matrix-wrap {
  padding: 16px 22px 20px;
  border-bottom: 1px solid var(--ia-line);
  overflow-x: auto;
}
.ia-matrix-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.ia-matrix-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 13.5px;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--ia-ink-700);
}
.ia-matrix-helper { font-size: 12px; color: var(--ia-ink-400); }

.ia-matrix { display: inline-grid; gap: 5px; }
.ia-mcell {
  width: 46px;
  height: 46px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  border: 1px solid var(--ia-line);
  background: var(--ia-card-2);
  font-size: 11px;
  color: var(--ia-ink-400);
  text-align: center;
  line-height: 1.1;
  padding: 2px;
  position: relative;
  cursor: default;
  transition: transform .15s, box-shadow .15s;
}
.ia-mcell-label {
  background: transparent;
  border: 0;
  font-weight: 600;
  color: var(--ia-ink-700);
  font-size: 11px;
  justify-content: flex-start;
  align-items: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-left: 0;
}
.ia-mcell-header { justify-content: center; text-align: center; padding: 2px; }
.ia-mcell-row { width: 110px; }
.ia-mcell-diag {
  background: repeating-linear-gradient(45deg, var(--ia-bg-soft) 0 4px, transparent 4px 8px);
  border-style: dashed;
}
.ia-mcell-danger { background: linear-gradient(135deg, #fef2f2, #fde0e0); border-color: #f7c7c7; cursor: pointer; }
.ia-mcell-warn { background: linear-gradient(135deg, #fef6e3, #fde7be); border-color: #f3d8a0; cursor: pointer; }
.ia-mcell-safe { background: linear-gradient(135deg, #f5edff, #eadcff); border-color: #d8c4f5; cursor: pointer; }
.ia-mcell-danger:hover, .ia-mcell-warn:hover, .ia-mcell-safe:hover {
  transform: translateY(-2px);
  box-shadow: var(--ia-shadow-md);
}
.ia-mcell-num {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 800;
  font-size: 15px;
}

/* ── AI insight strip ────────────────────────────────────────────── */
.ia-ai-insight {
  margin: 0 22px 18px;
  border-radius: 16px;
  padding: 15px 17px;
  background: linear-gradient(135deg, #0f172a, #0f766e 130%);
  color: #e8f6f1;
  display: flex;
  align-items: flex-start;
  gap: 13px;
  position: relative;
  overflow: hidden;
  margin-top: 18px;
}
.ia-ai-insight::before {
  content: "";
  position: absolute;
  inset: auto -50px -80px auto;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20,184,166,.4), transparent 60%);
}
.ia-ai-icon {
  width: 36px;
  height: 36px;
  border-radius: 11px;
  background: rgba(20,184,166,.22);
  color: #5eead4;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border: 1px solid rgba(94,234,212,.28);
}
.ia-ai-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  margin: 0;
  font-size: 13.5px;
  font-weight: 700;
  letter-spacing: -0.005em;
  display: flex;
  align-items: center;
  gap: 7px;
  color: #fff;
}
.ia-ai-pulse {
  font-size: 10px;
  color: #5eead4;
  background: rgba(94,234,212,.12);
  padding: 2px 7px;
  border-radius: 999px;
  border: 1px solid rgba(94,234,212,.28);
  text-transform: uppercase;
  letter-spacing: .1em;
}
.ia-ai-body { margin: 4px 0 0; font-size: 13px; line-height: 1.55; color: #cce6e0; max-width: 680px; position: relative; z-index: 1; }

/* ── Interaction cards ───────────────────────────────────────────── */
.ia-iact-list { padding: 16px 20px 20px; display: flex; flex-direction: column; gap: 12px; }
.ia-empty-filter { padding: 30px; text-align: center; font-size: 13px; color: var(--ia-ink-400); }

.ia-iact {
  border: 1px solid var(--ia-line);
  border-radius: 17px;
  overflow: hidden;
  background: #fff;
  position: relative;
}
.ia-iact-stripe { position: absolute; left: 0; top: 0; bottom: 0; width: 4px; }
.ia-iact.danger .ia-iact-stripe { background: linear-gradient(180deg, #ef4444, #b91c1c); }
.ia-iact.warn .ia-iact-stripe { background: linear-gradient(180deg, #fbbf24, #d97706); }

.ia-iact-head {
  display: flex;
  align-items: flex-start;
  gap: 13px;
  padding: 16px 18px 12px 22px;
  cursor: pointer;
}
.ia-iact-sev-icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.ia-iact.danger .ia-iact-sev-icon { background: #fef2f2; color: #dc2626; }
.ia-iact.warn .ia-iact-sev-icon { background: #fffbeb; color: #b45309; }

.ia-iact-titleline { flex: 1; min-width: 0; }
.ia-iact-pair {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 800;
  font-size: 16px;
  letter-spacing: -0.015em;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--ia-ink-900);
}
.ia-iact-x {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  background: var(--ia-bg-soft);
  color: var(--ia-ink-500);
  font-size: 11px;
  font-weight: 600;
}
.ia-iact-badges { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 7px; }
.ia-badge {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .04em;
  text-transform: uppercase;
  padding: 3px 9px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.ia-badge.danger { background: #fef2f2; color: #b91c1c; }
.ia-badge.warn { background: #fffbeb; color: #b45309; }
.ia-badge-neutral { background: var(--ia-bg-soft); color: var(--ia-ink-700); }
.ia-badge-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.ia-iact-actions { display: flex; align-items: center; }
.ia-chevron {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: var(--ia-bg-soft);
  display: grid;
  place-items: center;
  color: var(--ia-ink-500);
  transition: transform .2s;
}
.ia-chevron.open { transform: rotate(180deg); }

.ia-iact-summary {
  padding: 0 22px 14px 22px;
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--ia-ink-700);
}

.ia-iact-body {
  border-top: 1px dashed var(--ia-line);
  padding: 16px 22px 20px;
  background: var(--ia-card-2);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.ia-iact-full { grid-column: 1 / -1; }
.ia-iact-section-label {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--ia-ink-500);
  margin: 0 0 5px;
  display: flex;
  align-items: center;
  gap: 7px;
}
.ia-iact-p { margin: 0; font-size: 13px; color: var(--ia-ink-700); line-height: 1.55; }
.ia-iact-source {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ia-ink-500);
  flex-wrap: wrap;
}
.ia-src-chip {
  background: #fff;
  border: 1px solid var(--ia-line);
  border-radius: 7px;
  padding: 3px 7px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ia-ink-700);
  font-weight: 500;
  font-size: 11.5px;
}

/* ── Safe pairs ──────────────────────────────────────────────────── */
.ia-safe-header {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  font-weight: 600;
  color: #6b21a8;
  padding: 12px 4px 6px;
  border-top: 1px dashed var(--ia-line);
  margin-top: 4px;
}
.ia-safe-list {
  background: linear-gradient(135deg, #f5edff, #eadcff);
  border: 1px solid #d8c4f5;
  border-radius: 14px;
  padding: 4px 6px;
  display: flex;
  flex-direction: column;
}
.ia-safe-pair {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  font-size: 13px;
  color: #4c1d95;
  border-radius: 9px;
  transition: background .1s;
}
.ia-safe-pair:hover { background: rgba(255,255,255,.5); }
.ia-safe-check {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #6b21a8;
  color: #fff;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.ia-safe-x { color: #9333ea; font-weight: 600; }

/* ── Print FAB ───────────────────────────────────────────────────── */
.ia-fab {
  position: fixed;
  right: 26px;
  bottom: 26px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0f766e, #0d9488);
  color: #fff;
  display: grid;
  place-items: center;
  cursor: pointer;
  box-shadow: 0 16px 32px -10px rgba(13,148,136,.6);
  border: 0;
  z-index: 50;
  transition: transform .15s, box-shadow .15s;
}
.ia-fab:hover { transform: scale(1.08); box-shadow: 0 20px 40px -10px rgba(13,148,136,.7); }

/* ── Spinner animation ───────────────────────────────────────────── */
@keyframes ia-spin { to { transform: rotate(360deg); } }
.ia-spin { animation: ia-spin 1s linear infinite; transform-origin: center; }
</style>
