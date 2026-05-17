<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppNavbar from '@/components/layout/AppNavbar.vue'

const uiStore = useUiStore()
</script>

<template>
  <div class="min-h-screen relative overflow-x-hidden bg-page-bg text-on-surface transition-colors duration-300">
    <div class="pointer-events-none fixed inset-0">
      <div class="absolute left-[-8rem] top-[-8rem] h-80 w-80 rounded-full bg-primary-fixed/35 blur-3xl" />
      <div class="absolute bottom-[-10rem] right-[-4rem] h-[26rem] w-[26rem] rounded-full bg-tertiary-fixed/30 blur-3xl" />
    </div>

    <AppSidebar />
    <AppNavbar />
    <button
      v-if="uiStore.mobileSidebarOpen"
      type="button"
      class="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px] lg:hidden"
      @click="uiStore.setMobileSidebar(false)"
    />

    <main
      class="relative z-10 min-h-screen pt-20 transition-all duration-300"
      :class="uiStore.sidebarOpen ? 'lg:pl-[19rem]' : 'lg:pl-[7.25rem]'"
    >
      <div class="mx-auto max-w-screen-2xl px-4 pb-8 sm:px-6 lg:px-8">
        <slot />
      </div>
    </main>
  </div>
</template>
