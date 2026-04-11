<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen bg-[#F9FAFB] flex flex-col items-center justify-center px-4 py-12">
    <!-- Logo -->
    <div class="mb-8 text-center">
      <router-link to="/" class="inline-flex items-center gap-2 group">
        <div class="w-10 h-10 bg-[#10B981] rounded-xl flex items-center justify-center shadow-sm">
          <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <span class="text-2xl font-bold text-[#111827] group-hover:text-[#10B981] transition-colors">Medis</span>
      </router-link>
      <p class="mt-1 text-sm text-[#6B7280]">Quản lý thuốc & sức khỏe thông minh</p>
    </div>

    <!-- Card -->
    <div class="w-full max-w-md bg-white rounded-2xl shadow-sm border border-[#E5E7EB] p-8">
      <slot />
    </div>
  </div>
</template>
