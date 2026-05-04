<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePrescriptionDetail, usePrescriptionInteractions } from '@/api/prescriptions.api'
import { formatDate } from '@/utils/format'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
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

function getSeverityClasses(severity: string) {
  switch (severity) {
    case 'major':    return 'bg-error-container text-error'
    case 'moderate': return 'bg-yellow-100 text-yellow-700'
    case 'minor':    return 'bg-tertiary-fixed text-tertiary'
    default:         return 'bg-surface-container text-outline'
  }
}

function getSeverityLabel(severity: string) {
  switch (severity) {
    case 'major':    return 'Nặng'
    case 'moderate': return 'Trung bình'
    case 'minor':    return 'Nhẹ'
    default:         return severity
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-5">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <div v-if="isLoading" class="bg-card rounded-2xl border border-outline-variant p-6 space-y-4 shadow-sm">
      <AppSkeleton class="h-7 w-48" />
      <AppSkeleton class="h-4 w-full" />
      <AppSkeleton class="h-4 w-3/4" />
    </div>

    <template v-else-if="prescription">
      <!-- Header -->
      <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <div class="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 class="text-xl font-bold text-on-surface">{{ prescription.name }}</h1>
            <p class="text-sm text-outline mt-0.5">Tạo ngày {{ formatDate(prescription.created_at) }}</p>
            <p v-if="prescription.notes" class="text-sm text-on-surface-variant mt-2">{{ prescription.notes }}</p>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <span :class="[
              'px-2.5 py-0.5 rounded-full text-xs font-bold',
              prescription.status === 'active' ? 'bg-tertiary-fixed text-tertiary' : 'bg-surface-container text-outline',
            ]">
              {{ prescription.status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}
            </span>
            <button
              @click="checkInteractions"
              class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
            >
              Kiểm tra tương tác
            </button>
          </div>
        </div>
      </div>

      <!-- Drug items -->
      <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h2 class="text-base font-semibold text-on-surface mb-4">Danh sách thuốc ({{ prescription.items.length }})</h2>
        <div class="space-y-3">
          <div
            v-for="(item, i) in prescription.items"
            :key="item.id"
            class="flex items-start gap-4 p-4 bg-surface-container-low rounded-xl"
          >
            <div class="w-8 h-8 bg-primary-fixed rounded-xl flex items-center justify-center text-sm font-bold text-primary flex-shrink-0">
              {{ i + 1 }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-semibold text-on-surface">{{ item.drug_name }}</p>
              <div class="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-sm text-outline">
                <span>Liều: <span class="text-on-surface-variant font-medium">{{ item.dosage }}</span></span>
                <span v-if="item.frequency">Tần suất: <span class="text-on-surface-variant font-medium">{{ item.frequency }}</span></span>
                <span v-if="item.duration">Thời gian: <span class="text-on-surface-variant font-medium">{{ item.duration }}</span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Interaction results -->
      <div v-if="showInteractions" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h2 class="text-base font-semibold text-on-surface mb-4">Kết quả kiểm tra tương tác</h2>

        <div v-if="loadingInteractions" class="space-y-2">
          <AppSkeleton class="h-12 w-full" v-for="i in 3" :key="i" />
        </div>

        <template v-else-if="interactions">
          <!-- Summary -->
          <div :class="[
            'flex items-center gap-4 p-4 rounded-xl mb-4 border',
            interactions.has_interaction
              ? 'bg-error-container/30 border-error/20'
              : 'bg-tertiary-fixed/40 border-tertiary/20',
          ]">
            <div :class="['text-2xl font-bold', interactions.has_interaction ? 'text-error' : 'text-tertiary']">
              {{ interactions.interaction_count }}
            </div>
            <div>
              <p :class="['font-semibold text-sm', interactions.has_interaction ? 'text-error' : 'text-tertiary']">
                {{ interactions.has_interaction ? 'Phát hiện tương tác thuốc' : 'Không có tương tác đáng lo ngại' }}
              </p>
              <p class="text-xs text-outline">{{ interactions.total_pairs }} cặp được kiểm tra</p>
            </div>
          </div>

          <!-- Interaction pairs with issues -->
          <div v-if="interactions.has_interaction" class="space-y-3">
            <div
              v-for="pair in interactions.pairs.filter((p) => p.has_interaction)"
              :key="`${pair.drug_1_id}-${pair.drug_2_id}`"
              :class="[
                'border-l-4 rounded-xl p-4 bg-surface-container-low',
                pair.interaction?.severity === 'major' ? 'border-error' : pair.interaction?.severity === 'moderate' ? 'border-yellow-400' : 'border-tertiary',
              ]"
            >
              <div class="flex items-center justify-between mb-2 flex-wrap gap-2">
                <p class="font-semibold text-on-surface text-sm">{{ pair.drug_1_name }} ↔ {{ pair.drug_2_name }}</p>
                <span v-if="pair.interaction" :class="['text-xs font-bold px-2.5 py-0.5 rounded-full', getSeverityClasses(pair.interaction.severity)]">
                  {{ getSeverityLabel(pair.interaction.severity) }}
                </span>
              </div>
              <p v-if="pair.interaction?.description" class="text-sm text-on-surface-variant">{{ pair.interaction.description }}</p>
              <p v-if="pair.interaction?.recommendation" class="text-sm text-tertiary font-medium mt-1">💡 {{ pair.interaction.recommendation }}</p>
            </div>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>
