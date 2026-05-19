<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import {
  useCreateHealthVisitMutation,
  useDeleteHealthVisitMutation,
  useHealthSummary,
  useHealthVisits,
  useUpdateHealthBaselineMutation,
} from '@/api/health.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { healthProfileSchema } from '@/schemas/health-profile.schema'
import { formatDate } from '@/utils/format'
import type {
  CreateHealthProfileRequest,
  HealthBaselineStructured,
  HealthProfileSearchParams,
  UpdateHealthBaselineRequest,
} from '@/types/health-profile.types'
import type { AllergyItem, KidneyFunction, LiverFunction, MedicationItem } from '@/types/onboarding.types'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
import AppTabNav from '@/components/ui/AppTabNav.vue'

const router = useRouter()
const toast = useToast()
const { open: confirmOpen, onConfirm, onCancel, confirm } = useConfirm()
const { page, size, params: paginationParams, setPage, setSize } = usePagination()

const activeTab = ref<'baseline' | 'visits'>('baseline')
const visitViewMode = ref<'timeline' | 'table'>('timeline')
const search = ref('')
const deletingId = ref<string | null>(null)

const queryParams = computed<HealthProfileSearchParams>(() => ({
  ...paginationParams.value,
  search: search.value || undefined,
}))

const { data: summary, isLoading: loadingSummary } = useHealthSummary()
const { data: visitsData, isLoading: loadingVisits } = useHealthVisits(queryParams)
const { mutate: updateBaseline, isPending: updatingBaseline } = useUpdateHealthBaselineMutation()
const { mutate: createVisit, isPending: creatingVisit } = useCreateHealthVisitMutation()
const { mutate: deleteHealthVisit, isPending: deleting } = useDeleteHealthVisitMutation()

const showVisitModal = ref(false)
const showBaselineModal = ref(false)
const visitFormErrors = reactive<Record<string, string>>({})
const visitForm = reactive({
  diagnosis_name: '',
  exam_date: '',
  facility: '',
  doctor: '',
  symptoms: '',
  conclusion: '',
  notes: '',
})
const baselineForm = reactive({
  height_cm: null as number | null,
  weight_kg: null as number | null,
  blood_type: '',
  chronic_conditions_text: '',
  allergies_text: '',
  current_medications_text: '',
  is_pregnant: false,
  is_breastfeeding: false,
  kidney_function: 'normal' as KidneyFunction,
  liver_function: 'normal' as LiverFunction,
  health_goals_text: '',
})

const organOptions = [
  { label: 'Bình thường', value: 'normal' },
  { label: 'Suy nhẹ', value: 'mild_impairment' },
  { label: 'Suy trung bình', value: 'moderate_impairment' },
  { label: 'Suy nặng', value: 'severe_impairment' },
]
const organLabels: Record<string, string> = {
  normal: 'Bình thường',
  mild_impairment: 'Suy nhẹ',
  moderate_impairment: 'Suy trung bình',
  severe_impairment: 'Suy nặng',
}
const organColors: Record<string, string> = {
  normal: 'background:rgba(16,185,129,0.1);color:#059669;',
  mild_impairment: 'background:rgba(245,158,11,0.1);color:#D97706;',
  moderate_impairment: 'background:rgba(249,115,22,0.1);color:#EA580C;',
  severe_impairment: 'background:rgba(239,68,68,0.1);color:#DC2626;',
}

function bmi(h: number | null, w: number | null): string | null {
  if (!h || !w) return null
  const val = w / ((h / 100) ** 2)
  return val.toFixed(1)
}
function bmiLabel(val: string | null): { label: string; style: string } {
  if (!val) return { label: '—', style: 'background:rgba(15,23,42,0.06);color:#6B7280;' }
  const n = parseFloat(val)
  if (n < 18.5) return { label: 'Thiếu cân', style: 'background:rgba(0,104,93,0.1);color:#00685d;' }
  if (n < 25) return { label: 'Bình thường', style: 'background:rgba(16,185,129,0.1);color:#059669;' }
  if (n < 30) return { label: 'Thừa cân', style: 'background:rgba(245,158,11,0.1);color:#D97706;' }
  return { label: 'Béo phì', style: 'background:rgba(239,68,68,0.1);color:#DC2626;' }
}

function openBaselineEditor() {
  const data = baseline.value
  if (data) {
    baselineForm.height_cm = data.height_cm
    baselineForm.weight_kg = data.weight_kg
    baselineForm.blood_type = data.blood_type ?? ''
    baselineForm.is_pregnant = data.is_pregnant ?? false
    baselineForm.is_breastfeeding = data.is_breastfeeding ?? false
    baselineForm.kidney_function = (data.kidney_function as KidneyFunction) ?? 'normal'
    baselineForm.liver_function = (data.liver_function as LiverFunction) ?? 'normal'
    baselineForm.chronic_conditions_text = data.chronic_conditions?.join(', ') ?? ''
    baselineForm.allergies_text = data.allergies?.map((a: AllergyItem) => a.reaction ? `${a.drug} - ${a.reaction}` : a.drug).join('\n') ?? ''
    baselineForm.current_medications_text = data.current_medications?.map((m: MedicationItem) => [m.name, m.dosage, m.frequency].filter(Boolean).join(' | ')).join('\n') ?? ''
    baselineForm.health_goals_text = data.health_goals?.join(', ') ?? ''
  }
  showBaselineModal.value = true
}

function parseCommaList(text: string): string[] {
  return text.split(',').map(s => s.trim()).filter(Boolean)
}

function parseAllergies(text: string): AllergyItem[] {
  return text.split('\n').map(line => {
    const [drug = '', reaction] = line.split('-').map(p => p.trim())
    return { drug, reaction: reaction || null }
  }).filter(item => item.drug)
}

function parseMedications(text: string): MedicationItem[] {
  return text.split('\n').map(line => {
    const [name = '', dosage, frequency] = line.split('|').map(part => part.trim())
    return { name, dosage: dosage || null, frequency: frequency || null }
  }).filter(item => item.name)
}

function resetVisitForm() {
  Object.keys(visitForm).forEach(key => { (visitForm as Record<string, string>)[key] = '' })
  Object.keys(visitFormErrors).forEach(key => delete visitFormErrors[key])
}

function validateVisitForm() {
  Object.keys(visitFormErrors).forEach(key => delete visitFormErrors[key])
  try {
    healthProfileSchema.parse(visitForm)
    return true
  } catch (error) {
    if (error instanceof z.ZodError) {
      error.issues.forEach(issue => {
        if (issue.path[0]) visitFormErrors[issue.path[0] as string] = issue.message
      })
    }
    return false
  }
}

function submitVisitForm() {
  if (!validateVisitForm()) return
  const payload: CreateHealthProfileRequest = {
    diagnosis_name: visitForm.diagnosis_name,
    exam_date: visitForm.exam_date,
    ...(visitForm.facility ? { facility: visitForm.facility } : {}),
    ...(visitForm.doctor ? { doctor: visitForm.doctor } : {}),
    ...(visitForm.symptoms ? { symptoms: visitForm.symptoms } : {}),
    ...(visitForm.conclusion ? { conclusion: visitForm.conclusion } : {}),
    ...(visitForm.notes ? { notes: visitForm.notes } : {}),
  }
  createVisit(payload, {
    onSuccess: () => {
      toast.success('Tạo lần khám thành công')
      showVisitModal.value = false
      activeTab.value = 'visits'
      resetVisitForm()
    },
    onError: (error) => toast.error((error as { message?: string })?.message || 'Tạo lần khám thất bại'),
  })
}

function submitBaselineForm() {
  const payload: UpdateHealthBaselineRequest = {
    height_cm: baselineForm.height_cm,
    weight_kg: baselineForm.weight_kg,
    blood_type: baselineForm.blood_type || null,
    chronic_conditions: parseCommaList(baselineForm.chronic_conditions_text),
    allergies: parseAllergies(baselineForm.allergies_text),
    current_medications: parseMedications(baselineForm.current_medications_text),
    is_pregnant: baselineForm.is_pregnant,
    is_breastfeeding: baselineForm.is_breastfeeding,
    kidney_function: baselineForm.kidney_function,
    liver_function: baselineForm.liver_function,
    health_goals: parseCommaList(baselineForm.health_goals_text),
  }
  updateBaseline(payload, {
    onSuccess: () => {
      toast.success('Đã cập nhật hồ sơ sức khỏe nền')
      showBaselineModal.value = false
    },
    onError: (error) => toast.error((error as { message?: string })?.message || 'Cập nhật hồ sơ thất bại'),
  })
}

async function deleteVisit(id: string) {
  deletingId.value = id
  const confirmed = await confirm()
  if (!confirmed) { deletingId.value = null; return }
  deleteHealthVisit(id, {
    onSuccess: () => toast.success('Đã xóa lần khám'),
    onError: () => toast.error('Không thể xóa lần khám này'),
    onSettled: () => { deletingId.value = null },
  })
}

const baseline = computed(() => summary.value?.baseline)
const bmiVal = computed(() => bmi(baseline.value?.height_cm ?? null, baseline.value?.weight_kg ?? null))
const bmiMeta = computed(() => bmiLabel(bmiVal.value))

const mainTabs = computed(() => [
  { key: 'baseline', label: 'Sức Khoẻ Cơ Bản' },
  { key: 'visits', label: 'Lịch Sử Khám', count: summary.value?.total_visits ?? 0 },
])
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-start justify-between flex-wrap gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-widest mb-1" style="color:#00685d;">Hồ sơ y tế</p>
        <h1 class="text-3xl font-extrabold" style="color:#0A0F1E;">Hồ Sơ Sức Khoẻ</h1>
        <p class="text-sm mt-1" style="color:#4B5563;">Thông tin nền tảng và lịch sử khám bệnh</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-semibold transition-all hover:bg-gray-50"
          style="border-color:rgba(15,23,42,0.12);color:#1F2937;"
          @click="openBaselineEditor"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
          Cập nhật bệnh nền
        </button>
        <button
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-95"
          style="background:linear-gradient(135deg,#00685d,#00897B);box-shadow:0 4px 14px rgba(0,104,93,0.28);"
          @click="showVisitModal = true; resetVisitForm()"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Thêm lần khám
        </button>
      </div>
    </div>

    <!-- Summary stats -->
    <div v-if="loadingSummary" class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <AppSkeleton v-for="i in 4" :key="i" class="h-20 rounded-2xl" />
    </div>
    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="rounded-2xl p-4" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
        <p class="text-xs font-medium mb-1" style="color:#6B7280;">Tổng lần khám</p>
        <p class="text-2xl font-extrabold" style="color:#0A0F1E;">{{ summary?.total_visits ?? 0 }}</p>
      </div>
      <div class="rounded-2xl p-4" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
        <p class="text-xs font-medium mb-1" style="color:#6B7280;">Đơn đang dùng</p>
        <p class="text-2xl font-extrabold" style="color:#00685d;">{{ summary?.active_prescriptions ?? 0 }}</p>
      </div>
      <div class="rounded-2xl p-4" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
        <p class="text-xs font-medium mb-1" style="color:#6B7280;">Nhắc thuốc hoạt động</p>
        <p class="text-2xl font-extrabold" style="color:#0A0F1E;">{{ summary?.active_reminders ?? 0 }}</p>
      </div>
      <div class="rounded-2xl p-4" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
        <p class="text-xs font-medium mb-1" style="color:#6B7280;">Khám gần nhất</p>
        <p class="text-sm font-bold" style="color:#0A0F1E;">{{ summary?.last_exam_date ? formatDate(summary.last_exam_date) : '—' }}</p>
      </div>
    </div>

    <!-- Tab nav -->
    <div class="flex gap-1 p-1 rounded-xl w-fit" style="background:rgba(15,23,42,0.05);">
      <button
        v-for="tab in mainTabs"
        :key="tab.key"
        @click="activeTab = tab.key as 'baseline' | 'visits'"
        :class="['flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all', activeTab === tab.key ? 'bg-white shadow-sm' : 'hover:bg-white/60']"
        :style="activeTab === tab.key ? 'color:#0A0F1E;' : 'color:#4B5563;'"
      >
        {{ tab.label }}
        <span v-if="tab.count !== undefined && tab.count > 0" class="text-xs font-bold px-1.5 py-0.5 rounded-full" :style="activeTab === tab.key ? 'background:rgba(0,104,93,0.1);color:#00685d;' : 'background:rgba(15,23,42,0.08);color:#6B7280;'">
          {{ tab.count }}
        </span>
      </button>
    </div>

    <!-- Baseline tab -->
    <section v-if="activeTab === 'baseline'">
      <div v-if="loadingSummary" class="space-y-4">
        <AppSkeleton v-for="i in 3" :key="i" class="h-36 rounded-2xl" />
      </div>

      <div v-else-if="baseline" class="grid gap-5 lg:grid-cols-[1fr_320px]">
        <!-- Left column -->
        <div class="space-y-5">
          <!-- Biometric hero -->
          <div class="rounded-2xl overflow-hidden" style="background:linear-gradient(135deg,rgba(0,104,93,0.07),rgba(0,104,93,0.04));border:1px solid rgba(0,104,93,0.15);">
            <div class="p-5">
              <div class="flex items-center justify-between mb-4">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-widest mb-0.5" style="color:#00685d;">Chỉ số cơ thể</p>
                  <h2 class="text-lg font-bold" style="color:#0A0F1E;">Chỉ số nền</h2>
                </div>
                <span class="px-3 py-1.5 rounded-full text-sm font-bold" :style="bmiMeta.style">
                  BMI {{ bmiVal }} · {{ bmiMeta.label }}
                </span>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div class="rounded-xl p-3 text-center" style="background:rgba(255,255,255,0.7);">
                  <p class="text-2xl font-extrabold" style="color:#0A0F1E;">{{ baseline.height_cm ?? '—' }}</p>
                  <p class="text-xs mt-0.5" style="color:#6B7280;">Chiều cao (cm)</p>
                </div>
                <div class="rounded-xl p-3 text-center" style="background:rgba(255,255,255,0.7);">
                  <p class="text-2xl font-extrabold" style="color:#0A0F1E;">{{ baseline.weight_kg ?? '—' }}</p>
                  <p class="text-xs mt-0.5" style="color:#6B7280;">Cân nặng (kg)</p>
                </div>
                <div class="rounded-xl p-3 text-center" style="background:rgba(255,255,255,0.7);">
                  <p class="text-2xl font-extrabold" style="color:#DC2626;">{{ baseline.blood_type ?? '—' }}</p>
                  <p class="text-xs mt-0.5" style="color:#6B7280;">Nhóm máu</p>
                </div>
                <div class="rounded-xl p-3 text-center" style="background:rgba(255,255,255,0.7);">
                  <p class="text-sm font-bold pt-1" style="color:#0A0F1E;">{{ baseline.is_pregnant ? 'Thai kỳ' : baseline.is_breastfeeding ? 'Cho con bú' : '—' }}</p>
                  <p class="text-xs mt-0.5" style="color:#6B7280;">Tình trạng</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Organ function -->
          <div class="rounded-2xl p-5" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-semibold" style="color:#0A0F1E;">Chức năng cơ quan</h2>
              <span class="text-xs" style="color:#9CA3AF;">Cập nhật gần nhất</span>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div class="rounded-xl p-3" style="background:rgba(15,23,42,0.02);border:1px solid rgba(15,23,42,0.06);">
                <p class="text-xs font-medium mb-2" style="color:#6B7280;">Chức năng thận</p>
                <span class="px-2.5 py-1 rounded-full text-xs font-bold" :style="organColors[baseline.kidney_function] ?? organColors.normal">
                  {{ organLabels[baseline.kidney_function] }}
                </span>
              </div>
              <div class="rounded-xl p-3" style="background:rgba(15,23,42,0.02);border:1px solid rgba(15,23,42,0.06);">
                <p class="text-xs font-medium mb-2" style="color:#6B7280;">Chức năng gan</p>
                <span class="px-2.5 py-1 rounded-full text-xs font-bold" :style="organColors[baseline.liver_function] ?? organColors.normal">
                  {{ organLabels[baseline.liver_function] }}
                </span>
              </div>
            </div>
          </div>

          <!-- Conditions & allergies -->
          <div class="rounded-2xl p-5" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-semibold" style="color:#0A0F1E;">Bệnh nền & Dị ứng</h2>
              <button class="text-sm font-semibold" style="color:#00685d;" @click="openBaselineEditor">Sửa</button>
            </div>

            <p class="text-xs font-semibold uppercase tracking-wider mb-2" style="color:#9CA3AF;">Bệnh nền</p>
            <div v-if="baseline.chronic_conditions?.length" class="flex flex-wrap gap-2 mb-4">
              <span v-for="c in baseline.chronic_conditions" :key="c" class="px-3 py-1 rounded-full text-sm font-medium" style="background:rgba(57,73,171,0.1);color:#3949AB;">
                {{ c }}
              </span>
            </div>
            <p v-else class="text-sm mb-4" style="color:#9CA3AF;">Chưa có bệnh nền được ghi nhận.</p>

            <p class="text-xs font-semibold uppercase tracking-wider mb-2" style="color:#9CA3AF;">Dị ứng thuốc</p>
            <div v-if="baseline.allergies?.length" class="space-y-2">
              <div v-for="a in baseline.allergies" :key="a.drug" class="rounded-xl px-4 py-3" style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.15);">
                <p class="text-sm font-semibold" style="color:#DC2626;">{{ a.drug }}</p>
                <p v-if="a.reaction" class="text-xs mt-0.5" style="color:#4B5563;">{{ a.reaction }}</p>
              </div>
            </div>
            <p v-else class="text-sm" style="color:#9CA3AF;">Chưa ghi nhận dị ứng thuốc.</p>
          </div>

          <!-- Current medications -->
          <div class="rounded-2xl p-5" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
            <h2 class="font-semibold mb-4" style="color:#0A0F1E;">Thuốc đang dùng (tự khai báo)</h2>
            <div v-if="baseline.current_medications?.length" class="space-y-2">
              <div v-for="m in baseline.current_medications" :key="m.name" class="flex items-center gap-3 px-4 py-3 rounded-xl" style="background:rgba(15,23,42,0.02);border:1px solid rgba(15,23,42,0.06);">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style="background:rgba(0,104,93,0.08);">
                  <svg class="w-4 h-4" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold" style="color:#0A0F1E;">{{ m.name }}</p>
                  <p class="text-xs" style="color:#6B7280;">{{ [m.dosage, m.frequency].filter(Boolean).join(' · ') || 'Chưa có liều / tần suất' }}</p>
                </div>
              </div>
            </div>
            <p v-else class="text-sm" style="color:#9CA3AF;">Chưa có thuốc tự khai báo.</p>
            <button class="mt-3 text-sm font-semibold" style="color:#00685d;" @click="router.push('/profile/prescriptions')">
              Quản lý đơn thuốc cá nhân →
            </button>
          </div>
        </div>

        <!-- Right column -->
        <div class="space-y-5">
          <!-- Health goals -->
          <div class="rounded-2xl p-5" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
            <h2 class="font-semibold mb-4" style="color:#0A0F1E;">Mục tiêu sức khoẻ</h2>
            <div v-if="baseline.health_goals?.length" class="space-y-2">
              <div v-for="goal in baseline.health_goals" :key="goal" class="flex items-center gap-3 py-2">
                <div class="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style="background:rgba(16,185,129,0.1);">
                  <svg class="w-3 h-3" style="color:#059669;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                </div>
                <span class="text-sm" style="color:#1F2937;">{{ goal }}</span>
              </div>
            </div>
            <p v-else class="text-sm" style="color:#9CA3AF;">Chưa có mục tiêu sức khoẻ.</p>
          </div>

          <!-- Quick links -->
          <div class="rounded-2xl p-5" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
            <h2 class="font-semibold mb-3" style="color:#0A0F1E;">Truy cập nhanh</h2>
            <div class="space-y-2">
              <button class="w-full flex items-center gap-3 p-3 rounded-xl transition-all hover:bg-gray-50 text-left" style="border:1px solid rgba(15,23,42,0.06);" @click="router.push('/profile/prescriptions')">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:rgba(0,104,93,0.08);">
                  <svg class="w-4 h-4" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                </div>
                <div class="flex-1">
                  <p class="text-sm font-semibold" style="color:#0A0F1E;">Đơn thuốc cá nhân</p>
                  <p class="text-xs" style="color:#6B7280;">{{ summary?.active_prescriptions ?? 0 }} đơn đang dùng</p>
                </div>
                <svg class="w-4 h-4" style="color:#9CA3AF;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
              </button>
              <button class="w-full flex items-center gap-3 p-3 rounded-xl transition-all hover:bg-gray-50 text-left" style="border:1px solid rgba(15,23,42,0.06);" @click="router.push('/schedule')">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background:rgba(16,185,129,0.08);">
                  <svg class="w-4 h-4" style="color:#059669;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <div class="flex-1">
                  <p class="text-sm font-semibold" style="color:#0A0F1E;">Lịch uống thuốc</p>
                  <p class="text-xs" style="color:#6B7280;">{{ summary?.active_reminders ?? 0 }} nhắc đang hoạt động</p>
                </div>
                <svg class="w-4 h-4" style="color:#9CA3AF;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty baseline -->
      <div v-else class="flex flex-col items-center justify-center py-20 rounded-2xl border" style="background:white;border-color:rgba(15,23,42,0.08);">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style="background:rgba(0,104,93,0.08);">
          <svg class="w-8 h-8" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
        </div>
        <p class="text-base font-semibold mb-1" style="color:#0A0F1E;">Chưa có dữ liệu sức khỏe nền</p>
        <p class="text-sm mb-4" style="color:#6B7280;">Thêm thông tin để được tư vấn thuốc chính xác hơn</p>
        <button class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style="background:linear-gradient(135deg,#00685d,#00897B);" @click="openBaselineEditor">
          Cập nhật ngay
        </button>
      </div>
    </section>

    <!-- Visits tab -->
    <section v-else class="space-y-5">
      <!-- Summary bar -->
      <div class="flex items-center justify-between p-4 rounded-2xl" style="background:white;border:1px solid rgba(15,23,42,0.08);">
        <div class="flex items-center gap-6 text-sm" style="color:#4B5563;">
          <span><strong style="color:#0A0F1E;">{{ summary?.total_visits ?? 0 }}</strong> lần khám</span>
          <span v-if="summary?.last_exam_date">Lần gần nhất: <strong style="color:#0A0F1E;">{{ formatDate(summary.last_exam_date) }}</strong></span>
          <span><strong style="color:#00685d;">{{ summary?.active_prescriptions ?? 0 }}</strong> đơn thuốc đang dùng</span>
        </div>
        <!-- Search -->
        <div class="relative w-56">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style="color:#9CA3AF;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <input v-model="search" type="text" placeholder="Tìm kiếm..." class="w-full pl-9 pr-3 py-2 rounded-xl text-sm focus:outline-none" style="background:rgba(15,23,42,0.04);border:1px solid rgba(15,23,42,0.08);color:#0A0F1E;" />
        </div>
      </div>

      <div v-if="loadingVisits" class="space-y-4">
        <AppSkeleton v-for="i in 3" :key="i" class="h-28 rounded-2xl" />
      </div>

      <div v-else-if="!visitsData?.items.length" class="flex flex-col items-center justify-center py-20 rounded-2xl border" style="background:white;border-color:rgba(15,23,42,0.08);">
        <div class="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style="background:rgba(0,104,93,0.08);">
          <svg class="w-7 h-7" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
        </div>
        <p class="text-base font-semibold mb-1" style="color:#0A0F1E;">Chưa có lịch sử khám bệnh</p>
        <p class="text-sm mb-4" style="color:#6B7280;">Thêm lần khám đầu tiên để bắt đầu theo dõi sức khoẻ</p>
        <button class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style="background:linear-gradient(135deg,#00685d,#00897B);" @click="showVisitModal = true; resetVisitForm()">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Thêm lần khám đầu tiên
        </button>
      </div>

      <!-- Timeline -->
      <div v-else class="relative">
        <div class="absolute left-6 top-0 bottom-0 w-0.5" style="background:rgba(0,104,93,0.15);" />
        <div class="space-y-5">
          <div v-for="(profile, idx) in visitsData.items" :key="profile.id" class="relative pl-16">
            <!-- Timeline dot -->
            <div class="absolute left-4 top-6 w-4 h-4 rounded-full border-2 border-white flex items-center justify-center" :style="idx === 0 ? 'background:#00685d;box-shadow:0 0 0 3px rgba(0,104,93,0.2);' : 'background:#D1D5DB;'">
              <div class="w-1.5 h-1.5 rounded-full bg-white" />
            </div>
            <!-- Date on rail -->
            <div class="absolute left-0 top-5 w-10 text-center">
              <span class="text-xs font-bold" style="color:#00685d;font-size:9px;line-height:1.2;">
                {{ formatDate(profile.exam_date).slice(3) }}
              </span>
            </div>

            <div class="rounded-2xl p-5 transition-all hover:shadow-md" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 3px rgba(15,23,42,0.05);">
              <div class="flex items-start justify-between gap-3 flex-wrap">
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium mb-1" style="color:#6B7280;">{{ formatDate(profile.exam_date) }}</p>
                  <h3 class="text-base font-bold" style="color:#0A0F1E;">{{ profile.diagnosis_name }}</h3>
                  <div class="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-xs" style="color:#4B5563;">
                    <span v-if="profile.facility">Cơ sở: <strong style="color:#1F2937;">{{ profile.facility }}</strong></span>
                    <span v-if="profile.doctor">Bác sĩ: <strong style="color:#1F2937;">{{ profile.doctor }}</strong></span>
                  </div>
                  <p v-if="profile.conclusion" class="mt-2 text-sm line-clamp-2" style="color:#4B5563;">{{ profile.conclusion }}</p>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <button
                    @click="router.push(`/profile/health/${profile.id}`)"
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all"
                    style="border-color:rgba(0,104,93,0.25);color:#00685d;background:rgba(0,104,93,0.05);"
                  >Xem chi tiết</button>
                  <button
                    @click="deleteVisit(profile.id as string)"
                    :disabled="deleting && deletingId === profile.id"
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all disabled:opacity-50"
                    style="border-color:rgba(239,68,68,0.3);color:#EF4444;"
                  >Xóa</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="visitsData?.meta && visitsData.meta.total_pages > 1" class="rounded-2xl border px-5" style="background:white;border-color:rgba(15,23,42,0.08);">
        <AppPagination :meta="visitsData.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </section>

    <!-- Baseline modal -->
    <AppModal :open="showBaselineModal" title="Cập nhật bệnh nền & dị ứng" size="lg" @close="showBaselineModal = false">
      <form @submit.prevent="submitBaselineForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="baselineForm.height_cm" type="number" label="Chiều cao (cm)" />
          <AppInput v-model="baselineForm.weight_kg" type="number" label="Cân nặng (kg)" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="baselineForm.blood_type" label="Nhóm máu" placeholder="VD: O+" />
          <div>
            <label class="text-sm font-medium block mb-1.5" style="color:#0A0F1E;">Chức năng thận</label>
            <select v-model="baselineForm.kidney_function" class="w-full px-3 py-2.5 rounded-xl text-sm focus:outline-none" style="background:rgba(15,23,42,0.04);border:1px solid rgba(15,23,42,0.1);color:#0A0F1E;">
              <option v-for="opt in organOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
        </div>
        <div>
          <label class="text-sm font-medium block mb-1.5" style="color:#0A0F1E;">Chức năng gan</label>
          <select v-model="baselineForm.liver_function" class="w-full px-3 py-2.5 rounded-xl text-sm focus:outline-none" style="background:rgba(15,23,42,0.04);border:1px solid rgba(15,23,42,0.1);color:#0A0F1E;">
            <option v-for="opt in organOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="flex items-center gap-3 rounded-xl border px-4 py-3 text-sm cursor-pointer" style="border-color:rgba(15,23,42,0.1);color:#0A0F1E;">
            <input v-model="baselineForm.is_pregnant" type="checkbox" class="rounded" />
            Đang mang thai
          </label>
          <label class="flex items-center gap-3 rounded-xl border px-4 py-3 text-sm cursor-pointer" style="border-color:rgba(15,23,42,0.1);color:#0A0F1E;">
            <input v-model="baselineForm.is_breastfeeding" type="checkbox" class="rounded" />
            Đang cho con bú
          </label>
        </div>
        <AppTextarea v-model="baselineForm.chronic_conditions_text" label="Bệnh nền" placeholder="Nhập cách nhau bằng dấu phẩy, ví dụ: Tăng huyết áp, Đái tháo đường type 2" :rows="2" />
        <AppTextarea v-model="baselineForm.allergies_text" label="Dị ứng thuốc" placeholder="Mỗi dòng một dị ứng, ví dụ: Penicillin - nổi mẩn" :rows="3" />
        <AppTextarea v-model="baselineForm.current_medications_text" label="Thuốc đang dùng tự khai báo" placeholder="Mỗi dòng: Tên thuốc | liều | tần suất" :rows="3" />
        <AppTextarea v-model="baselineForm.health_goals_text" label="Mục tiêu sức khoẻ" placeholder="Nhập cách nhau bằng dấu phẩy" :rows="2" />
      </form>
      <template #footer>
        <AppButton variant="ghost" @click="showBaselineModal = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="updatingBaseline" @click="submitBaselineForm">Lưu hồ sơ</AppButton>
      </template>
    </AppModal>

    <!-- Visit modal -->
    <AppModal :open="showVisitModal" title="Thêm lần khám" size="lg" @close="showVisitModal = false">
      <form @submit.prevent="submitVisitForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="visitForm.diagnosis_name" label="Chẩn đoán" placeholder="VD: Viêm họng cấp" :error="visitFormErrors.diagnosis_name" required />
          <AppInput v-model="visitForm.exam_date" type="date" label="Ngày khám" :error="visitFormErrors.exam_date" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="visitForm.facility" label="Cơ sở y tế" placeholder="Bệnh viện..." />
          <AppInput v-model="visitForm.doctor" label="Bác sĩ" placeholder="BS. Nguyễn..." />
        </div>
        <AppTextarea v-model="visitForm.symptoms" label="Triệu chứng" placeholder="Mô tả triệu chứng..." :rows="2" />
        <AppTextarea v-model="visitForm.conclusion" label="Kết luận" placeholder="Kết luận khám..." :rows="2" />
        <AppTextarea v-model="visitForm.notes" label="Ghi chú" placeholder="Ghi chú thêm..." :rows="2" />
      </form>
      <template #footer>
        <AppButton variant="ghost" @click="showVisitModal = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="creatingVisit" @click="submitVisitForm">Lưu lần khám</AppButton>
      </template>
    </AppModal>

    <AppConfirmDialog :open="confirmOpen" title="Xóa lần khám" message="Bạn có chắc muốn xóa lần khám này?" danger :loading="deleting" @confirm="onConfirm" @cancel="onCancel" />
  </div>
</template>
