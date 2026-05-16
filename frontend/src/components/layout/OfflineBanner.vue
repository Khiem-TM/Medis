<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'

const uiStore = useUiStore()
</script>

<template>
  <Transition name="offline-banner">
    <div
      v-if="uiStore.isOffline"
      class="fixed inset-x-4 top-4 z-[70] rounded-2xl px-4 py-3 text-sm text-white glass-panel-strong"
      style="background: linear-gradient(135deg, rgba(186, 26, 26, 0.92), rgba(138, 48, 176, 0.9));"
    >
      <div class="flex items-center gap-3">
        <svg class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.111 16.404a5.5 5.5 0 017.778 0M4.929 13.222a10 10 0 0114.142 0M1.757 10.05a14.5 14.5 0 0120.486 0M12 20h.01" />
        </svg>
        <div>
          <p class="font-semibold">Không có kết nối mạng</p>
          <p class="text-white/80">Medis sẽ tự đồng bộ lại khi kết nối ổn định.</p>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.offline-banner-enter-active,
.offline-banner-leave-active {
  transition: all 0.24s ease;
}

.offline-banner-enter-from,
.offline-banner-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
