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

const visitTabs = [
  { key: 'timeline', label: 'Dòng thời gian' },
  { key: 'table', label: 'Bảng danh sách' },
]
const mainTabs = computed(() => [
  { key: 'baseline', label: 'Bệnh nền & dị ứng' },
  { key: 'visits', label: 'Lịch sử khám', count: summary.value?.total_visits ?? 0 },
])
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

function resetVisitForm() {
  Object.keys(visitForm).forEach((key) => {
    ;(visitForm as Record<string, string>)[key] = ''
  })
  Object.keys(visitFormErrors).forEach((key) => delete visitFormErrors[key])
}

function validateVisitForm() {
  Object.keys(visitFormErrors).forEach((key) => delete visitFormErrors[key])
  try {
    healthProfileSchema.parse(visitForm)
    return true
  } catch (error) {
    if (error instanceof z.ZodError) {
      error.issues.forEach((issue) => {
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

function hydrateBaselineForm(baseline?: HealthBaselineStructured) {
  baselineForm.height_cm = baseline?.height_cm ?? null
  baselineForm.weight_kg = baseline?.weight_kg ?? null
  baselineForm.blood_type = baseline?.blood_type ?? ''
  baselineForm.chronic_conditions_text = baseline?.chronic_conditions.join(', ') ?? ''
  baselineForm.allergies_text = baseline?.allergies
    .map((item) => [item.drug, item.reaction].filter(Boolean).join(' - '))
    .join('\n') ?? ''
  baselineForm.current_medications_text = baseline?.current_medications
    .map((item) => [item.name, item.dosage, item.frequency].filter(Boolean).join(' | '))
    .join('\n') ?? ''
  baselineForm.is_pregnant = baseline?.is_pregnant ?? false
  baselineForm.is_breastfeeding = baseline?.is_breastfeeding ?? false
  baselineForm.kidney_function = baseline?.kidney_function ?? 'normal'
  baselineForm.liver_function = baseline?.liver_function ?? 'normal'
  baselineForm.health_goals_text = baseline?.health_goals.join(', ') ?? ''
}

function openBaselineEditor() {
  hydrateBaselineForm(summary.value?.baseline)
  showBaselineModal.value = true
}

function parseCommaList(value: string) {
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}

function parseAllergies(value: string): AllergyItem[] {
  return value.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
    const [drug = '', ...reactionParts] = line.split('-').map((part) => part.trim())
    return { drug, reaction: reactionParts.join(' - ') || null }
  }).filter((item) => item.drug)
}

function parseMedications(value: string): MedicationItem[] {
  return value.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
    const [name = '', dosage, frequency] = line.split('|').map((part) => part.trim())
    return { name, dosage: dosage || null, frequency: frequency || null }
  }).filter((item) => item.name)
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
  if (!confirmed) {
    deletingId.value = null
    return
  }
  deleteHealthVisit(id, {
    onSuccess: () => toast.success('Đã xóa lần khám'),
    onError: () => toast.error('Không thể xóa lần khám này'),
    onSettled: () => { deletingId.value = null },
  })
}

const baseline = computed(() => summary.value?.baseline)
const hasStaticData = computed(() => {
  const data = baseline.value
  if (!data) return false
  return Boolean(
    data.height_cm || data.weight_kg || data.blood_type ||
    data.chronic_conditions.length || data.allergies.length ||
    data.current_medications.length || data.health_goals.length,
  )
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-on-surface">Sức khỏe của tôi</h1>
        <p class="text-sm text-outline mt-0.5">Quản lý bệnh nền, dị ứng và lịch sử khám bệnh</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <AppButton variant="outline" @click="openBaselineEditor">
          Cập nhật bệnh nền
        </AppButton>
        <AppButton variant="gradient" @click="showVisitModal = true; resetVisitForm()">
          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Thêm lần khám
        </AppButton>
      </div>
    </div>

    <div v-if="loadingSummary" class="grid gap-4 md:grid-cols-4">
      <AppSkeleton v-for="i in 4" :key="i" class="h-24 rounded-2xl" />
    </div>
    <div v-else class="grid gap-4 md:grid-cols-4">
      <div class="bg-card rounded-2xl border border-outline-variant p-4 shadow-sm">
        <p class="text-xs text-outline mb-1">Lần khám</p>
        <p class="text-2xl font-bold text-on-surface">{{ summary?.total_visits ?? 0 }}</p>
      </div>
      <div class="bg-card rounded-2xl border border-outline-variant p-4 shadow-sm">
        <p class="text-xs text-outline mb-1">Đơn thuốc đang dùng</p>
        <p class="text-2xl font-bold text-on-surface">{{ summary?.active_prescriptions ?? 0 }}</p>
      </div>
      <div class="bg-card rounded-2xl border border-outline-variant p-4 shadow-sm">
        <p class="text-xs text-outline mb-1">Nhắc thuốc hoạt động</p>
        <p class="text-2xl font-bold text-on-surface">{{ summary?.active_reminders ?? 0 }}</p>
      </div>
      <div class="bg-card rounded-2xl border border-outline-variant p-4 shadow-sm">
        <p class="text-xs text-outline mb-1">Khám gần nhất</p>
        <p class="text-base font-semibold text-on-surface">{{ summary?.last_exam_date ? formatDate(summary.last_exam_date) : '—' }}</p>
      </div>
    </div>

    <AppTabNav
      :tabs="mainTabs"
      :model-value="activeTab"
      @update:model-value="activeTab = $event as 'baseline' | 'visits'"
    />

    <section v-if="activeTab === 'baseline'" class="space-y-5">
      <div v-if="loadingSummary" class="space-y-3">
        <AppSkeleton v-for="i in 3" :key="i" class="h-24 rounded-2xl" />
      </div>

      <div v-else-if="baseline" class="grid gap-5 lg:grid-cols-[1fr_340px]">
        <div class="space-y-5">
          <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
            <div class="flex items-center justify-between gap-3 mb-4">
              <h2 class="text-base font-semibold text-on-surface">Bệnh nền & tình trạng cần lưu ý</h2>
              <AppButton size="sm" variant="ghost" @click="openBaselineEditor">Sửa</AppButton>
            </div>
            <div v-if="baseline.chronic_conditions.length" class="flex flex-wrap gap-2">
              <span
                v-for="condition in baseline.chronic_conditions"
                :key="condition"
                class="rounded-full bg-primary-fixed px-3 py-1.5 text-xs font-semibold text-primary"
              >
                {{ condition }}
              </span>
            </div>
            <div v-else class="text-sm text-outline">Chưa có bệnh nền được ghi nhận.</div>
          </div>

          <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
            <h2 class="text-base font-semibold text-on-surface mb-4">Dị ứng thuốc</h2>
            <div v-if="baseline.allergies.length" class="space-y-2">
              <div
                v-for="allergy in baseline.allergies"
                :key="`${allergy.drug}-${allergy.reaction}`"
                class="rounded-xl bg-error-container/60 px-4 py-3"
              >
                <p class="text-sm font-semibold text-on-surface">{{ allergy.drug }}</p>
                <p v-if="allergy.reaction" class="text-xs text-on-surface-variant mt-0.5">{{ allergy.reaction }}</p>
              </div>
            </div>
            <div v-else class="text-sm text-outline">Chưa ghi nhận dị ứng thuốc.</div>
          </div>

          <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
            <h2 class="text-base font-semibold text-on-surface mb-4">Thuốc đang dùng tự khai báo</h2>
            <div v-if="baseline.current_medications.length" class="space-y-2">
              <div
                v-for="medication in baseline.current_medications"
                :key="`${medication.name}-${medication.dosage}-${medication.frequency}`"
                class="rounded-xl bg-surface-container-low px-4 py-3"
              >
                <p class="text-sm font-semibold text-on-surface">{{ medication.name }}</p>
                <p class="text-xs text-on-surface-variant mt-0.5">
                  {{ [medication.dosage, medication.frequency].filter(Boolean).join(' · ') || 'Chưa có liều/tần suất' }}
                </p>
              </div>
            </div>
            <div v-else class="text-sm text-outline">Chưa có thuốc tự khai báo trong hồ sơ nền.</div>
            <button class="mt-4 text-sm font-semibold text-primary hover:underline" @click="router.push('/profile/prescriptions')">
              Quản lý đơn thuốc cá nhân
            </button>
          </div>
        </div>

        <aside class="space-y-5">
          <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
            <h2 class="text-base font-semibold text-on-surface mb-4">Chỉ số nền</h2>
            <div class="grid grid-cols-2 gap-3">
              <div class="rounded-xl bg-surface-container-low p-3">
                <p class="text-xs text-outline">Chiều cao</p>
                <p class="text-sm font-semibold text-on-surface">{{ baseline.height_cm ? `${baseline.height_cm} cm` : '—' }}</p>
              </div>
              <div class="rounded-xl bg-surface-container-low p-3">
                <p class="text-xs text-outline">Cân nặng</p>
                <p class="text-sm font-semibold text-on-surface">{{ baseline.weight_kg ? `${baseline.weight_kg} kg` : '—' }}</p>
              </div>
              <div class="rounded-xl bg-surface-container-low p-3">
                <p class="text-xs text-outline">Nhóm máu</p>
                <p class="text-sm font-semibold text-on-surface">{{ baseline.blood_type ?? '—' }}</p>
              </div>
              <div class="rounded-xl bg-surface-container-low p-3">
                <p class="text-xs text-outline">Thai kỳ</p>
                <p class="text-sm font-semibold text-on-surface">{{ baseline.is_pregnant ? 'Đang mang thai' : baseline.is_breastfeeding ? 'Cho con bú' : '—' }}</p>
              </div>
              <div class="rounded-xl bg-surface-container-low p-3">
                <p class="text-xs text-outline">Chức năng thận</p>
                <p class="text-sm font-semibold text-on-surface">{{ organLabels[baseline.kidney_function] }}</p>
              </div>
              <div class="rounded-xl bg-surface-container-low p-3">
                <p class="text-xs text-outline">Chức năng gan</p>
                <p class="text-sm font-semibold text-on-surface">{{ organLabels[baseline.liver_function] }}</p>
              </div>
            </div>
          </div>

          <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
            <h2 class="text-base font-semibold text-on-surface mb-4">Mục tiêu sức khỏe</h2>
            <div v-if="baseline.health_goals.length" class="flex flex-wrap gap-2">
              <span
                v-for="goal in baseline.health_goals"
                :key="goal"
                class="rounded-full bg-tertiary-fixed px-3 py-1.5 text-xs font-semibold text-tertiary"
              >
                {{ goal }}
              </span>
            </div>
            <p v-else class="text-sm text-outline">Chưa có mục tiêu sức khỏe.</p>
          </div>
        </aside>
      </div>

      <div v-else-if="!hasStaticData" class="bg-card rounded-2xl border border-outline-variant p-12 text-center shadow-sm">
        <p class="text-sm text-outline">Chưa có dữ liệu sức khỏe nền.</p>
        <button class="mt-2 text-sm text-primary hover:underline" @click="openBaselineEditor">Cập nhật ngay</button>
      </div>
    </section>

    <section v-else class="space-y-5">
      <div class="flex flex-wrap items-center gap-3">
        <div class="relative flex-1 min-w-48">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-outline pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="search"
            type="text"
            placeholder="Tìm kiếm lần khám..."
            class="w-full pl-9 pr-3 py-2 bg-card border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          />
        </div>
        <AppTabNav
          :tabs="visitTabs"
          :model-value="visitViewMode"
          @update:model-value="visitViewMode = $event as 'timeline' | 'table'"
        />
      </div>

      <div v-if="loadingVisits" class="space-y-4">
        <AppSkeleton v-for="i in 3" :key="i" class="h-28 rounded-2xl" />
      </div>

      <div v-else-if="!visitsData?.items.length" class="bg-card rounded-2xl border border-outline-variant p-12 text-center shadow-sm">
        <svg class="w-12 h-12 text-outline/40 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p class="text-sm text-outline">Chưa có lịch sử khám bệnh nào</p>
        <button class="mt-2 text-sm text-primary hover:underline" @click="showVisitModal = true; resetVisitForm()">Thêm lần khám đầu tiên</button>
      </div>

      <div v-else-if="visitViewMode === 'timeline'" class="relative">
        <div class="absolute left-5 top-0 bottom-0 w-0.5 bg-outline-variant/40" />
        <div class="space-y-6">
          <div v-for="(profile, idx) in visitsData.items" :key="profile.id" class="relative pl-14">
            <div :class="[
              'absolute left-3 top-5 w-5 h-5 rounded-full border-2 border-card flex items-center justify-center',
              idx === 0 ? 'bg-primary' : 'bg-surface-container-high',
            ]">
              <div :class="['w-2 h-2 rounded-full', idx === 0 ? 'bg-white' : 'bg-outline']" />
            </div>

            <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm hover:shadow-md transition-shadow">
              <div class="flex items-start justify-between gap-3 flex-wrap">
                <div>
                  <p class="text-xs text-outline mb-1">{{ formatDate(profile.exam_date) }}</p>
                  <h3 class="text-base font-semibold text-on-surface">{{ profile.diagnosis_name }}</h3>
                  <div class="flex flex-wrap gap-3 mt-2 text-xs text-on-surface-variant">
                    <span v-if="profile.facility">{{ profile.facility }}</span>
                    <span v-if="profile.doctor">{{ profile.doctor }}</span>
                  </div>
                  <p v-if="profile.conclusion" class="mt-2 text-sm text-on-surface-variant line-clamp-2">
                    {{ profile.conclusion }}
                  </p>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <button
                    @click="router.push(`/profile/health/${profile.id}`)"
                    class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
                  >
                    Xem chi tiết
                  </button>
                  <button
                    @click="deleteVisit(profile.id as string)"
                    :disabled="deleting && deletingId === profile.id"
                    class="px-3 py-1.5 text-xs font-medium text-error border border-error/30 rounded-lg hover:bg-error hover:text-white transition-colors disabled:opacity-50"
                  >
                    Xóa
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Chẩn đoán</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Ngày khám</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Cơ sở y tế</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Bác sĩ</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/50">
            <tr v-for="profile in visitsData.items" :key="profile.id" class="hover:bg-surface-container-low/50 transition-colors">
              <td class="px-5 py-4 text-sm font-medium text-on-surface">{{ profile.diagnosis_name }}</td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">{{ formatDate(profile.exam_date) }}</td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">{{ profile.facility ?? '—' }}</td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">{{ profile.doctor ?? '—' }}</td>
              <td class="px-5 py-4">
                <div class="flex items-center gap-2 justify-end">
                  <button
                    @click="router.push(`/profile/health/${profile.id}`)"
                    class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
                  >
                    Xem
                  </button>
                  <button
                    @click="deleteVisit(profile.id as string)"
                    :disabled="deleting && deletingId === profile.id"
                    class="px-3 py-1.5 text-xs font-medium text-error border border-error/30 rounded-lg hover:bg-error hover:text-white transition-colors disabled:opacity-50"
                  >
                    Xóa
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="visitsData?.meta" class="px-5 border-t border-outline-variant">
          <AppPagination :meta="visitsData.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
        </div>
      </div>
    </section>

    <AppModal :open="showBaselineModal" title="Cập nhật bệnh nền & dị ứng" size="lg" @close="showBaselineModal = false">
      <form @submit.prevent="submitBaselineForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="baselineForm.height_cm" type="number" label="Chiều cao (cm)" />
          <AppInput v-model="baselineForm.weight_kg" type="number" label="Cân nặng (kg)" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="baselineForm.blood_type" label="Nhóm máu" placeholder="VD: O+" />
          <div>
            <label class="text-sm font-medium text-on-surface block mb-1.5">Chức năng thận</label>
            <select v-model="baselineForm.kidney_function" class="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30">
              <option v-for="opt in organOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
        </div>
        <div>
          <label class="text-sm font-medium text-on-surface block mb-1.5">Chức năng gan</label>
          <select v-model="baselineForm.liver_function" class="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30">
            <option v-for="opt in organOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="flex items-center gap-3 rounded-xl border border-outline-variant px-4 py-3 text-sm text-on-surface">
            <input v-model="baselineForm.is_pregnant" type="checkbox" class="rounded border-outline-variant" />
            Đang mang thai
          </label>
          <label class="flex items-center gap-3 rounded-xl border border-outline-variant px-4 py-3 text-sm text-on-surface">
            <input v-model="baselineForm.is_breastfeeding" type="checkbox" class="rounded border-outline-variant" />
            Đang cho con bú
          </label>
        </div>
        <AppTextarea v-model="baselineForm.chronic_conditions_text" label="Bệnh nền" placeholder="Nhập cách nhau bằng dấu phẩy, ví dụ: Tăng huyết áp, Đái tháo đường type 2" :rows="2" />
        <AppTextarea v-model="baselineForm.allergies_text" label="Dị ứng thuốc" placeholder="Mỗi dòng một dị ứng, ví dụ: Penicillin - nổi mẩn" :rows="3" />
        <AppTextarea v-model="baselineForm.current_medications_text" label="Thuốc đang dùng tự khai báo" placeholder="Mỗi dòng: Tên thuốc | liều | tần suất" :rows="3" />
        <AppTextarea v-model="baselineForm.health_goals_text" label="Mục tiêu sức khỏe" placeholder="Nhập cách nhau bằng dấu phẩy" :rows="2" />
      </form>
      <template #footer>
        <AppButton variant="ghost" @click="showBaselineModal = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="updatingBaseline" @click="submitBaselineForm">Lưu hồ sơ</AppButton>
      </template>
    </AppModal>

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
