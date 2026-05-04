<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  open: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}>()

const emit = defineEmits<{ close: [] }>()

function handleKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.open) emit('close')
}

onMounted(() => document.addEventListener('keydown', handleKey))
onUnmounted(() => document.removeEventListener('keydown', handleKey))
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50" @click="emit('close')" />

        <!-- Dialog -->
        <div
          :class="[
            'relative bg-card rounded-2xl shadow-xl flex flex-col max-h-[90vh] w-full',
            size === 'sm' ? 'max-w-sm' : size === 'lg' ? 'max-w-2xl' : size === 'xl' ? 'max-w-4xl' : 'max-w-lg',
          ]"
        >
          <!-- Header -->
          <div v-if="title || $slots.header" class="flex items-center justify-between px-6 py-4 border-b border-outline-variant">
            <h2 class="text-lg font-semibold text-on-surface">
              <slot name="header">{{ title }}</slot>
            </h2>
            <button @click="emit('close')" class="text-outline hover:text-on-surface p-1 rounded-lg hover:bg-surface-container-low">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto px-6 py-4">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-outline-variant flex justify-end gap-2">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.95);
}
</style>
