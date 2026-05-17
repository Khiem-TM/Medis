import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

export const useUiStore = defineStore('ui', () => {
  const sidebarOpen = ref(true)
  const mobileSidebarOpen = ref(false)
  const notificationDropdownOpen = ref(false)
  const commandPaletteOpen = ref(false)
  const isOffline = ref(!navigator.onLine)
  const toasts = ref<Toast[]>([])
  const theme = ref<'light' | 'dark'>((localStorage.getItem('theme') as 'light' | 'dark') || 'light')

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
    updateTheme()
  }

  function updateTheme() {
    if (theme.value === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function setMobileSidebar(open: boolean) {
    mobileSidebarOpen.value = open
  }

  function toggleMobileSidebar() {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
  }

  function setNotificationDropdown(open: boolean) {
    notificationDropdownOpen.value = open
  }

  function setCommandPalette(open: boolean) {
    commandPaletteOpen.value = open
  }

  function setOffline(value: boolean) {
    isOffline.value = value
  }

  function addToast(toast: Omit<Toast, 'id'>): string {
    const id = Math.random().toString(36).slice(2)
    const duration = toast.duration ?? 4000
    toasts.value.push({ ...toast, id, duration })

    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
    return id
  }

  function removeToast(id: string) {
    const idx = toasts.value.findIndex((t) => t.id === id)
    if (idx !== -1) toasts.value.splice(idx, 1)
  }

  function success(message: string) {
    return addToast({ type: 'success', message })
  }

  function error(message: string) {
    return addToast({ type: 'error', message, duration: 6000 })
  }

  function warning(message: string) {
    return addToast({ type: 'warning', message })
  }

  function info(message: string) {
    return addToast({ type: 'info', message })
  }

  return {
    sidebarOpen,
    mobileSidebarOpen,
    notificationDropdownOpen,
    commandPaletteOpen,
    isOffline,
    toasts,
    theme,
    toggleTheme,
    updateTheme,
    toggleSidebar,
    setMobileSidebar,
    toggleMobileSidebar,
    setNotificationDropdown,
    setCommandPalette,
    setOffline,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
  }
})
