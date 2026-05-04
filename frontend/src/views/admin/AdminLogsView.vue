<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSystemLogs, useAdminActivityLogs, useAdminStats } from '@/api/admin.api'
import { adminApi } from '@/api/admin.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { downloadBlob } from '@/utils/download'
import { formatDateTime } from '@/utils/format'
import type { SystemLogLevel, SystemLogSearchParams, AdminActivityLogSearchParams } from '@/types/admin.types'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import StatCard from '@/components/ui/StatCard.vue'

const toast = useToast()
const activeTab = ref<'system' | 'activity'>('system')

// Stats
const { data: stats, isLoading: loadingStats } = useAdminStats()

// System log filters
const systemLevel = ref<SystemLogLevel | ''>('')
const { page: sPage, size: sSize, params: sPagination, setPage: setSPage, setSize: setSSize } = usePagination(30)

const systemParams = computed<SystemLogSearchParams>(() => ({
  ...sPagination.value,
  level: systemLevel.value || undefined,
}))
const { data: systemData, isLoading: loadingSystem } = useSystemLogs(systemParams)

// Derived metric: critical count from current page (approximation)
const criticalCount = computed(() =>
  systemData.value?.items.filter((l) => l.level === 'CRITICAL' || l.level === 'ERROR').length ?? 0,
)

// Activity log filters
const activityAction = ref('')
const activityDateFrom = ref('')
const activityDateTo = ref('')
const { page: aPage, size: aSize, params: aPagination, setPage: setAPage, setSize: setASize } = usePagination(30)

const activityParams = computed<AdminActivityLogSearchParams>(() => ({
  ...aPagination.value,
  action: activityAction.value || undefined,
  date_from: activityDateFrom.value || undefined,
  date_to: activityDateTo.value || undefined,
}))
const { data: activityData, isLoading: loadingActivity } = useAdminActivityLogs(activityParams)

const exporting = ref(false)

async function exportSystem() {
  exporting.value = true
  try {
    const blob = await adminApi.exportSystemLogs()
    downloadBlob(blob, 'system-logs.xlsx')
  } catch {
    toast.error('Không thể xuất file')
  } finally {
    exporting.value = false
  }
}

async function exportActivity() {
  exporting.value = true
  try {
    const blob = await adminApi.exportActivityLogs()
    downloadBlob(blob, 'activity-logs.xlsx')
  } catch {
    toast.error('Không thể xuất file')
  } finally {
    exporting.value = false
  }
}

const levelOptions = [
  { label: 'Tất cả mức độ', value: '' },
  { label: 'DEBUG', value: 'DEBUG' },
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'CRITICAL', value: 'CRITICAL' },
]

function getLevelClasses(level: string) {
  switch (level) {
    case 'CRITICAL': return 'bg-error text-white'
    case 'ERROR':    return 'bg-error-container text-error'
    case 'WARNING':  return 'bg-yellow-100 text-yellow-700'
    case 'INFO':     return 'bg-primary-fixed text-primary'
    case 'DEBUG':    return 'bg-surface-container text-outline'
    default:         return 'bg-surface-container text-outline'
  }
}

function getActionClasses(action: string) {
  if (action?.includes('DELETE') || action?.includes('delete')) return 'bg-error-container text-error'
  if (action?.includes('CREATE') || action?.includes('create') || action?.includes('register')) return 'bg-tertiary-fixed text-tertiary'
  if (action?.includes('login') || action?.includes('LOGIN')) return 'bg-primary-fixed text-primary'
  return 'bg-surface-container text-on-surface-variant'
}

function getAvatarInitials(userId: string | null) {
  if (!userId) return '?'
  return userId.slice(0, 2).toUpperCase()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-on-surface">Nhật ký hệ thống</h1>
        <p class="text-sm text-outline mt-0.5">Theo dõi hoạt động và lỗi hệ thống</p>
      </div>
      <button
        :disabled="exporting"
        @click="activeTab === 'system' ? exportSystem() : exportActivity()"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary border border-primary/30 rounded-xl hover:bg-primary hover:text-white transition-colors disabled:opacity-50"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        {{ exporting ? 'Đang xuất...' : 'Xuất Excel' }}
      </button>
    </div>

    <!-- Metric cards -->
    <div v-if="loadingStats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <AppSkeleton v-for="i in 4" :key="i" class="h-24 rounded-2xl" />
    </div>
    <div v-else-if="stats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Critical Alerts -->
      <StatCard
        label="Lỗi nghiêm trọng"
        :value="criticalCount.toString()"
        change="trang hiện tại"
        :changePositive="criticalCount === 0"
        iconColor="bg-error-container"
      >
        <template #icon>
          <svg class="w-5 h-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </template>
      </StatCard>

      <!-- System Health -->
      <StatCard
        label="Tổng log hệ thống"
        :value="systemData?.meta.total.toLocaleString() ?? '—'"
        iconColor="bg-primary-fixed"
      >
        <template #icon>
          <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
          </svg>
        </template>
      </StatCard>

      <!-- Active Sessions -->
      <StatCard
        label="Hoạt động người dùng"
        :value="activityData?.meta.total.toLocaleString() ?? '—'"
        iconColor="bg-tertiary-fixed"
      >
        <template #icon>
          <svg class="w-5 h-5 text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </template>
      </StatCard>

      <!-- Total Users -->
      <StatCard
        label="Tổng người dùng"
        :value="stats.total_users.toLocaleString()"
        :change="`+${stats.new_users_today} hôm nay`"
        :changePositive="true"
        iconColor="bg-secondary-container"
      >
        <template #icon>
          <svg class="w-5 h-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </template>
      </StatCard>
    </div>

    <!-- Tab navigation -->
    <div class="flex gap-1 bg-surface-container p-1 rounded-xl w-fit">
      <button
        :class="[
          'px-5 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'system'
            ? 'bg-card text-on-surface shadow-sm'
            : 'text-outline hover:text-on-surface',
        ]"
        @click="activeTab = 'system'"
      >
        System Logs
      </button>
      <button
        :class="[
          'px-5 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'activity'
            ? 'bg-card text-on-surface shadow-sm'
            : 'text-outline hover:text-on-surface',
        ]"
        @click="activeTab = 'activity'"
      >
        Activity Logs
      </button>
    </div>

    <!-- System Logs Tab -->
    <template v-if="activeTab === 'system'">
      <div class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
        <!-- Filter bar -->
        <div class="px-5 py-4 border-b border-outline-variant flex flex-wrap gap-3 bg-card">
          <select
            v-model="systemLevel"
            class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option v-for="opt in levelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <div class="ml-auto flex items-center text-sm text-outline">
            <template v-if="!loadingSystem && systemData">{{ systemData.meta.total.toLocaleString() }} logs</template>
          </div>
        </div>

        <!-- Table -->
        <div v-if="loadingSystem" class="p-5 space-y-3">
          <AppSkeleton v-for="i in 5" :key="i" class="h-12 rounded-xl" />
        </div>
        <div v-else-if="!systemData?.items.length" class="text-center py-16">
          <p class="text-sm text-outline">Không có log nào</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-low border-b border-outline-variant">
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider w-28 text-center">Mức độ</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider w-36">Nguồn</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Nội dung</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider w-40">Thời gian</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant/50">
              <tr
                v-for="log in systemData.items"
                :key="log.id"
                class="hover:bg-surface-container-low/50 transition-colors"
              >
                <td class="px-5 py-3 text-center">
                  <span :class="['px-2.5 py-0.5 rounded-full text-xs font-bold', getLevelClasses(log.level)]">
                    {{ log.level }}
                  </span>
                </td>
                <td class="px-5 py-3">
                  <code class="text-xs font-mono text-on-surface-variant">{{ log.source ?? '—' }}</code>
                </td>
                <td class="px-5 py-3">
                  <p class="text-sm text-on-surface line-clamp-2">{{ log.message }}</p>
                </td>
                <td class="px-5 py-3 text-xs text-outline whitespace-nowrap">{{ formatDateTime(log.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="systemData?.meta" class="px-5 border-t border-outline-variant">
          <AppPagination :meta="systemData.meta" :model-value="sPage" show-size-selector :size="sSize" @update:model-value="setSPage" @update:size="setSSize" />
        </div>
      </div>
    </template>

    <!-- Activity Logs Tab -->
    <template v-else>
      <div class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
        <!-- Filter bar -->
        <div class="px-5 py-4 border-b border-outline-variant flex flex-wrap gap-3 bg-card">
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-outline pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              v-model="activityAction"
              type="text"
              placeholder="Lọc theo hành động..."
              class="pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
          </div>
          <div class="flex items-center gap-2">
            <label class="text-sm text-outline whitespace-nowrap">Từ:</label>
            <input
              v-model="activityDateFrom"
              type="date"
              class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>
          <div class="flex items-center gap-2">
            <label class="text-sm text-outline whitespace-nowrap">Đến:</label>
            <input
              v-model="activityDateTo"
              type="date"
              class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>
          <div class="ml-auto flex items-center text-sm text-outline">
            <template v-if="!loadingActivity && activityData">{{ activityData.meta.total.toLocaleString() }} hoạt động</template>
          </div>
        </div>

        <!-- Table -->
        <div v-if="loadingActivity" class="p-5 space-y-3">
          <AppSkeleton v-for="i in 5" :key="i" class="h-12 rounded-xl" />
        </div>
        <div v-else-if="!activityData?.items.length" class="text-center py-16">
          <p class="text-sm text-outline">Không có hoạt động nào</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-low border-b border-outline-variant">
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Người dùng</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Hành động</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Đối tượng</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">IP</th>
                <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider w-40">Thời gian</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant/50">
              <tr
                v-for="log in activityData.items"
                :key="(log as any).id"
                class="hover:bg-surface-container-low/50 transition-colors"
              >
                <td class="px-5 py-3">
                  <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-lg bg-primary-fixed flex items-center justify-center flex-shrink-0">
                      <span class="text-xs font-bold text-primary">{{ getAvatarInitials((log as any).user_id) }}</span>
                    </div>
                    <code class="text-xs font-mono text-on-surface-variant truncate max-w-24">{{ (log as any).user_id ?? '—' }}</code>
                  </div>
                </td>
                <td class="px-5 py-3">
                  <span :class="['px-2.5 py-0.5 rounded-full text-xs font-bold font-mono', getActionClasses((log as any).action)]">
                    {{ (log as any).action }}
                  </span>
                </td>
                <td class="px-5 py-3 text-sm text-on-surface-variant">{{ (log as any).entity_type ?? '—' }}</td>
                <td class="px-5 py-3">
                  <code class="text-xs text-outline">{{ (log as any).ip_address ?? '—' }}</code>
                </td>
                <td class="px-5 py-3 text-xs text-outline whitespace-nowrap">{{ formatDateTime((log as any).created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="activityData?.meta" class="px-5 border-t border-outline-variant">
          <AppPagination :meta="activityData.meta" :model-value="aPage" show-size-selector :size="aSize" @update:model-value="setAPage" @update:size="setASize" />
        </div>
      </div>
    </template>
  </div>
</template>
