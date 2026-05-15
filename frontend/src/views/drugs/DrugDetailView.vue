<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDrugDetail, useDrugInteractions } from '@/api/drugs.api'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)

const { data: drug, isLoading, error } = useDrugDetail(id)
const { data: interactions } = useDrugInteractions(id)
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-5">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="bg-card rounded-2xl border border-outline-variant p-6 space-y-4">
      <AppSkeleton class="h-8 w-64" />
      <AppSkeleton class="h-4 w-32" />
      <AppSkeleton :lines="4" />
    </div>

    <AppAlert v-else-if="error" type="error">Không tìm thấy thuốc</AppAlert>

    <template v-else-if="drug">
      <!-- Drug header -->
      <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <div class="flex items-start justify-between flex-wrap gap-3">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <div class="w-10 h-10 rounded-xl bg-primary-fixed flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
                </svg>
              </div>
              <h1 class="text-2xl font-bold text-on-surface">{{ drug.generic_name }}</h1>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <code v-for="atc in drug.atc_codes" :key="atc" class="text-xs bg-surface-container px-2.5 py-1 rounded-lg font-mono text-on-surface-variant">{{ atc }}</code>
              <span v-for="form in drug.dosage_forms" :key="form" class="text-xs bg-primary-fixed text-primary px-2.5 py-0.5 rounded-full font-medium">{{ form }}</span>
              <span v-for="category in drug.categories" :key="category" class="text-xs bg-secondary-container text-secondary px-2.5 py-0.5 rounded-full font-medium">{{ category }}</span>
            </div>
          </div>
          <AppButton variant="outline" size="sm" @click="router.push({ path: '/interactions', query: { drug: drug.id } })">
            Thêm vào kiểm tra tương tác
          </AppButton>
        </div>
        <p v-if="drug.description" class="text-sm text-on-surface-variant mt-4 leading-relaxed">{{ drug.description }}</p>
      </div>

      <!-- Warnings -->
      <div v-if="drug.warnings.length > 0" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h2 class="text-base font-semibold text-on-surface mb-3 flex items-center gap-2">
          <span class="w-5 h-5 bg-yellow-100 text-yellow-600 rounded flex items-center justify-center text-xs">⚠️</span>
          Cảnh báo an toàn
        </h2>
        <div class="space-y-2">
          <div v-for="w in drug.warnings" :key="w.id" class="flex gap-2 p-3 bg-yellow-50 border border-yellow-100 rounded-xl">
            <span class="text-yellow-500 flex-shrink-0 mt-0.5">•</span>
            <p class="text-sm text-yellow-800">{{ w.warning_text }}</p>
          </div>
        </div>
      </div>

      <!-- Products -->
      <div v-if="drug.brand_names.length > 0" class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
        <div class="px-5 py-4 border-b border-outline-variant">
          <h2 class="text-base font-semibold text-on-surface">Sản phẩm thương mại ({{ drug.brand_names.length }})</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-low border-b border-outline-variant">
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Tên thương mại</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Đường dùng</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Hàm lượng</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Dạng bào chế</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Xuất xứ</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant/50">
              <tr v-for="p in drug.brand_names" :key="p.id" class="hover:bg-surface-container-low/50 transition-colors">
                <td class="px-5 py-3 font-medium text-on-surface">{{ p.name }}</td>
                <td class="px-5 py-3 text-on-surface-variant">{{ p.route ?? '—' }}</td>
                <td class="px-5 py-3 text-on-surface-variant">{{ p.strength ?? '—' }}</td>
                <td class="px-5 py-3 text-on-surface-variant">{{ p.dosage_form ?? '—' }}</td>
                <td class="px-5 py-3 text-on-surface-variant">{{ p.country ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Interactions -->
      <div v-if="interactions && interactions.items.length > 0" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h2 class="text-base font-semibold text-on-surface mb-4">Tương tác thuốc đã biết</h2>
        <div class="space-y-3">
          <div
            v-for="inter in interactions.items"
            :key="`${inter.drug_id}-${inter.interacts_with_id}`"
            class="border-l-4 border-error rounded-xl p-4 bg-surface-container-low"
          >
            <div class="flex items-center justify-between mb-1 flex-wrap gap-2">
              <p class="font-semibold text-on-surface text-sm">
                {{ inter.drug_id === id ? (inter.interacts_with_name || inter.interacts_with_id) : (inter.drug_name || inter.drug_id) }}
              </p>
              <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-surface-container text-outline">
                {{ inter.source ?? 'database' }}
              </span>
            </div>
            <p v-if="inter.interaction_label" class="text-xs text-on-surface-variant">{{ inter.interaction_label }}</p>
            <p v-if="inter.confidence_score != null" class="text-xs text-tertiary mt-1 font-medium">
              Độ tin cậy: {{ (inter.confidence_score * 100).toFixed(1) }}%
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
