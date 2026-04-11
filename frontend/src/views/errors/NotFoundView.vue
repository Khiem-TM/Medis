<script setup lang="ts">
import { useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'

const router = useRouter()
</script>

<template>
  <div class="min-h-screen bg-[#F9FAFB] flex items-center justify-center p-6">
    <div class="text-center max-w-md">
      <div class="w-24 h-24 bg-[#F3F4F6] rounded-full flex items-center justify-center mx-auto mb-6">
        <span class="text-4xl font-bold text-[#9CA3AF]">404</span>
      </div>
      <h1 class="text-2xl font-bold text-[#111827] mb-2">Không tìm thấy trang</h1>
      <p class="text-[#6B7280] mb-6">Trang bạn đang tìm kiếm không tồn tại hoặc đã bị di chuyển.</p>
      <div class="flex gap-3 justify-center">
        <AppButton variant="outline" @click="router.back()">Quay lại</AppButton>
        <AppButton @click="router.push('/dashboard')">Về trang chủ</AppButton>
      </div>
    </div>
  </div>
</template>
