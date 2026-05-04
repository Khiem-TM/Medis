<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useDebounce } from '@/composables/useDebounce'
import { drugsApi } from '@/api/drugs.api'
import type { DrugListItem } from '@/types/drug.types'
import AppSpinner from '@/components/ui/AppSpinner.vue'

const props = defineProps<{
  modelValue: DrugListItem[]
  max?: number
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: DrugListItem[]]
}>()

const search = ref('')
const debouncedSearch = useDebounce(search, 300)
const results = ref<DrugListItem[]>([])
const loading = ref(false)
const open = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const MAX = computed(() => props.max ?? 20)
const isFull = computed(() => props.modelValue.length >= MAX.value)

watch(debouncedSearch, async (q) => {
  if (!q || q.length < 2) { results.value = []; open.value = false; return }
  loading.value = true
  try {
    const data = await drugsApi.search({ search: q, size: 10 })
    results.value = data.items.filter((d) => !props.modelValue.some((s) => s.id === d.id))
    open.value = results.value.length > 0
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
})

function select(drug: DrugListItem) {
  if (isFull.value || props.modelValue.some((d) => d.id === drug.id)) return
  emit('update:modelValue', [...props.modelValue, drug])
  search.value = ''
  results.value = []
  open.value = false
  inputRef.value?.focus()
}

function remove(id: string) {
  emit('update:modelValue', props.modelValue.filter((d) => d.id !== id))
}

function onBlur() {
  setTimeout(() => { open.value = false }, 150)
}
</script>

<template>
  <div class="space-y-2">
    <!-- Selected tags -->
    <div v-if="modelValue.length > 0" class="flex flex-wrap gap-2">
      <div
        v-for="drug in modelValue"
        :key="drug.id"
        class="flex items-center gap-1.5 px-3 py-1 bg-primary-fixed text-primary rounded-full text-sm font-medium"
      >
        <span>{{ drug.name }}</span>
        <button @click="remove(drug.id)" class="hover:text-error transition-colors">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Search input -->
    <div class="relative">
      <input
        ref="inputRef"
        v-model="search"
        :disabled="isFull"
        :placeholder="isFull ? `Đã đạt tối đa ${MAX} thuốc` : (placeholder ?? 'Tìm tên thuốc...')"
        class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2 pr-9 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        @focus="open = debouncedSearch.length >= 2 && results.length > 0"
        @blur="onBlur"
      />
      <div class="absolute inset-y-0 right-3 flex items-center">
        <AppSpinner v-if="loading" size="sm" class="text-primary" />
        <svg v-else class="w-4 h-4 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <!-- Dropdown -->
      <div v-if="open" class="absolute top-full left-0 right-0 mt-1 bg-card border border-outline-variant rounded-xl shadow-lg z-50 overflow-hidden max-h-60 overflow-y-auto">
        <button
          v-for="drug in results"
          :key="drug.id"
          @mousedown.prevent="select(drug)"
          class="w-full text-left px-4 py-2.5 hover:bg-surface-container-low transition-colors"
        >
          <p class="text-sm font-medium text-on-surface">{{ drug.name }}</p>
          <p class="text-xs text-outline">
            {{ [drug.atc_code, drug.dosage_form].filter(Boolean).join(' · ') || 'Không có thông tin thêm' }}
          </p>
        </button>
      </div>
    </div>

    <p class="text-xs text-outline">
      Đã chọn {{ modelValue.length }}/{{ MAX }} thuốc
      <span v-if="modelValue.length < 2" class="text-yellow-600"> (cần ít nhất 2 thuốc)</span>
    </p>
  </div>
</template>
