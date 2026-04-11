import { ref, computed } from 'vue'
import type { PaginationMeta } from '@/types/api.types'

export function usePagination(initialSize = 10) {
  const page = ref(1)
  const size = ref(initialSize)

  function setPage(p: number) {
    page.value = p
  }

  function setSize(s: number) {
    size.value = s
    page.value = 1
  }

  function reset() {
    page.value = 1
  }

  const params = computed(() => ({ page: page.value, size: size.value }))

  return { page, size, params, setPage, setSize, reset }
}
