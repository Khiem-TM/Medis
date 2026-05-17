<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, RouterView } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import OfflineBanner from '@/components/layout/OfflineBanner.vue'
import AppToastContainer from '@/components/ui/AppToastContainer.vue'
import { useAuthStore } from '@/stores/auth.store'
import { useNotificationStore } from '@/stores/notification.store'
import { useOnboardingStore } from '@/stores/onboarding.store'
import { useUiStore } from '@/stores/ui.store'

const route = useRoute()
const layout = computed(() => route.meta.layout ?? 'none')
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const onboardingStore = useOnboardingStore()
const uiStore = useUiStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)

function syncConnectivity() {
  uiStore.setOffline(!navigator.onLine)
}

watch(
  () => authStore.accessToken,
  (token) => {
    if (token) {
      notificationStore.connect(token)
    } else {
      notificationStore.disconnect()
      onboardingStore.clear()
    }
  },
  { immediate: true },
)

watch(
  () => route.fullPath,
  () => {
    uiStore.setMobileSidebar(false)
    uiStore.setNotificationDropdown(false)
  },
)

watch(isAuthenticated, (value) => {
  if (!value) {
    notificationStore.disconnect()
  }
})

onMounted(() => {
  syncConnectivity()
  uiStore.updateTheme()
  window.addEventListener('online', syncConnectivity)
  window.addEventListener('offline', syncConnectivity)
})

onUnmounted(() => {
  window.removeEventListener('online', syncConnectivity)
  window.removeEventListener('offline', syncConnectivity)
})
</script>

<template>
  <AppToastContainer />
  <OfflineBanner />

  <AppLayout v-if="layout === 'app'">
    <RouterView />
  </AppLayout>

  <AuthLayout v-else-if="layout === 'auth'">
    <RouterView />
  </AuthLayout>

  <RouterView v-else />
</template>
