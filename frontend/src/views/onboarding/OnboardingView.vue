<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import { onboardingApi } from '@/api/onboarding.api'
import { onboardingStep1Schema, onboardingStep2Schema, onboardingStep3Schema } from '@/schemas/onboarding.schema'
import { useOnboardingStore } from '@/stores/onboarding.store'
import type { AllergyItem, KidneyFunction, LiverFunction, MedicationItem } from '@/types/onboarding.types'

const router = useRouter()
const onboardingStore = useOnboardingStore()

const step = ref(1)
const loading = ref(false)
const parsing = ref(false)
const errorMessage = ref<string | null>(null)

const step1 = reactive({
  height_cm: null as number | null,
  weight_kg: null as number | null,
  blood_type: '',
  is_pregnant: false,
  is_breastfeeding: false,
  kidney_function: 'normal' as KidneyFunction,
  liver_function: 'normal' as LiverFunction,
})

const step2 = reactive({
  conditions_text: '',
  allergies_text: '',
  conditions: [] as string[],
  allergies: [] as AllergyItem[],
})

const step3 = reactive({
  medications_text: '',
  medications: [] as MedicationItem[],
  goals_text: '',
  health_goals: [] as string[],
})

const errors = reactive<Record<string, string>>({})

const bloodOptions = [
  { label: 'A+', value: 'A+' },
  { label: 'A-', value: 'A-' },
  { label: 'B+', value: 'B+' },
  { label: 'B-', value: 'B-' },
  { label: 'AB+', value: 'AB+' },
  { label: 'AB-', value: 'AB-' },
  { label: 'O+', value: 'O+' },
  { label: 'O-', value: 'O-' },
]

const organOptions = [
  { label: 'Bình thường', value: 'normal' },
  { label: 'Suy nhẹ', value: 'mild_impairment' },
  { label: 'Suy trung bình', value: 'moderate_impairment' },
  { label: 'Suy nặng', value: 'severe_impairment' },
]

const progress = computed(() => (step.value / 3) * 100)

function clearErrors() {
  Object.keys(errors).forEach((key) => {
    delete errors[key]
  })
  errorMessage.value = null
}

function parseJsonArray<T>(raw: string | null, fallback: T[] = []): T[] {
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T[]
  } catch {
    return fallback
  }
}

function hydrateFromStatus() {
  const status = onboardingStore.status
  if (!status) return
  step1.height_cm = status.height_cm
  step1.weight_kg = status.weight_kg
  step1.blood_type = status.blood_type ?? ''
  step1.is_pregnant = status.is_pregnant
  step1.is_breastfeeding = status.is_breastfeeding
  step1.kidney_function = status.kidney_function
  step1.liver_function = status.liver_function
  step2.conditions = parseJsonArray<string>(status.chronic_conditions)
  step2.allergies = parseJsonArray<AllergyItem>(status.allergies)
  step3.medications = parseJsonArray<MedicationItem>(status.current_medications)
  step3.health_goals = parseJsonArray<string>(status.health_goals)
  step.value = onboardingStore.currentStep
}

function validateCurrentStep() {
  clearErrors()
  try {
    if (step.value === 1) onboardingStep1Schema.parse(step1)
    if (step.value === 2) onboardingStep2Schema.parse(step2)
    if (step.value === 3) onboardingStep3Schema.parse(step3)
    return true
  } catch (error) {
    if (error instanceof z.ZodError) {
      error.issues.forEach((issue) => {
        const key = String(issue.path[0] ?? 'form')
        errors[key] = issue.message
      })
    }
    return false
  }
}

function normalizeGoals() {
  step3.health_goals = step3.goals_text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

async function parseHealthText() {
  const content = [step2.conditions_text, step2.allergies_text].filter(Boolean).join('\n')
  if (!content.trim()) return
  parsing.value = true
  clearErrors()
  try {
    const parsed = await onboardingApi.parseText(content)
    step2.conditions = parsed.conditions
    step2.allergies = parsed.allergies
  } catch {
    errorMessage.value = 'Không thể phân tích nội dung sức khỏe lúc này. Bạn vẫn có thể tiếp tục nhập tự do.'
  } finally {
    parsing.value = false
  }
}

async function submitStep() {
  if (!validateCurrentStep()) return

  loading.value = true
  clearErrors()
  try {
    if (step.value === 1) {
      await onboardingStore.saveStep1({
        ...step1,
        blood_type: step1.blood_type || null,
      })
      step.value = 2
      return
    }

    if (step.value === 2) {
      await onboardingStore.saveStep2({
        conditions_text: step2.conditions_text || null,
        allergies_text: step2.allergies_text || null,
        conditions: step2.conditions,
        allergies: step2.allergies,
      })
      step.value = 3
      return
    }

    normalizeGoals()
    await onboardingStore.complete({
      medications_text: step3.medications_text || null,
      medications: step3.medications,
      health_goals: step3.health_goals,
    })
    router.replace('/dashboard')
  } catch (error) {
    errorMessage.value = (error as { message?: string }).message ?? 'Không thể lưu thông tin. Vui lòng thử lại.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await onboardingStore.loadStatus(true)
    hydrateFromStatus()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen px-4 py-8 sm:px-6 lg:px-8 flex items-center justify-center w-full">
    <div class="w-full max-w-5xl mx-auto">
      <div class="grid gap-8 lg:grid-cols-[320px_minmax(0,1fr)] items-start">
        <aside class="glass-panel-strong rounded-[2rem] p-6">
          <div class="mb-8 flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-secondary text-white">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7z" />
              </svg>
            </div>
            <div>
              <p class="text-lg font-bold text-on-surface">Thiết lập Medis</p>
              <p class="text-sm text-outline">Hoàn thiện hồ sơ để cá nhân hóa AI và cảnh báo thuốc.</p>
            </div>
          </div>

          <div class="mb-6 rounded-full bg-white/60 p-1">
            <div class="h-2 rounded-full bg-gradient-to-r from-primary to-secondary transition-all" :style="{ width: `${progress}%` }" />
          </div>

          <div class="space-y-3">
            <div
              v-for="item in [
                { id: 1, title: 'Sức khỏe nền', desc: 'Thể trạng, thai kỳ, gan thận' },
                { id: 2, title: 'Bệnh nền và dị ứng', desc: 'Nhập tự do hoặc để AI parse' },
                { id: 3, title: 'Thuốc đang dùng và mục tiêu', desc: 'Danh sách thuốc và mục tiêu sức khỏe' },
              ]"
              :key="item.id"
              class="rounded-[1.4rem] border px-4 py-4 transition"
              :class="step === item.id ? 'border-primary bg-white/80 shadow-sm' : 'border-white/70 bg-white/45'"
            >
              <div class="flex items-start gap-3">
                <span
                  class="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold"
                  :class="step === item.id ? 'bg-primary text-white' : 'bg-surface-container text-on-surface-variant'"
                >
                  {{ item.id }}
                </span>
                <div>
                  <p class="font-semibold text-on-surface">{{ item.title }}</p>
                  <p class="text-sm text-outline">{{ item.desc }}</p>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <section class="glass-panel-strong rounded-[2rem] p-6 sm:p-8">
          <div class="mb-6">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-primary">Onboarding</p>
            <h1 class="mt-2 text-3xl font-bold tracking-tight text-on-surface">
              {{ step === 1 ? 'Tình trạng sức khỏe cơ bản' : step === 2 ? 'Bệnh nền và dị ứng thuốc' : 'Thuốc đang dùng và mục tiêu' }}
            </h1>
            <p class="mt-2 text-sm text-outline">
              {{ step === 1
                ? 'Những dữ liệu này giúp Medis đánh giá tương tác thuốc và gợi ý AI an toàn hơn.'
                : step === 2
                  ? 'Bạn có thể nhập mô tả bằng tiếng Việt. Medis sẽ hỗ trợ phân tích thành dữ liệu cấu trúc.'
                  : 'Bước cuối cùng để cá nhân hóa nhắc nhở, chatbot và gợi ý điều trị.' }}
            </p>
          </div>

          <AppAlert v-if="errorMessage" type="error" class="mb-6">{{ errorMessage }}</AppAlert>

          <div v-if="loading" class="flex min-h-[24rem] items-center justify-center">
            <div class="text-center">
              <div class="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
              <p class="mt-4 text-sm text-outline">Đang tải thông tin hồ sơ sức khỏe...</p>
            </div>
          </div>

          <form v-else class="space-y-6" @submit.prevent="submitStep">
            <Transition name="fade-slide" mode="out-in">
              <div :key="step" class="min-h-[300px]">
                <template v-if="step === 1">
                  <div class="grid gap-4 md:grid-cols-2">
                <AppInput v-model="step1.height_cm" type="number" label="Chiều cao (cm)" :error="errors.height_cm" />
                <AppInput v-model="step1.weight_kg" type="number" label="Cân nặng (kg)" :error="errors.weight_kg" />
                <AppSelect v-model="step1.blood_type" label="Nhóm máu" placeholder="Chọn nhóm máu" :options="bloodOptions" />
                <div class="grid grid-cols-2 gap-3">
                  <label class="glass-panel flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-on-surface">
                    <input v-model="step1.is_pregnant" type="checkbox" class="rounded border-outline-variant" />
                    Đang mang thai
                  </label>
                  <label class="glass-panel flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-on-surface">
                    <input v-model="step1.is_breastfeeding" type="checkbox" class="rounded border-outline-variant" />
                    Đang cho con bú
                  </label>
                </div>
                <AppSelect v-model="step1.kidney_function" label="Chức năng thận" :options="organOptions" />
                <AppSelect v-model="step1.liver_function" label="Chức năng gan" :options="organOptions" />
              </div>
                </template>

                <template v-else-if="step === 2">
                  <div class="grid gap-4">
                <AppTextarea v-model="step2.conditions_text" label="Bệnh nền / tình trạng hiện tại" placeholder="Ví dụ: Tôi bị tiểu đường type 2, tăng huyết áp, từng viêm loét dạ dày..." :rows="4" :error="errors.conditions_text" />
                <AppTextarea v-model="step2.allergies_text" label="Dị ứng thuốc" placeholder="Ví dụ: Dị ứng penicillin, nổi mẩn với ibuprofen..." :rows="3" :error="errors.allergies_text" />
                <div class="flex flex-wrap gap-3">
                  <AppButton variant="outline" :loading="parsing" @click="parseHealthText">AI phân tích nội dung</AppButton>
                  <AppButton variant="ghost" @click="step2.conditions = []; step2.allergies = []">Xóa kết quả parse</AppButton>
                </div>
                <div class="grid gap-4 md:grid-cols-2">
                  <div class="rounded-[1.4rem] border border-white/70 bg-white/55 p-4">
                    <p class="text-sm font-semibold text-on-surface">Bệnh nền đã nhận diện</p>
                    <div class="mt-3 flex flex-wrap gap-2">
                      <span v-for="condition in step2.conditions" :key="condition" class="rounded-full bg-primary-fixed px-3 py-1.5 text-xs font-semibold text-primary">
                        {{ condition }}
                      </span>
                      <p v-if="step2.conditions.length === 0" class="text-sm text-outline">Chưa có dữ liệu cấu trúc.</p>
                    </div>
                  </div>
                  <div class="rounded-[1.4rem] border border-white/70 bg-white/55 p-4">
                    <p class="text-sm font-semibold text-on-surface">Dị ứng đã nhận diện</p>
                    <div class="mt-3 space-y-2">
                      <div v-for="allergy in step2.allergies" :key="`${allergy.drug}-${allergy.reaction}`" class="rounded-2xl bg-error-container/60 px-3 py-2 text-sm text-on-surface">
                        <p class="font-semibold">{{ allergy.drug }}</p>
                        <p v-if="allergy.reaction" class="text-xs text-on-surface-variant">{{ allergy.reaction }}</p>
                      </div>
                      <p v-if="step2.allergies.length === 0" class="text-sm text-outline">Chưa có dữ liệu cấu trúc.</p>
                    </div>
                  </div>
                </div>
              </div>
                </template>

                <template v-else>
                  <div class="grid gap-4">
                <AppTextarea v-model="step3.medications_text" label="Thuốc đang dùng" placeholder="Ví dụ: Metformin 500mg ngày 2 lần, Amlodipine 5mg mỗi sáng..." :rows="4" :error="errors.medications_text" />
                <AppTextarea v-model="step3.goals_text" label="Mục tiêu sức khỏe" placeholder="Ví dụ: kiểm soát đường huyết, ngủ tốt hơn, giảm đau khớp" :rows="3" :error="errors.goals_text" />
                <div class="rounded-[1.4rem] border border-white/70 bg-white/55 p-4">
                  <p class="text-sm font-semibold text-on-surface">Danh sách mục tiêu sẽ lưu</p>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span
                      v-for="goal in step3.goals_text.split(',').map((item) => item.trim()).filter(Boolean)"
                      :key="goal"
                      class="rounded-full bg-tertiary-fixed px-3 py-1.5 text-xs font-semibold text-tertiary"
                    >
                      {{ goal }}
                    </span>
                    <p v-if="step3.goals_text.trim().length === 0" class="text-sm text-outline">Mục tiêu sức khỏe có thể để trống và bổ sung sau.</p>
                  </div>
                </div>
                  </div>
                </template>
              </div>
            </Transition>

            <div class="flex flex-col gap-3 border-t border-white/70 pt-6 sm:flex-row sm:items-center sm:justify-between">
              <AppButton v-if="step > 1" variant="ghost" @click="step -= 1">Quay lại</AppButton>
              <div class="flex items-center gap-3 sm:ml-auto">
                <p class="text-sm text-outline">Bước {{ step }}/3</p>
                <AppButton type="submit" variant="gradient" :loading="loading">
                  {{ step === 3 ? 'Hoàn tất thiết lập' : 'Tiếp tục' }}
                </AppButton>
              </div>
            </div>
          </form>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
