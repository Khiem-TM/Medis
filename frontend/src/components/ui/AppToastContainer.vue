<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import AppToast from './AppToast.vue'

const uiStore = useUiStore()
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup
        name="toast"
        tag="div"
        class="flex flex-col gap-2"
      >
        <div
          v-for="toast in uiStore.toasts"
          :key="toast.id"
          class="pointer-events-auto"
        >
          <AppToast :toast="toast" @dismiss="uiStore.removeToast(toast.id)" />
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
