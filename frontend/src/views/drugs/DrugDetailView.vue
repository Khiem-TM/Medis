<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDrugDetail, useDrugInteractions } from '@/api/drugs.api'
import { getSeverityClasses, getSeverityLabel } from '@/utils/severity'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppTable from '@/components/ui/AppTable.vue'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)

const { data: drug, isLoading, error } = useDrugDetail(id)
const { data: interactions } = useDrugInteractions(id)

const interactionColumns = [
  { key: 'drug_name', label: 'Thuốc tương tác' },
  { key: 'severity', label: 'Mức độ', align: 'center' as const },
  { key: 'interaction_type', label: 'Loại' },
  { key: 'description', label: 'Mô tả' },
]
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-4">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-4">
      <AppSkeleton class="h-8 w-64" />
      <AppSkeleton class="h-4 w-32" />
      <AppSkeleton :lines="4" />
    </div>

    <AppAlert v-else-if="error" type="error">Không tìm thấy thuốc</AppAlert>

    <template v-else-if="drug">
      <!-- Drug header -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <div class="flex items-start justify-between">
          <div>
            <h1 class="text-2xl font-bold text-[#111827]">{{ drug.name }}</h1>
            <div class="flex items-center gap-2 mt-2">
              <span v-if="drug.atc_code" class="text-xs font-mono bg-[#F3F4F6] text-[#374151] px-2 py-1 rounded">{{ drug.atc_code }}</span>
              <AppBadge v-if="drug.dosage_form">{{ drug.dosage_form }}</AppBadge>
              <AppBadge v-if="drug.classification" variant="info">{{ drug.classification }}</AppBadge>
            </div>
          </div>
          <AppButton variant="outline" size="sm" @click="router.push({ path: '/interactions', query: { drug: drug.id } })">
            Thêm vào kiểm tra tương tác
          </AppButton>
        </div>
        <p v-if="drug.description" class="text-sm text-[#374151] mt-4 leading-relaxed">{{ drug.description }}</p>
      </div>

      <!-- Warnings -->
      <div v-if="drug.warnings.length > 0" class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <h2 class="text-base font-semibold text-[#111827] mb-3">⚠️ Cảnh báo an toàn</h2>
        <div class="space-y-2">
          <div v-for="w in drug.warnings" :key="w.id" class="flex gap-2 p-3 bg-yellow-50 border border-yellow-100 rounded-lg">
            <span class="text-yellow-500 flex-shrink-0">•</span>
            <p class="text-sm text-yellow-800">{{ w.warning_text }}</p>
          </div>
        </div>
      </div>

      <!-- Products -->
      <div v-if="drug.products.length > 0" class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <h2 class="text-base font-semibold text-[#111827] mb-4">Sản phẩm thương mại ({{ drug.products.length }})</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-[#E5E7EB] text-[#6B7280]">
                <th class="text-left py-2 pr-4 font-medium">Tên thương mại</th>
                <th class="text-left py-2 pr-4 font-medium">Đường dùng</th>
                <th class="text-left py-2 pr-4 font-medium">Liều</th>
                <th class="text-left py-2 pr-4 font-medium">Dạng bào chế</th>
                <th class="text-left py-2 font-medium">Xuất xứ</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#F3F4F6]">
              <tr v-for="p in drug.products" :key="p.id" class="hover:bg-[#F9FAFB]">
                <td class="py-2 pr-4 font-medium text-[#111827]">{{ p.trade_name }}</td>
                <td class="py-2 pr-4 text-[#374151]">{{ p.route ?? '—' }}</td>
                <td class="py-2 pr-4 text-[#374151]">{{ p.dosage ?? '—' }}</td>
                <td class="py-2 pr-4 text-[#374151]">{{ p.formulation ?? '—' }}</td>
                <td class="py-2 text-[#374151]">{{ p.origin ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Interactions -->
      <div v-if="interactions && interactions.items.length > 0" class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <h2 class="text-base font-semibold text-[#111827] mb-4">Tương tác thuốc đã biết</h2>
        <div class="space-y-3">
          <div
            v-for="inter in interactions.items"
            :key="inter.id"
            class="border border-[#E5E7EB] rounded-xl p-4"
          >
            <div class="flex items-center justify-between mb-1">
              <p class="font-medium text-[#111827] text-sm">{{ inter.drug_id_1 === id ? inter.drug_id_2 : inter.drug_id_1 }}</p>
              <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', getSeverityClasses(inter.severity)]">
                {{ getSeverityLabel(inter.severity) }}
              </span>
            </div>
            <p v-if="inter.description" class="text-xs text-[#374151]">{{ inter.description }}</p>
            <p v-if="inter.recommendation" class="text-xs text-[#10B981] mt-1">💡 {{ inter.recommendation }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
