<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHealthProfileDetail } from '@/api/health-profiles.api'
import { formatDate, formatDateTime } from '@/utils/format'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)
const { data: profile, isLoading } = useHealthProfileDetail(id)
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-5">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <div v-if="isLoading" class="bg-card rounded-2xl border border-outline-variant p-6 space-y-3 shadow-sm">
      <AppSkeleton class="h-7 w-64" />
      <AppSkeleton class="h-4 w-full" />
      <AppSkeleton class="h-4 w-3/4" />
    </div>

    <div v-else-if="profile" class="space-y-5">
      <!-- Header card -->
      <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 rounded-xl bg-error-container flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-bold text-on-surface">{{ profile.diagnosis_name }}</h1>
            <p class="text-sm text-outline mt-0.5">Hồ sơ khám bệnh</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mt-5">
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Ngày khám</p>
            <p class="text-sm font-medium text-on-surface">{{ formatDate(profile.exam_date) }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Cơ sở y tế</p>
            <p class="text-sm font-medium text-on-surface">{{ profile.facility ?? '—' }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Bác sĩ</p>
            <p class="text-sm font-medium text-on-surface">{{ profile.doctor ?? '—' }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Ngày tạo</p>
            <p class="text-sm font-medium text-on-surface">{{ formatDateTime(profile.created_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Symptoms -->
      <div v-if="profile.symptoms" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h3 class="text-sm font-semibold text-outline uppercase tracking-wider mb-3">Triệu chứng</h3>
        <p class="text-sm text-on-surface whitespace-pre-wrap leading-relaxed">{{ profile.symptoms }}</p>
      </div>

      <!-- Conclusion -->
      <div v-if="profile.conclusion" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h3 class="text-sm font-semibold text-outline uppercase tracking-wider mb-3">Kết luận</h3>
        <p class="text-sm text-on-surface whitespace-pre-wrap leading-relaxed">{{ profile.conclusion }}</p>
      </div>

      <!-- Notes -->
      <div v-if="profile.notes" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h3 class="text-sm font-semibold text-outline uppercase tracking-wider mb-3">Ghi chú</h3>
        <p class="text-sm text-on-surface whitespace-pre-wrap leading-relaxed">{{ profile.notes }}</p>
      </div>
    </div>
  </div>
</template>
