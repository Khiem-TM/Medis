<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounce } from '@/composables/useDebounce'
import { marketDrugsApi } from '@/api/market-drugs.api'
import type { MarketDrugProduct } from '@/types/market-drug.types'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [value: boolean] }>()

const router = useRouter()
const searchInput = ref<HTMLInputElement | null>(null)
const query = ref('')
const debounced = useDebounce(query, 300)
const results = ref<MarketDrugProduct[]>([])
const loading = ref(false)

function close() {
  emit('update:open', false)
  query.value = ''
  results.value = []
}

function handleKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.open) close()
}

onMounted(() => document.addEventListener('keydown', handleKey))
onUnmounted(() => document.removeEventListener('keydown', handleKey))

watch(
  () => props.open,
  async (val) => {
    if (val) {
      await nextTick()
      searchInput.value?.focus()
    } else {
      query.value = ''
      results.value = []
    }
  },
)

watch(debounced, async (q) => {
  if (!q || q.length < 1) {
    results.value = []
    return
  }
  loading.value = true
  try {
    const data = await marketDrugsApi.search({ search: q, size: 12 })
    results.value = data.items
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
})

function goToProduct(product: MarketDrugProduct) {
  router.push(`/market-drugs/${product.id}`)
  close()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-search">
      <div v-if="open" class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] px-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="close" />

        <!-- Dialog -->
        <div
          class="relative w-full max-w-xl bg-white rounded-2xl shadow-2xl overflow-hidden"
          style="border: 1px solid rgba(12,29,66,0.08);"
        >
          <!-- Search input -->
          <div class="flex items-center gap-3 px-4 py-3" style="border-bottom: 1px solid rgba(12,29,66,0.08);">
            <svg class="w-5 h-5 flex-shrink-0" style="color: #8A95AC;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref="searchInput"
              v-model="query"
              class="flex-1 bg-transparent outline-none text-sm"
              style="color: #0C1D42;"
              placeholder="Tìm thuốc theo tên thương mại, hoạt chất, số đăng ký..."
            />
            <div v-if="loading" class="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin" style="border-color: #1D4FD8; border-top-color: transparent;" />
            <kbd class="text-xs px-1.5 py-0.5 rounded font-mono flex-shrink-0" style="background: rgba(12,29,66,0.07); color: #8A95AC;">Esc</kbd>
          </div>

          <!-- Results -->
          <div class="max-h-[60vh] overflow-y-auto">
            <!-- Items -->
            <template v-if="results.length > 0">
              <p class="px-4 pt-3 pb-1 text-xs font-semibold uppercase tracking-wide" style="color: #8A95AC;">Thuốc thị trường</p>
              <button
                v-for="product in results"
                :key="product.id"
                type="button"
                class="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-[#F3F5F7]"
                @click="goToProduct(product)"
              >
                <!-- Image -->
                <div class="w-10 h-10 rounded-lg flex-shrink-0 overflow-hidden border" style="border-color: rgba(12,29,66,0.08); background: #F8FAFB;">
                  <img
                    v-if="product.image_url"
                    :src="product.image_url"
                    :alt="product.product_name"
                    class="w-full h-full object-contain p-1"
                  />
                  <svg v-else class="w-full h-full p-2" style="color: #B5BCCB;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
                  </svg>
                </div>

                <!-- Info -->
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-medium truncate" style="color: #0C1D42;">{{ product.product_name }}</p>
                  <p class="text-xs truncate mt-0.5" style="color: #8A95AC;">
                    {{ [product.dosage_form, product.packaging].filter(Boolean).join(' · ') }}
                  </p>
                </div>

                <!-- Registration badge + status -->
                <div class="flex flex-col items-end gap-1 flex-shrink-0">
                  <span class="text-xs px-1.5 py-0.5 rounded font-mono" style="background: #EFF6FF; color: #1D4FD8;">
                    {{ product.registration_number }}
                  </span>
                  <span v-if="product.is_expired" class="text-xs" style="color: #EF4444;">Hết hạn</span>
                </div>
              </button>
            </template>

            <!-- Empty state (after typing) -->
            <div v-else-if="debounced.length > 0 && !loading" class="py-12 text-center">
              <svg class="w-10 h-10 mx-auto mb-3" style="color: #B5BCCB;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <p class="text-sm" style="color: #8A95AC;">Không tìm thấy thuốc nào cho "<strong>{{ debounced }}</strong>"</p>
            </div>

            <!-- Idle state -->
            <div v-else-if="!debounced" class="py-10 text-center">
              <p class="text-sm" style="color: #B5BCCB;">Nhập tên thuốc để tra cứu...</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-search-enter-active,
.modal-search-leave-active {
  transition: all 0.15s ease;
}
.modal-search-enter-from,
.modal-search-leave-to {
  opacity: 0;
}
.modal-search-enter-from .relative,
.modal-search-leave-to .relative {
  transform: translateY(-8px) scale(0.98);
}
</style>
