import { useUiStore } from '@/stores/ui.store'

export function useToast() {
  const uiStore = useUiStore()
  return {
    success: uiStore.success.bind(uiStore),
    error: uiStore.error.bind(uiStore),
    warning: uiStore.warning.bind(uiStore),
    info: uiStore.info.bind(uiStore),
  }
}
