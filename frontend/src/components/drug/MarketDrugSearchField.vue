<script setup lang="ts">
import { ref, watch } from 'vue'
import { useDebounce } from '@/composables/useDebounce'
import { marketDrugsApi } from '@/api/market-drugs.api'
import type { MarketDrugProduct } from '@/types/market-drug.types'
import AppSpinner from '@/components/ui/AppSpinner.vue'

const props = defineProps<{
  modelValue: MarketDrugProduct | null
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: MarketDrugProduct | null]
}>()

const search = ref(props.modelValue?.product_name ?? '')
const debounced = useDebounce(search, 300)
const results = ref<MarketDrugProduct[]>([])
const loading = ref(false)
const open = ref(false)

watch(() => props.modelValue, (value) => {
  if (value && value.product_name !== search.value) search.value = value.product_name
  if (!value && !open.value) search.value = ''
})

watch(debounced, async (q) => {
  if (!q || q.length < 2) {
    results.value = []
    open.value = false
    return
  }
  loading.value = true
  try {
    const data = await marketDrugsApi.search({ search: q, size: 8 })
    results.value = data.items
    open.value = results.value.length > 0
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
})

function selectProduct(product: MarketDrugProduct) {
  emit('update:modelValue', product)
  search.value = product.product_name
  open.value = false
  results.value = []
}

function clearProduct() {
  emit('update:modelValue', null)
  search.value = ''
  results.value = []
  open.value = false
}

function onBlur() {
  setTimeout(() => { open.value = false }, 150)
}
</script>

<template>
  <div class="space-y-2">
    <div v-if="modelValue" class="flex items-center gap-3 rounded-xl border border-outline-variant bg-surface px-3 py-2">
      <img
        v-if="modelValue.image_url"
        :src="modelValue.image_url"
        :alt="modelValue.product_name"
        class="w-14 h-14 rounded-lg object-cover border border-outline-variant bg-white"
      />
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold text-on-surface truncate">{{ modelValue.product_name }}</p>
        <p class="text-xs text-outline truncate">
          {{ [modelValue.registration_number, modelValue.dosage_form].filter(Boolean).join(' · ') }}
        </p>
        <p class="text-xs text-outline truncate">{{ modelValue.ingredient_summary.join(', ') }}</p>
      </div>
      <button type="button" class="text-sm text-primary hover:underline" @click="clearProduct">Đổi</button>
    </div>

    <div v-else class="relative">
      <input
        v-model="search"
        :placeholder="placeholder ?? 'Tìm thuốc theo tên thương mại / số đăng ký...'"
        class="w-full rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2 pr-9 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
        @focus="open = debounced.length >= 2 && results.length > 0"
        @blur="onBlur"
      />
      <div class="absolute inset-y-0 right-3 flex items-center">
        <AppSpinner v-if="loading" size="sm" class="text-primary" />
      </div>

      <div v-if="open" class="absolute top-full left-0 right-0 mt-1 bg-card border border-outline-variant rounded-xl shadow-lg z-50 overflow-hidden max-h-72 overflow-y-auto">
        <button
          v-for="product in results"
          :key="product.id"
          type="button"
          @mousedown.prevent="selectProduct(product)"
          class="w-full text-left px-4 py-3 hover:bg-surface-container-low transition-colors"
        >
          <div class="flex gap-3 items-start">
            <img
              v-if="product.image_url"
              :src="product.image_url"
              :alt="product.product_name"
              class="w-12 h-12 rounded-lg object-cover border border-outline-variant bg-white flex-shrink-0"
            />
            <div class="min-w-0">
              <p class="text-sm font-medium text-on-surface truncate">{{ product.product_name }}</p>
              <p class="text-xs text-outline truncate">
                {{ [product.registration_number, product.dosage_form].filter(Boolean).join(' · ') }}
              </p>
              <p class="text-xs text-outline truncate">{{ product.ingredient_summary.join(', ') }}</p>
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
