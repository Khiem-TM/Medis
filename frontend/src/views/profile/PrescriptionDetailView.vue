<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePrescriptionDetail, usePrescriptionInteractions } from '@/api/prescriptions.api'
import { formatDate } from '@/utils/format'
import { getSeverityClasses, getSeverityLabel } from '@/utils/severity'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)
const showInteractions = ref(false)

const { data: prescription, isLoading } = usePrescriptionDetail(id)
const { data: interactions, isLoading: loadingInteractions, refetch: fetchInteractions } = usePrescriptionInteractions(id)

function checkInteractions() {
  showInteractions.value = true
  fetchInteractions()
}

const interactionColumns = [
  { key: 'drug_1_name', label: 'Thuốc 1' },
  { key: 'drug_2_name', label: 'Thuốc 2' },
  { key: 'severity', label: 'Mức độ', align: 'center' as const },
  { key: 'description', label: 'Mô tả' },
]
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <div v-if="isLoading" class="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-4">
      <AppSkeleton class="h-7 w-48" />
      <AppSkeleton class="h-4 w-full" />
      <AppSkeleton class="h-4 w-3/4" />
    </div>

    <template v-else-if="prescription">
      <!-- Header -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <div class="flex items-start justify-between">
          <div>
            <h1 class="text-xl font-bold text-[#111827]">{{ prescription.name }}</h1>
            <p class="text-sm text-[#6B7280] mt-1">Tạo ngày {{ formatDate(prescription.created_at) }}</p>
            <p v-if="prescription.notes" class="text-sm text-[#374151] mt-2">{{ prescription.notes }}</p>
          </div>
          <div class="flex items-center gap-2">
            <AppBadge :variant="prescription.status === 'active' ? 'success' : 'default'">
              {{ prescription.status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}
            </AppBadge>
            <AppButton variant="outline" size="sm" @click="checkInteractions">Kiểm tra tương tác</AppButton>
          </div>
        </div>
      </div>

      <!-- Drug items -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <h2 class="text-base font-semibold text-[#111827] mb-4">Danh sách thuốc ({{ prescription.items.length }})</h2>
        <div class="space-y-3">
          <div
            v-for="(item, i) in prescription.items"
            :key="item.id"
            class="flex items-start gap-4 p-4 bg-[#F9FAFB] rounded-xl"
          >
            <div class="w-8 h-8 bg-[#D1FAE5] rounded-full flex items-center justify-center text-sm font-semibold text-[#065F46] flex-shrink-0">
              {{ i + 1 }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-[#111827]">{{ item.drug_name }}</p>
              <div class="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-sm text-[#6B7280]">
                <span>Liều: <span class="text-[#374151]">{{ item.dosage }}</span></span>
                <span v-if="item.frequency">Tần suất: <span class="text-[#374151]">{{ item.frequency }}</span></span>
                <span v-if="item.duration">Thời gian: <span class="text-[#374151]">{{ item.duration }}</span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Interaction results -->
      <div v-if="showInteractions" class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <h2 class="text-base font-semibold text-[#111827] mb-4">Kết quả kiểm tra tương tác</h2>

        <div v-if="loadingInteractions" class="space-y-2">
          <AppSkeleton class="h-12 w-full" v-for="i in 3" :key="i" />
        </div>

        <template v-else-if="interactions">
          <!-- Summary -->
          <div class="flex items-center gap-4 p-4 rounded-xl mb-4"
            :class="interactions.has_interaction ? 'bg-red-50 border border-red-100' : 'bg-[#D1FAE5] border border-[#6EE7B7]'"
          >
            <div class="text-2xl font-bold" :class="interactions.has_interaction ? 'text-red-600' : 'text-[#059669]'">
              {{ interactions.interaction_count }}
            </div>
            <div>
              <p class="font-medium" :class="interactions.has_interaction ? 'text-red-700' : 'text-[#065F46]'">
                {{ interactions.has_interaction ? 'Phát hiện tương tác thuốc' : 'Không có tương tác đáng lo ngại' }}
              </p>
              <p class="text-sm" :class="interactions.has_interaction ? 'text-red-600' : 'text-[#059669]'">
                {{ interactions.total_pairs }} cặp được kiểm tra
              </p>
            </div>
          </div>

          <!-- Interaction pairs with issues -->
          <div v-if="interactions.has_interaction" class="space-y-3">
            <div
              v-for="pair in interactions.pairs.filter((p) => p.has_interaction)"
              :key="`${pair.drug_1_id}-${pair.drug_2_id}`"
              class="border border-[#E5E7EB] rounded-xl p-4"
            >
              <div class="flex items-center justify-between mb-2">
                <p class="font-medium text-[#111827]">{{ pair.drug_1_name }} ↔ {{ pair.drug_2_name }}</p>
                <span v-if="pair.interaction" :class="['text-xs font-medium px-2 py-0.5 rounded-full', getSeverityClasses(pair.interaction.severity)]">
                  {{ getSeverityLabel(pair.interaction.severity) }}
                </span>
              </div>
              <p v-if="pair.interaction?.description" class="text-sm text-[#374151]">{{ pair.interaction.description }}</p>
              <p v-if="pair.interaction?.recommendation" class="text-sm text-[#10B981] mt-1">💡 {{ pair.interaction.recommendation }}</p>
            </div>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>
