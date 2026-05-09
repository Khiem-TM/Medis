<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppNavbar from '@/components/layout/AppNavbar.vue'

const uiStore = useUiStore()
</script>

<template>
  <div class="min-h-screen" style="background: #F3F5F7;">
    <AppSidebar />
    <AppNavbar />

    <main
      class="pt-14 min-h-screen transition-[margin] duration-200"
      :class="uiStore.sidebarOpen ? 'lg:ml-60' : 'lg:ml-16'"
    >
      <div class="p-6 max-w-screen-2xl">
        <slot />
      </div>
    </main>
  </div>
</template>
