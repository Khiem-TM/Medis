import { ref } from 'vue'

export function useConfirm() {
  const open = ref(false)
  const loading = ref(false)
  let _resolve: ((val: boolean) => void) | null = null

  function confirm(): Promise<boolean> {
    open.value = true
    return new Promise((resolve) => {
      _resolve = resolve
    })
  }

  function onConfirm() {
    _resolve?.(true)
    open.value = false
  }

  function onCancel() {
    _resolve?.(false)
    open.value = false
  }

  return { open, loading, confirm, onConfirm, onCancel }
}
