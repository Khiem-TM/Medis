<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppNavbar from '@/components/layout/AppNavbar.vue'

const uiStore = useUiStore()
</script>

<template>
  <div class="min-h-screen bg-[#F9FAFB]">
    <AppSidebar />
    <AppNavbar />

    <!-- Main content -->
    <main
      :class="[
        'pt-14 min-h-screen transition-all duration-200',
        uiStore.sidebarOpen ? 'lg:ml-60' : 'lg:ml-16',
      ]"
    >
      <div class="p-6">
        <slot />
      </div>
    </main>
  </div>
</template>
