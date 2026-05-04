<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { useHealthProfiles, useCreateHealthProfileMutation, useDeleteHealthProfileMutation } from '@/api/health-profiles.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { healthProfileSchema } from '@/schemas/health-profile.schema'
import { formatDate } from '@/utils/format'
import type { HealthProfileSearchParams } from '@/types/health-profile.types'
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

const viewMode = ref<'timeline' | 'table'>('timeline')
const search = ref('')
const deletingId = ref<string | null>(null)

const queryParams = computed<HealthProfileSearchParams>(() => ({
  ...paginationParams.value,
  search: search.value || undefined,
}))

const { data, isLoading } = useHealthProfiles(queryParams)
const { mutate: createHealthProfile, isPending: creating } = useCreateHealthProfileMutation()
const { mutate: deleteHealthProfile, isPending: deleting } = useDeleteHealthProfileMutation()

const showModal = ref(false)
const formErrors = reactive<Record<string, string>>({})
const form = reactive({
  diagnosis_name: '',
  exam_date: '',
  facility: '',
  doctor: '',
  symptoms: '',
  conclusion: '',
  notes: '',
})

function resetForm() {
  Object.keys(form).forEach((k) => (form as Record<string, string>)[k] = '')
  Object.keys(formErrors).forEach((k) => delete formErrors[k])
}

function validateForm() {
  Object.keys(formErrors).forEach((k) => delete formErrors[k])
  try { healthProfileSchema.parse(form); return true }
  catch (e) {
    if (e instanceof z.ZodError) e.issues.forEach((err) => { if (err.path[0]) formErrors[err.path[0] as string] = err.message })
    return false
  }
}

function submitForm() {
  if (!validateForm()) return
  const payload = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ''))
  createHealthProfile(payload as any, {
    onSuccess: () => { toast.success('Tạo hồ sơ khám bệnh thành công'); showModal.value = false; resetForm() },
    onError: (e) => toast.error((e as { message?: string })?.message || 'Tạo hồ sơ thất bại'),
  })
}

async function deleteItem(id: string) {
  deletingId.value = id
  const confirmed = await confirm()
  if (!confirmed) { deletingId.value = null; return }
  deleteHealthProfile(id, {
    onSuccess: () => toast.success('Đã xóa hồ sơ'),
    onError: () => toast.error('Không thể xóa hồ sơ này'),
    onSettled: () => { deletingId.value = null },
  })
}

const viewTabs = [
  { key: 'timeline', label: 'Dòng thời gian' },
  { key: 'table', label: 'Bảng danh sách' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-on-surface">Hồ sơ khám bệnh</h1>
        <p class="text-sm text-outline mt-0.5">Lịch sử khám và chẩn đoán của bạn</p>
      </div>
      <AppButton variant="gradient" @click="showModal = true; resetForm()">
        <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Thêm hồ sơ
      </AppButton>
    </div>

    <!-- Controls bar -->
    <div class="flex flex-wrap items-center gap-3">
      <div class="relative flex-1 min-w-48">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-outline pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="search"
          type="text"
          placeholder="Tìm kiếm hồ sơ..."
          class="w-full pl-9 pr-3 py-2 bg-card border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
        />
      </div>
      <AppTabNav
        :tabs="viewTabs"
        :model-value="viewMode"
        @update:model-value="viewMode = $event as 'timeline' | 'table'"
      />
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="space-y-4">
      <AppSkeleton v-for="i in 3" :key="i" class="h-28 rounded-2xl" />
    </div>

    <!-- Empty state -->
    <div v-else-if="!data?.items.length" class="bg-card rounded-2xl border border-outline-variant p-12 text-center shadow-sm">
      <svg class="w-12 h-12 text-outline/40 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <p class="text-sm text-outline">Chưa có hồ sơ khám bệnh nào</p>
      <button class="mt-2 text-sm text-primary hover:underline" @click="showModal = true; resetForm()">Thêm hồ sơ đầu tiên</button>
    </div>

    <!-- Timeline view -->
    <div v-else-if="viewMode === 'timeline'" class="relative">
      <!-- Vertical line -->
      <div class="absolute left-5 top-0 bottom-0 w-0.5 bg-outline-variant/40" />

      <div class="space-y-6">
        <div
          v-for="(profile, idx) in data.items"
          :key="profile.id"
          class="relative pl-14"
        >
          <!-- Timeline dot -->
          <div :class="[
            'absolute left-3 top-5 w-5 h-5 rounded-full border-2 border-card flex items-center justify-center',
            idx === 0 ? 'bg-primary' : 'bg-surface-container-high',
          ]">
            <div :class="['w-2 h-2 rounded-full', idx === 0 ? 'bg-white' : 'bg-outline']" />
          </div>

          <!-- Card -->
          <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm hover:shadow-md transition-shadow">
            <div class="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <p class="text-xs text-outline mb-1">{{ formatDate((profile as any).exam_date) }}</p>
                <h3 class="text-base font-semibold text-on-surface">{{ (profile as any).diagnosis_name }}</h3>
                <div class="flex flex-wrap gap-3 mt-2 text-xs text-on-surface-variant">
                  <span v-if="(profile as any).facility" class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {{ (profile as any).facility }}
                  </span>
                  <span v-if="(profile as any).doctor" class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    {{ (profile as any).doctor }}
                  </span>
                </div>
                <p v-if="(profile as any).conclusion" class="mt-2 text-sm text-on-surface-variant line-clamp-2">
                  {{ (profile as any).conclusion }}
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
                  @click="deleteItem(profile.id as string)"
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

    <!-- Table view -->
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
          <tr
            v-for="profile in data.items"
            :key="profile.id"
            class="hover:bg-surface-container-low/50 transition-colors"
          >
            <td class="px-5 py-4 text-sm font-medium text-on-surface">{{ (profile as any).diagnosis_name }}</td>
            <td class="px-5 py-4 text-sm text-on-surface-variant">{{ formatDate((profile as any).exam_date) }}</td>
            <td class="px-5 py-4 text-sm text-on-surface-variant">{{ (profile as any).facility ?? '—' }}</td>
            <td class="px-5 py-4 text-sm text-on-surface-variant">{{ (profile as any).doctor ?? '—' }}</td>
            <td class="px-5 py-4">
              <div class="flex items-center gap-2 justify-end">
                <button
                  @click="router.push(`/profile/health/${profile.id}`)"
                  class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
                >
                  Xem
                </button>
                <button
                  @click="deleteItem(profile.id as string)"
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
      <div v-if="data?.meta" class="px-5 border-t border-outline-variant">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>

    <!-- Create modal -->
    <AppModal :open="showModal" title="Thêm hồ sơ khám bệnh" size="lg" @close="showModal = false">
      <form @submit.prevent="submitForm" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.diagnosis_name" label="Chẩn đoán" placeholder="VD: Viêm họng cấp" :error="formErrors.diagnosis_name" required />
          <AppInput v-model="form.exam_date" type="date" label="Ngày khám" :error="formErrors.exam_date" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="form.facility" label="Cơ sở y tế" placeholder="Bệnh viện..." />
          <AppInput v-model="form.doctor" label="Bác sĩ" placeholder="BS. Nguyễn..." />
        </div>
        <AppTextarea v-model="form.symptoms" label="Triệu chứng" placeholder="Mô tả triệu chứng..." :rows="2" />
        <AppTextarea v-model="form.conclusion" label="Kết luận" placeholder="Kết luận khám..." :rows="2" />
        <AppTextarea v-model="form.notes" label="Ghi chú" placeholder="Ghi chú thêm..." :rows="2" />
      </form>
      <template #footer>
        <AppButton variant="ghost" @click="showModal = false">Hủy</AppButton>
        <AppButton variant="gradient" :loading="creating" @click="submitForm">Lưu hồ sơ</AppButton>
      </template>
    </AppModal>

    <AppConfirmDialog :open="confirmOpen" title="Xóa hồ sơ" message="Bạn có chắc muốn xóa hồ sơ khám bệnh này?" danger :loading="deleting" @confirm="onConfirm" @cancel="onCancel" />
  </div>
</template>
