<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useInteractionCheckMutation } from '@/api/interactions.api'
import { drugsApi } from '@/api/drugs.api'
import { useExcelExport } from '@/composables/useExcelExport'
import { getSeverityClasses, getSeverityLabel } from '@/utils/severity'
import type { DrugListItem } from '@/types/drug.types'
import type { InteractionCheckResult } from '@/types/interaction.types'
import DrugSearchCombobox from '@/components/drug/DrugSearchCombobox.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const route = useRoute()
const selectedDrugs = ref<DrugListItem[]>([])
const result = ref<InteractionCheckResult | null>(null)

const { mutate: checkInteractions, isPending: checking, error } = useInteractionCheckMutation()
const { exporting, exportExcel } = useExcelExport()

const canCheck = computed(() => selectedDrugs.value.length >= 2)

// Pre-select drug from query param (e.g. from DrugDetail)
onMounted(async () => {
  const drugId = route.query.drug as string
  if (drugId) {
    try {
      const drug = await drugsApi.get(drugId)
      selectedDrugs.value = [{ id: drug.id, name: drug.name, atc_code: drug.atc_code, description: drug.description, dosage_form: drug.dosage_form, classification: drug.classification }]
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
</script>

<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold text-[#111827]">Kiểm tra tương tác thuốc</h1>
      <p class="text-sm text-[#6B7280] mt-1">Chọn từ 2 đến 20 thuốc để kiểm tra tương tác</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left: drug selector -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-4">
        <h2 class="text-base font-semibold text-[#111827]">Chọn thuốc</h2>

        <DrugSearchCombobox v-model="selectedDrugs" :max="20" placeholder="Tìm và thêm thuốc..." />

        <div class="flex items-center gap-3 pt-2">
          <AppButton :disabled="!canCheck" :loading="checking" @click="doCheck" full>
            Kiểm tra tương tác
          </AppButton>
          <AppButton v-if="result" variant="outline" :loading="exporting" @click="doExport">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Xuất Excel
          </AppButton>
        </div>

        <AppAlert v-if="errorMessage" type="error">{{ errorMessage }}</AppAlert>
      </div>

      <!-- Right: results -->
      <div class="space-y-4">
        <!-- Loading -->
        <div v-if="checking" class="bg-white rounded-2xl border border-[#E5E7EB] p-8 flex items-center justify-center">
          <div class="flex flex-col items-center gap-3">
            <AppSpinner size="lg" class="text-[#10B981]" />
            <p class="text-sm text-[#6B7280]">Đang kiểm tra tương tác...</p>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else-if="!result" class="bg-white rounded-2xl border border-[#E5E7EB] p-8 text-center">
          <div class="w-14 h-14 bg-[#F3F4F6] rounded-full flex items-center justify-center mx-auto mb-3">
            <svg class="w-7 h-7 text-[#9CA3AF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p class="text-sm text-[#6B7280]">Chọn ít nhất 2 thuốc và nhấn kiểm tra để xem kết quả</p>
        </div>

        <!-- Results -->
        <template v-else>
          <!-- Summary card -->
          <div :class="['rounded-2xl border p-5', result.has_interaction ? 'bg-red-50 border-red-200' : 'bg-[#D1FAE5] border-[#6EE7B7]']">
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-bold flex-shrink-0"
                :class="result.has_interaction ? 'bg-red-100 text-red-600' : 'bg-[#A7F3D0] text-[#065F46]'"
              >
                {{ result.interaction_count }}
              </div>
              <div>
                <p class="font-semibold" :class="result.has_interaction ? 'text-red-700' : 'text-[#065F46]'">
                  {{ result.has_interaction ? 'Phát hiện tương tác thuốc!' : 'Không có tương tác đáng lo ngại' }}
                </p>
                <p class="text-sm" :class="result.has_interaction ? 'text-red-600' : 'text-[#059669]'">
                  {{ result.interaction_count }} / {{ result.total_pairs }} cặp có tương tác
                </p>
              </div>
            </div>
          </div>

          <!-- Interaction pairs -->
          <div v-if="result.has_interaction" class="space-y-3">
            <div
              v-for="pair in result.pairs.filter((p) => p.has_interaction)"
              :key="`${pair.drug_1_id}-${pair.drug_2_id}`"
              class="bg-white rounded-xl border border-[#E5E7EB] p-4"
            >
              <div class="flex items-start justify-between gap-3">
                <p class="font-medium text-[#111827] text-sm">{{ pair.drug_1_name }} ↔ {{ pair.drug_2_name }}</p>
                <span v-if="pair.interaction" :class="['text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0', getSeverityClasses(pair.interaction.severity)]">
                  {{ getSeverityLabel(pair.interaction.severity) }}
                </span>
              </div>
              <p v-if="pair.interaction?.description" class="text-sm text-[#374151] mt-2">{{ pair.interaction.description }}</p>
              <div v-if="pair.interaction?.recommendation" class="mt-2 p-2 bg-[#D1FAE5] rounded-lg">
                <p class="text-sm text-[#065F46]">💡 {{ pair.interaction.recommendation }}</p>
              </div>
            </div>
          </div>

          <!-- Safe pairs (collapsible) -->
          <details v-if="result.pairs.some((p) => !p.has_interaction)" class="bg-white rounded-xl border border-[#E5E7EB]">
            <summary class="px-4 py-3 cursor-pointer text-sm font-medium text-[#374151] select-none list-none flex items-center justify-between">
              <span>Cặp thuốc an toàn ({{ result.pairs.filter((p) => !p.has_interaction).length }})</span>
              <svg class="w-4 h-4 text-[#9CA3AF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div class="px-4 pb-3 space-y-1">
              <div
                v-for="pair in result.pairs.filter((p) => !p.has_interaction)"
                :key="`${pair.drug_1_id}-${pair.drug_2_id}`"
                class="flex items-center gap-2 py-1.5 text-sm text-[#374151]"
              >
                <span class="text-[#10B981]">✓</span>
                {{ pair.drug_1_name }} ↔ {{ pair.drug_2_name }}
              </div>
            </div>
          </details>
        </template>
      </div>
    </div>
  </div>
</template>
