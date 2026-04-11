<script setup lang="ts">
import AppModal from './AppModal.vue'
import AppButton from './AppButton.vue'

defineProps<{
  open: boolean
  title?: string
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <AppModal :open="open" :title="title ?? 'Xác nhận'" size="sm" @close="emit('cancel')">
    <p class="text-sm text-[#374151]">{{ message ?? 'Bạn có chắc muốn thực hiện thao tác này?' }}</p>

    <template #footer>
      <AppButton variant="ghost" @click="emit('cancel')">{{ cancelLabel ?? 'Hủy' }}</AppButton>
      <AppButton
        :variant="danger ? 'danger' : 'primary'"
        :loading="loading"
        @click="emit('confirm')"
      >
        {{ confirmLabel ?? 'Xác nhận' }}
      </AppButton>
    </template>
  </AppModal>
</template>
