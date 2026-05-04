<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDrugSearch } from '@/api/drugs.api'
import { usePagination } from '@/composables/usePagination'
import { useDebounce } from '@/composables/useDebounce'
import type { DrugSearchParams } from '@/types/drug.types'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'

const router = useRouter()
const { page, size, params: paginationParams, setPage, setSize } = usePagination(20)
const searchInput = ref('')
const dosageForm = ref('')
const debouncedSearch = useDebounce(searchInput, 400)

const queryParams = computed<DrugSearchParams>(() => ({
  ...paginationParams.value,
  search: debouncedSearch.value || undefined,
  dosage_form: dosageForm.value || undefined,
}))

const { data, isLoading } = useDrugSearch(queryParams)

const dosageOptions = [
  { label: 'Tất cả dạng bào chế', value: '' },
  { label: 'Viên nén', value: 'Viên nén' },
  { label: 'Viên nang', value: 'Viên nang' },
  { label: 'Dung dịch', value: 'Dung dịch' },
  { label: 'Thuốc tiêm', value: 'Thuốc tiêm' },
  { label: 'Kem/Mỡ', value: 'Kem' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-on-surface">Tra cứu thuốc</h1>
      <p class="text-sm text-outline mt-0.5">Tìm kiếm thông tin thuốc, sản phẩm thương mại và cảnh báo an toàn</p>
    </div>

    <!-- Search bar -->
    <div class="bg-card rounded-2xl border border-outline-variant p-4 flex flex-col sm:flex-row gap-3 shadow-sm">
      <div class="relative flex-1">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-outline pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchInput"
          type="text"
          placeholder="Nhập tên thuốc, mã ATC..."
          class="w-full pl-10 pr-4 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
        />
      </div>
      <select
        v-model="dosageForm"
        class="px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
      >
        <option v-for="opt in dosageOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
    </div>

    <!-- Results table -->
    <div class="bg-card rounded-2xl border border-outline-variant overflow-hidden">
      <!-- Table header -->
      <div class="px-6 py-4 border-b border-outline-variant flex items-center justify-between bg-card">
        <div class="flex items-center gap-3">
          <h2 class="text-base font-semibold text-on-surface">Kết quả tìm kiếm</h2>
          <span v-if="!isLoading && data" class="px-2.5 py-0.5 bg-surface-container text-primary rounded-full text-xs font-bold">
            {{ data.meta.total.toLocaleString() }} thuốc
          </span>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="isLoading" class="p-6 space-y-3">
        <AppSkeleton v-for="i in 6" :key="i" class="h-14 rounded-xl" />
      </div>

      <!-- Empty state -->
      <div v-else-if="!data?.items.length" class="text-center py-16">
        <svg class="w-12 h-12 text-outline mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="text-sm font-medium text-on-surface">Không tìm thấy thuốc phù hợp</p>
        <p class="text-xs text-outline mt-1">Thử tìm kiếm với từ khóa khác</p>
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th class="px-6 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Tên thuốc</th>
              <th class="px-6 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Mã ATC</th>
              <th class="px-6 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Dạng bào chế</th>
              <th class="px-6 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Phân loại</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/50">
            <tr
              v-for="drug in data.items"
              :key="drug.id"
              class="hover:bg-surface-container-low transition-colors cursor-pointer group"
              @click="router.push(`/drugs/${drug.id}`)"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-primary-fixed flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                  </div>
                  <span class="text-sm font-semibold text-on-surface group-hover:text-primary transition-colors">{{ drug.name }}</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <code v-if="drug.atc_code" class="px-2 py-0.5 bg-surface-container text-primary rounded text-xs font-bold">{{ drug.atc_code }}</code>
                <span v-else class="text-outline text-xs">—</span>
              </td>
              <td class="px-6 py-4">
                <span v-if="drug.dosage_form" class="px-2 py-0.5 bg-secondary-container/40 text-secondary rounded-full text-xs font-medium">
                  {{ drug.dosage_form }}
                </span>
                <span v-else class="text-outline text-xs">—</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-on-surface-variant">{{ drug.classification ?? '—' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="data?.meta" class="px-6 border-t border-outline-variant">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>
  </div>
</template>
