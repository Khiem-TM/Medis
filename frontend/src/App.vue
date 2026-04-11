<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterView } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import AppToastContainer from '@/components/ui/AppToastContainer.vue'

const route = useRoute()
const layout = computed(() => route.meta.layout ?? 'none')
</script>

<template>
  <AppToastContainer />

  <AppLayout v-if="layout === 'app'">
    <RouterView />
  </AppLayout>

  <AdminLayout v-else-if="layout === 'admin'">
    <RouterView />
  </AdminLayout>

  <AuthLayout v-else-if="layout === 'auth'">
    <RouterView />
  </AuthLayout>

  <RouterView v-else />
</template>
