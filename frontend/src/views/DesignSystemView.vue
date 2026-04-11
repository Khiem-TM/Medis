<script setup lang="ts">
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppAvatar from '@/components/ui/AppAvatar.vue'
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-10 py-8">
    <div>
      <h1 class="text-3xl font-bold text-[#111827]">Design System</h1>
      <p class="text-[#6B7280] mt-1">Medis UI component library</p>
    </div>

    <!-- Colors -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Colors</h2>
      <div class="grid grid-cols-4 gap-3">
        <div class="h-16 bg-[#10B981] rounded-xl flex items-end p-2"><span class="text-xs text-white font-medium">Primary #10B981</span></div>
        <div class="h-16 bg-[#059669] rounded-xl flex items-end p-2"><span class="text-xs text-white font-medium">Primary-dk #059669</span></div>
        <div class="h-16 bg-[#D1FAE5] rounded-xl border border-[#6EE7B7] flex items-end p-2"><span class="text-xs text-[#065F46] font-medium">Primary-lt #D1FAE5</span></div>
        <div class="h-16 bg-[#EF4444] rounded-xl flex items-end p-2"><span class="text-xs text-white font-medium">Danger #EF4444</span></div>
        <div class="h-16 bg-[#F59E0B] rounded-xl flex items-end p-2"><span class="text-xs text-white font-medium">Warning #F59E0B</span></div>
        <div class="h-16 bg-[#F9FAFB] rounded-xl border border-[#E5E7EB] flex items-end p-2"><span class="text-xs text-[#374151] font-medium">Page bg #F9FAFB</span></div>
        <div class="h-16 bg-[#111827] rounded-xl flex items-end p-2"><span class="text-xs text-white font-medium">Text #111827</span></div>
        <div class="h-16 bg-[#6B7280] rounded-xl flex items-end p-2"><span class="text-xs text-white font-medium">Muted #6B7280</span></div>
      </div>
    </section>

    <!-- Buttons -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Buttons</h2>
      <div class="flex flex-wrap gap-3">
        <AppButton>Primary</AppButton>
        <AppButton variant="outline">Outline</AppButton>
        <AppButton variant="ghost">Ghost</AppButton>
        <AppButton variant="danger">Danger</AppButton>
        <AppButton :loading="true">Loading</AppButton>
        <AppButton :disabled="true">Disabled</AppButton>
        <AppButton size="sm">Small</AppButton>
        <AppButton size="lg">Large</AppButton>
      </div>
    </section>

    <!-- Inputs -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Inputs</h2>
      <div class="grid grid-cols-2 gap-4 max-w-xl">
        <AppInput placeholder="Nhập văn bản..." model-value="" />
        <AppInput placeholder="Có icon" model-value="">
          <template #prefix>
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </template>
        </AppInput>
        <AppInput placeholder="Lỗi" model-value="" error="Trường này không hợp lệ" />
        <AppInput placeholder="Disabled" model-value="" :disabled="true" />
      </div>
    </section>

    <!-- Badges -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Badges</h2>
      <div class="flex flex-wrap gap-2">
        <AppBadge>Default</AppBadge>
        <AppBadge variant="success">Success</AppBadge>
        <AppBadge variant="danger">Danger</AppBadge>
        <AppBadge variant="warning">Warning</AppBadge>
        <AppBadge variant="info">Info</AppBadge>
      </div>
    </section>

    <!-- Alerts -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Alerts</h2>
      <div class="space-y-3 max-w-xl">
        <AppAlert type="success">Thao tác thành công! Dữ liệu đã được lưu.</AppAlert>
        <AppAlert type="error">Đã xảy ra lỗi. Vui lòng thử lại sau.</AppAlert>
        <AppAlert type="warning">Cảnh báo: Hành động này không thể hoàn tác.</AppAlert>
        <AppAlert type="info">Thông tin: Hệ thống đang được bảo trì.</AppAlert>
      </div>
    </section>

    <!-- Spinners & Skeletons -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Loading States</h2>
      <div class="flex items-center gap-6 mb-4">
        <AppSpinner size="sm" class="text-[#10B981]" />
        <AppSpinner size="md" class="text-[#10B981]" />
        <AppSpinner size="lg" class="text-[#10B981]" />
      </div>
      <div class="space-y-2 max-w-md">
        <AppSkeleton class="h-4 w-full" />
        <AppSkeleton class="h-4 w-3/4" />
        <AppSkeleton class="h-4 w-1/2" />
        <AppSkeleton class="h-8 w-32 mt-4" />
      </div>
    </section>

    <!-- Avatars -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Avatars</h2>
      <div class="flex items-center gap-4">
        <AppAvatar name="Nguyen Van A" size="sm" />
        <AppAvatar name="Tran Thi B" size="md" />
        <AppAvatar name="Le Van C" size="lg" />
        <AppAvatar src="https://i.pravatar.cc/150?img=1" name="With Image" size="md" />
      </div>
    </section>

    <!-- Typography -->
    <section>
      <h2 class="text-xl font-semibold text-[#111827] mb-4">Typography (Inter)</h2>
      <div class="space-y-2">
        <p class="text-4xl font-bold text-[#111827]">Heading 4xl Bold</p>
        <p class="text-2xl font-bold text-[#111827]">Heading 2xl Bold</p>
        <p class="text-xl font-semibold text-[#111827]">Heading xl Semibold</p>
        <p class="text-base font-medium text-[#374151]">Body Base Medium</p>
        <p class="text-sm text-[#374151]">Body Small Regular</p>
        <p class="text-xs text-[#6B7280]">Caption xs Muted</p>
        <p class="text-xs font-mono text-[#374151]">Monospace: A01AA01</p>
      </div>
    </section>
  </div>
</template>
