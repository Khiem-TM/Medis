<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDrugSearch } from '@/api/drugs.api'
import { usePagination } from '@/composables/usePagination'
import { useDebounce } from '@/composables/useDebounce'
import type { DrugSearchParams } from '@/types/drug.types'
import AppTable from '@/components/ui/AppTable.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'

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

const columns = [
  { key: 'name', label: 'Tên thuốc' },
  { key: 'atc_code', label: 'Mã ATC' },
  { key: 'dosage_form', label: 'Dạng bào chế' },
  { key: 'classification', label: 'Phân loại' },
]

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
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold text-[#111827]">Tra cứu thuốc</h1>
      <p class="text-sm text-[#6B7280] mt-1">Tìm kiếm thông tin thuốc, sản phẩm thương mại và cảnh báo an toàn</p>
    </div>

    <!-- Search bar -->
    <div class="flex items-center gap-3 bg-white p-3 rounded-xl border border-[#E5E7EB]">
      <div class="flex-1 relative">
        <AppInput v-model="searchInput" placeholder="Nhập tên thuốc, mã ATC..." class="w-full">
          <template #prefix>
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </template>
        </AppInput>
      </div>
      <AppSelect v-model="dosageForm" :options="dosageOptions" class="w-48" placeholder="Dạng bào chế" />
    </div>

    <!-- Results -->
    <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
      <div class="px-4 py-3 border-b border-[#E5E7EB] flex items-center justify-between">
        <p class="text-sm text-[#6B7280]">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} kết quả</template>
          <template v-else>Đang tìm kiếm...</template>
        </p>
      </div>

      <AppTable
        :columns="columns"
        :data="(data?.items ?? []) as any[]"
        :loading="isLoading"
        empty-message="Không tìm thấy thuốc phù hợp"
        class="cursor-pointer"
      >
        <template #name="{ row }">
          <button class="text-left hover:text-[#10B981] font-medium transition-colors" @click="router.push(`/drugs/${row.id}`)">
            {{ row.name }}
          </button>
        </template>
        <template #atc_code="{ row }">
          <span class="font-mono text-xs">{{ row.atc_code ?? '—' }}</span>
        </template>
        <template #dosage_form="{ row }">{{ row.dosage_form ?? '—' }}</template>
        <template #classification="{ row }">{{ row.classification ?? '—' }}</template>
      </AppTable>

      <div v-if="data?.meta" class="px-4 border-t border-[#E5E7EB]">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>
  </div>
</template>
