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
  <div class="max-w-2xl mx-auto space-y-4">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <div v-if="isLoading" class="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-3">
      <AppSkeleton class="h-7 w-64" />
      <AppSkeleton class="h-4 w-full" />
      <AppSkeleton class="h-4 w-3/4" />
    </div>

    <div v-else-if="profile" class="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-5">
      <h1 class="text-xl font-bold text-[#111827]">{{ profile.diagnosis_name }}</h1>

      <div class="grid grid-cols-2 gap-4 text-sm">
        <div><span class="text-[#6B7280]">Ngày khám:</span> <span class="font-medium">{{ formatDate(profile.exam_date) }}</span></div>
        <div><span class="text-[#6B7280]">Cơ sở y tế:</span> <span class="font-medium">{{ profile.facility ?? '—' }}</span></div>
        <div><span class="text-[#6B7280]">Bác sĩ:</span> <span class="font-medium">{{ profile.doctor ?? '—' }}</span></div>
        <div><span class="text-[#6B7280]">Ngày tạo:</span> <span class="font-medium">{{ formatDateTime(profile.created_at) }}</span></div>
      </div>

      <div v-if="profile.symptoms" class="border-t border-[#E5E7EB] pt-4">
        <h3 class="text-sm font-medium text-[#6B7280] mb-1">Triệu chứng</h3>
        <p class="text-sm text-[#374151] whitespace-pre-wrap">{{ profile.symptoms }}</p>
      </div>

      <div v-if="profile.conclusion" class="border-t border-[#E5E7EB] pt-4">
        <h3 class="text-sm font-medium text-[#6B7280] mb-1">Kết luận</h3>
        <p class="text-sm text-[#374151] whitespace-pre-wrap">{{ profile.conclusion }}</p>
      </div>

      <div v-if="profile.notes" class="border-t border-[#E5E7EB] pt-4">
        <h3 class="text-sm font-medium text-[#6B7280] mb-1">Ghi chú</h3>
        <p class="text-sm text-[#374151] whitespace-pre-wrap">{{ profile.notes }}</p>
      </div>
    </div>
  </div>
</template>
