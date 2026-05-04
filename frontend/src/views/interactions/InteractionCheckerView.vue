<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useInteractionCheckMutation } from '@/api/interactions.api'
import { drugsApi } from '@/api/drugs.api'
import { useExcelExport } from '@/composables/useExcelExport'
import type { DrugListItem } from '@/types/drug.types'
import type { InteractionCheckResult } from '@/types/interaction.types'
import DrugSearchCombobox from '@/components/drug/DrugSearchCombobox.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'

const route = useRoute()
const selectedDrugs = ref<DrugListItem[]>([])
const result = ref<InteractionCheckResult | null>(null)

const { mutate: checkInteractions, isPending: checking, error } = useInteractionCheckMutation()
const { exporting, exportExcel } = useExcelExport()

const canCheck = computed(() => selectedDrugs.value.length >= 2)

onMounted(async () => {
  const drugId = route.query.drug as string
  if (drugId) {
    try {
      const drug = await drugsApi.get(drugId)
      selectedDrugs.value = [{
        id: drug.id, name: drug.name, atc_code: drug.atc_code,
        description: drug.description, dosage_form: drug.dosage_form,
        classification: drug.classification,
      }]
    } catch { /* ignore */ }
  }
})

function doCheck() {
  const ids = selectedDrugs.value.map((d) => d.id)
  checkInteractions(ids, {
    onSuccess: (data) => { result.value = data },
  })
}

function doExport() {
  const ids = selectedDrugs.value.map((d) => d.id)
  exportExcel('/interactions/check/export', { drug_ids: ids }, 'tuong-tac-thuoc.xlsx')
}

const errorMessage = computed(() => {
  const e = error.value as { message?: string } | null
  return e?.message || null
})

const dangerCount = computed(() => result.value?.pairs.filter((p) => p.has_interaction && p.interaction?.severity === 'major').length ?? 0)
const warningCount = computed(() => result.value?.pairs.filter((p) => p.has_interaction && p.interaction?.severity !== 'major').length ?? 0)

function severityToBorder(severity: string | undefined) {
  if (severity === 'major') return 'bg-error'
  if (severity === 'moderate') return 'bg-warning'
  return 'bg-yellow-400'
}

function severityToIconBg(severity: string | undefined) {
  if (severity === 'major') return 'bg-error-container text-error'
  if (severity === 'moderate') return 'bg-yellow-50 text-yellow-600'
  return 'bg-yellow-50 text-yellow-600'
}

function severityToTitleColor(severity: string | undefined) {
  if (severity === 'major') return 'text-error'
  return 'text-yellow-700'
}

function severityToBadge(severity: string | undefined) {
  if (severity === 'major') return 'bg-error/10 text-error border border-error/20'
  return 'bg-yellow-50 text-yellow-700 border border-yellow-200'
}

function severityLabel(severity: string | undefined) {
  if (severity === 'major') return 'MỨC ĐỘ: CAO'
  if (severity === 'moderate') return 'MỨC ĐỘ: TRUNG BÌNH'
  return 'MỨC ĐỘ: NHẸ'
}

function severityInteractionTypeColor(severity: string | undefined) {
  if (severity === 'major') return 'text-error'
  return 'text-yellow-600'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-on-surface">Kiểm tra tương tác thuốc</h1>
      <p class="text-sm text-outline mt-0.5">Chọn từ 2 đến 20 thuốc để kiểm tra tương tác tự động</p>
    </div>

    <!-- Input section -->
    <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
      <div class="flex items-center gap-4 mb-6">
        <div class="w-10 h-10 bg-primary-fixed rounded-xl flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div>
          <h2 class="text-base font-bold text-on-surface">Danh sách thuốc cần kiểm tra</h2>
          <p class="text-sm text-outline">Thêm các loại thuốc để bắt đầu phân tích tương tác</p>
        </div>
      </div>

      <DrugSearchCombobox v-model="selectedDrugs" :max="20" placeholder="Tìm và thêm thuốc..." />

      <div class="mt-6 flex flex-wrap items-center gap-3">
        <AppButton
          variant="gradient"
          :disabled="!canCheck"
          :loading="checking"
          @click="doCheck"
          size="lg"
        >
          <template v-if="!checking">
            <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Chạy phân tích tương tác
          </template>
        </AppButton>
        <AppButton v-if="result" variant="outline" :loading="exporting" @click="doExport">
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Xuất Excel
        </AppButton>
      </div>

      <div v-if="errorMessage" class="mt-4 p-3 bg-error-container border border-error/20 rounded-xl text-sm text-error">
        {{ errorMessage }}
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="checking" class="bg-card rounded-2xl border border-outline-variant p-12 flex flex-col items-center gap-4">
      <AppSpinner size="lg" class="text-primary" />
      <p class="text-sm text-outline">Đang phân tích tương tác thuốc...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="!result" class="bg-card rounded-2xl border border-outline-variant p-12 text-center">
      <div class="w-16 h-16 bg-surface-container rounded-2xl flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      </div>
      <p class="text-sm font-medium text-on-surface">Chọn ít nhất 2 thuốc để kiểm tra</p>
      <p class="text-xs text-outline mt-1">Kết quả phân tích tương tác sẽ hiển thị tại đây</p>
    </div>

    <!-- Results -->
    <template v-else>
      <!-- Summary header -->
      <div class="flex flex-wrap items-center justify-between gap-4">
        <h3 class="text-lg font-bold text-on-surface">Kết quả phân tích</h3>
        <div class="flex flex-wrap gap-3">
          <div v-if="dangerCount > 0" class="flex items-center gap-2 px-3 py-1 bg-error-container text-error rounded-full text-xs font-bold uppercase tracking-wider">
            <span class="w-2 h-2 rounded-full bg-error" />
            {{ dangerCount }} Nguy hiểm
          </div>
          <div v-if="warningCount > 0" class="flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-bold uppercase tracking-wider">
            <span class="w-2 h-2 rounded-full bg-yellow-500" />
            {{ warningCount }} Cảnh báo
          </div>
          <div v-if="!result.has_interaction" class="flex items-center gap-2 px-3 py-1 bg-tertiary-fixed text-tertiary rounded-full text-xs font-bold uppercase tracking-wider">
            <span class="w-2 h-2 rounded-full bg-tertiary" />
            An toàn
          </div>
        </div>
      </div>

      <!-- Summary card -->
      <div :class="[
        'rounded-2xl border p-5 flex items-center gap-4',
        result.has_interaction ? 'bg-error-container/40 border-error/20' : 'bg-tertiary-fixed/40 border-tertiary/20'
      ]">
        <div :class="[
          'w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-bold flex-shrink-0',
          result.has_interaction ? 'bg-error-container text-error' : 'bg-tertiary-fixed text-tertiary'
        ]">
          {{ result.interaction_count }}
        </div>
        <div>
          <p class="font-semibold text-on-surface">
            {{ result.has_interaction ? 'Phát hiện tương tác thuốc!' : 'Không có tương tác đáng lo ngại' }}
          </p>
          <p class="text-sm text-outline mt-0.5">
            {{ result.interaction_count }} / {{ result.total_pairs }} cặp có tương tác
          </p>
        </div>
      </div>

      <!-- Interaction pair cards (with left border accent) -->
      <div class="space-y-4">
        <div
          v-for="pair in result.pairs.filter((p) => p.has_interaction)"
          :key="`${pair.drug_1_id}-${pair.drug_2_id}`"
          class="bg-card rounded-2xl overflow-hidden border border-outline-variant shadow-sm flex"
        >
          <!-- Left severity bar -->
          <div :class="['w-1.5 flex-shrink-0', severityToBorder(pair.interaction?.severity)]" />
          <div class="p-5 flex-1">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div class="flex items-center gap-3">
                <div :class="['w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0', severityToIconBg(pair.interaction?.severity)]">
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h4 :class="['text-base font-extrabold', severityToTitleColor(pair.interaction?.severity)]">
                    {{ pair.drug_1_name }} × {{ pair.drug_2_name }}
                  </h4>
                  <p :class="['text-xs font-bold uppercase tracking-wider', severityInteractionTypeColor(pair.interaction?.severity)]">
                    {{ pair.interaction?.interaction_type || 'Tương tác thuốc' }}
                  </p>
                </div>
              </div>
              <span :class="['px-3 py-1 rounded-lg text-xs font-black whitespace-nowrap flex-shrink-0', severityToBadge(pair.interaction?.severity)]">
                {{ severityLabel(pair.interaction?.severity) }}
              </span>
            </div>

            <p v-if="pair.interaction?.description" class="text-sm text-on-surface-variant mb-4 leading-relaxed">
              {{ pair.interaction.description }}
            </p>

            <div v-if="pair.interaction?.recommendation" class="bg-surface-container-low rounded-xl p-4 flex items-start gap-3 border-l-4 border-outline-variant">
              <svg class="w-4 h-4 text-outline mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <span class="text-xs font-bold text-on-surface block mb-1">Khuyến nghị:</span>
                <span class="text-sm text-on-surface-variant">{{ pair.interaction.recommendation }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Safe pairs collapsible -->
      <details v-if="result.pairs.some((p) => !p.has_interaction)" class="bg-card rounded-2xl border border-outline-variant overflow-hidden">
        <summary class="px-5 py-4 cursor-pointer text-sm font-semibold text-on-surface select-none list-none flex items-center justify-between hover:bg-surface-container-low transition-colors">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Cặp thuốc an toàn ({{ result.pairs.filter((p) => !p.has_interaction).length }})
          </div>
          <svg class="w-4 h-4 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="px-5 pb-4 space-y-1 border-t border-outline-variant">
          <div
            v-for="pair in result.pairs.filter((p) => !p.has_interaction)"
            :key="`${pair.drug_1_id}-${pair.drug_2_id}`"
            class="flex items-center gap-2 py-2 text-sm text-on-surface-variant"
          >
            <svg class="w-4 h-4 text-tertiary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {{ pair.drug_1_name }} ↔ {{ pair.drug_2_name }}
          </div>
        </div>
      </details>
    </template>

    <!-- Print FAB -->
    <Teleport to="body">
      <button
        v-if="result"
        @click="window.print()"
        class="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-br from-primary to-primary-container text-white rounded-full shadow-lg flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-50"
        title="In kết quả"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
      </button>
    </Teleport>
  </div>
</template>
