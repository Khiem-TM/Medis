<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import AppNavbar from '@/components/layout/AppNavbar.vue'

const uiStore = useUiStore()
</script>

<template>
  <div class="min-h-screen bg-[#F9FAFB]">
    <AdminSidebar />
    <AppNavbar />

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
