<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRecommendationMutation, recommendationApi } from '@/api/recommendations.api'
import type { RecommendationResult } from '@/api/recommendations.api'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'

const router = useRouter()
const symptoms = ref('')
const result = ref<RecommendationResult | null>(null)
const exporting = ref(false)

const { mutate: recommend, isPending, error } = useRecommendationMutation()

function doRecommend() {
  if (!symptoms.value.trim() || isPending.value) return
  recommend(
    { symptoms: symptoms.value.trim() },
    {
      onSuccess: (data) => { result.value = data },
    },
  )
}

async function doExport() {
  if (!result.value) return
  exporting.value = true
  try {
    const blob = await recommendationApi.export(result.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'goi-y-thuoc.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

function scoreColor(score: number) {
  if (score >= 80) return 'bg-tertiary'
  if (score >= 60) return 'bg-primary'
  if (score >= 40) return 'bg-warning'
  return 'bg-error'
}

function scoreTextColor(score: number) {
  if (score >= 80) return 'text-tertiary'
  if (score >= 60) return 'text-primary'
  if (score >= 40) return 'text-warning'
  return 'text-error'
}

const errorMessage = (error.value as { message?: string } | null)?.message
</script>

<template>
  <div class="space-y-6">
    <!-- Hero gradient header -->
    <div class="relative overflow-hidden bg-gradient-to-br from-primary to-primary-container rounded-2xl p-6 text-white">
      <div class="relative z-10">
        <div class="flex items-center gap-2 mb-2">
          <svg class="w-5 h-5 text-tertiary-fixed" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <span class="text-xs font-bold uppercase tracking-widest text-tertiary-fixed">AI Drug Advisor</span>
        </div>
        <h1 class="text-2xl font-bold mb-1">Gợi ý thuốc từ AI</h1>
        <p class="text-primary-fixed-dim text-sm max-w-2xl">Nhập triệu chứng của bạn và AI sẽ gợi ý thuốc phù hợp dựa trên hồ sơ sức khỏe cá nhân. Chỉ mang tính tham khảo.</p>
      </div>
      <div class="absolute -right-8 -bottom-8 w-40 h-40 rounded-full bg-white/10" />
      <div class="absolute right-16 -top-4 w-20 h-20 rounded-full bg-white/5" />
    </div>

    <!-- Input section -->
    <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
      <h2 class="text-base font-bold text-on-surface mb-4">Mô tả triệu chứng</h2>
      <textarea
        v-model="symptoms"
        rows="4"
        :disabled="isPending"
        placeholder="Mô tả chi tiết triệu chứng của bạn (ít nhất 10 ký tự)...&#10;Ví dụ: Tôi bị đau đầu, sốt nhẹ 37.5°C, nghẹt mũi, ho khan từ 2 ngày nay..."
        class="w-full px-4 py-3 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none transition-all disabled:opacity-50"
      />
      <p class="text-xs text-outline mt-1.5">{{ symptoms.length }}/1000 ký tự (tối thiểu 10)</p>

      <div v-if="error" class="mt-3 p-3 bg-error-container border border-error/20 rounded-xl text-sm text-error">
        {{ (error as any)?.message || 'Đã xảy ra lỗi. Vui lòng thử lại.' }}
      </div>

      <div class="mt-4 flex flex-wrap gap-3">
        <AppButton
          variant="gradient"
          size="lg"
          :disabled="symptoms.trim().length < 10 || isPending"
          :loading="isPending"
          @click="doRecommend"
        >
          <template v-if="!isPending">
            <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Nhận gợi ý từ AI
          </template>
        </AppButton>
        <AppButton v-if="result" variant="outline" :loading="exporting" @click="doExport">
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Xuất Excel
        </AppButton>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="isPending" class="bg-card rounded-2xl border border-outline-variant p-12 flex flex-col items-center gap-4">
      <AppSpinner size="lg" class="text-primary" />
      <p class="text-sm text-outline">AI đang phân tích triệu chứng và gợi ý thuốc phù hợp...</p>
    </div>

    <!-- Results -->
    <template v-else-if="result">
      <!-- General advice card -->
      <div class="bg-primary-fixed/40 border border-primary/10 rounded-2xl p-5">
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 bg-primary rounded-xl flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="text-sm font-bold text-on-surface mb-1">Lời khuyên chung</p>
            <p class="text-sm text-on-surface-variant leading-relaxed">{{ result.general_advice }}</p>
          </div>
        </div>
      </div>

      <!-- Drug suggestion cards -->
      <div>
        <h2 class="text-lg font-bold text-on-surface mb-4">Thuốc được gợi ý ({{ result.suggestions.length }})</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(drug, i) in result.suggestions"
            :key="i"
            :class="[
              'bg-card rounded-2xl border p-5 shadow-sm',
              drug.has_interaction ? 'border-error/30' : 'border-outline-variant',
            ]"
          >
            <!-- Header -->
            <div class="flex items-start justify-between gap-2 mb-3">
              <div class="flex items-center gap-2 min-w-0">
                <div class="w-9 h-9 bg-primary-fixed rounded-xl flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-bold text-on-surface truncate">{{ drug.drug_name }}</p>
                  <p class="text-xs text-outline truncate">{{ drug.active_ingredient }}</p>
                </div>
              </div>
              <span v-if="drug.has_interaction" class="flex-shrink-0 px-2 py-0.5 bg-error-container text-error rounded-full text-xs font-bold">
                ⚠ Tương tác
              </span>
            </div>

            <!-- Suitability score -->
            <div class="mb-3">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-outline">Độ phù hợp</span>
                <span :class="['text-xs font-bold', scoreTextColor(drug.suitability_score)]">
                  {{ drug.suitability_score }}%
                </span>
              </div>
              <div class="w-full bg-surface-container rounded-full h-1.5">
                <div
                  :class="['h-1.5 rounded-full transition-all', scoreColor(drug.suitability_score)]"
                  :style="{ width: `${drug.suitability_score}%` }"
                />
              </div>
            </div>

            <!-- Indication & dosage -->
            <p class="text-xs text-on-surface-variant mb-1 leading-relaxed">{{ drug.indication }}</p>
            <p class="text-xs font-medium text-on-surface">Liều tham khảo: {{ drug.reference_dosage }}</p>

            <!-- Warnings -->
            <div v-if="drug.warnings" class="mt-3 p-2.5 bg-error-container/30 border border-error/10 rounded-xl text-xs text-error leading-relaxed">
              {{ drug.warnings }}
            </div>

            <!-- Link to drug detail -->
            <button
              v-if="drug.drug_id"
              class="mt-3 text-xs font-medium text-primary hover:underline flex items-center gap-1"
              @click="router.push(`/drugs/${drug.drug_id}`)"
            >
              Xem chi tiết thuốc →
            </button>
          </div>
        </div>
      </div>

      <!-- See doctor warning -->
      <div class="bg-error-container/30 border border-error/10 rounded-2xl p-5 flex items-start gap-3">
        <svg class="w-5 h-5 text-error flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <p class="text-sm font-bold text-error mb-1">Khi nào cần đến bác sĩ</p>
          <p class="text-sm text-on-surface-variant leading-relaxed">{{ result.see_doctor_if }}</p>
        </div>
      </div>

      <!-- Disclaimer -->
      <p class="text-xs text-outline text-center">
        Thông tin trên chỉ mang tính tham khảo và không thay thế tư vấn của bác sĩ hay dược sĩ chuyên nghiệp.
      </p>
    </template>
  </div>
</template>
