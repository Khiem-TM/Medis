<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSystemLogs, useAdminActivityLogs } from '@/api/admin.api'
import { adminApi } from '@/api/admin.api'
import { usePagination } from '@/composables/usePagination'
import { useToast } from '@/composables/useToast'
import { downloadBlob } from '@/utils/download'
import { formatDateTime } from '@/utils/format'
import type { SystemLogLevel, SystemLogSearchParams, AdminActivityLogSearchParams } from '@/types/admin.types'
import AppTable from '@/components/ui/AppTable.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'

const toast = useToast()
const activeTab = ref<'system' | 'activity'>('system')

// System log filters
const systemLevel = ref<SystemLogLevel | ''>('')
const { page: sPage, size: sSize, params: sPagination, setPage: setSPage, setSize: setSSize } = usePagination(30)

const systemParams = computed<SystemLogSearchParams>(() => ({
  ...sPagination.value,
  level: systemLevel.value || undefined,
}))
const { data: systemData, isLoading: loadingSystem } = useSystemLogs(systemParams)

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

const levelVariantMap: Record<string, string> = {
  DEBUG: 'default',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'danger',
  CRITICAL: 'danger',
}

const systemColumns = [
  { key: 'level', label: 'Mức độ', align: 'center' as const },
  { key: 'source', label: 'Nguồn' },
  { key: 'message', label: 'Nội dung' },
  { key: 'created_at', label: 'Thời gian' },
]

const activityColumns = [
  { key: 'action', label: 'Hành động' },
  { key: 'user_id', label: 'User ID' },
  { key: 'entity_type', label: 'Đối tượng' },
  { key: 'ip_address', label: 'IP' },
  { key: 'created_at', label: 'Thời gian' },
]
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-[#111827]">Nhật ký hệ thống</h1>
        <p class="text-sm text-[#6B7280] mt-1">Theo dõi hoạt động và lỗi hệ thống</p>
      </div>
      <AppButton variant="outline" :loading="exporting" @click="activeTab === 'system' ? exportSystem() : exportActivity()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Xuất Excel
      </AppButton>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-[#F3F4F6] p-1 rounded-xl w-fit">
      <button
        :class="['px-4 py-1.5 rounded-lg text-sm font-medium transition-colors', activeTab === 'system' ? 'bg-white text-[#111827] shadow-sm' : 'text-[#6B7280] hover:text-[#111827]']"
        @click="activeTab = 'system'"
      >
        System Logs
      </button>
      <button
        :class="['px-4 py-1.5 rounded-lg text-sm font-medium transition-colors', activeTab === 'activity' ? 'bg-white text-[#111827] shadow-sm' : 'text-[#6B7280] hover:text-[#111827]']"
        @click="activeTab = 'activity'"
      >
        Activity Logs
      </button>
    </div>

    <!-- System Logs Tab -->
    <template v-if="activeTab === 'system'">
      <div class="bg-white p-3 rounded-xl border border-[#E5E7EB] flex gap-3">
        <AppSelect v-model="systemLevel" :options="levelOptions" class="w-44" />
      </div>

      <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
        <div class="px-4 py-3 border-b border-[#E5E7EB]">
          <p class="text-sm text-[#6B7280]">
            <template v-if="!loadingSystem && systemData">{{ systemData.meta.total.toLocaleString() }} logs</template>
            <template v-else>Đang tải...</template>
          </p>
        </div>

        <AppTable :columns="systemColumns" :data="(systemData?.items ?? []) as any[]" :loading="loadingSystem" empty-message="Không có log nào">
          <template #level="{ row }">
            <AppBadge :variant="(levelVariantMap[row.level] ?? 'default') as any">{{ row.level }}</AppBadge>
          </template>
          <template #source="{ row }">
            <span class="text-xs font-mono text-[#374151]">{{ row.source ?? '—' }}</span>
          </template>
          <template #message="{ row }">
            <span class="text-sm text-[#374151] line-clamp-2">{{ row.message }}</span>
          </template>
          <template #created_at="{ row }">
            <span class="text-xs text-[#9CA3AF] whitespace-nowrap">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </AppTable>

        <div v-if="systemData?.meta" class="px-4 border-t border-[#E5E7EB]">
          <AppPagination :meta="systemData.meta" :model-value="sPage" show-size-selector :size="sSize" @update:model-value="setSPage" @update:size="setSSize" />
        </div>
      </div>
    </template>

    <!-- Activity Logs Tab -->
    <template v-else>
      <div class="bg-white p-3 rounded-xl border border-[#E5E7EB] flex flex-wrap gap-3">
        <AppInput v-model="activityAction" placeholder="Lọc theo hành động..." class="w-52" />
        <div class="flex items-center gap-2">
          <label class="text-sm text-[#6B7280]">Từ:</label>
          <input v-model="activityDateFrom" type="date" class="rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-[#6B7280]">Đến:</label>
          <input v-model="activityDateTo" type="date" class="rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981]" />
        </div>
      </div>

      <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
        <div class="px-4 py-3 border-b border-[#E5E7EB]">
          <p class="text-sm text-[#6B7280]">
            <template v-if="!loadingActivity && activityData">{{ activityData.meta.total.toLocaleString() }} hoạt động</template>
            <template v-else>Đang tải...</template>
          </p>
        </div>

        <AppTable :columns="activityColumns" :data="(activityData?.items ?? []) as any[]" :loading="loadingActivity" empty-message="Không có hoạt động nào">
          <template #action="{ row }">
            <span class="text-xs font-mono font-medium text-[#10B981] bg-[#D1FAE5] px-2 py-0.5 rounded">{{ row.action }}</span>
          </template>
          <template #user_id="{ row }">
            <span class="text-xs font-mono text-[#374151]">{{ row.user_id ?? '—' }}</span>
          </template>
          <template #entity_type="{ row }">
            <span class="text-sm text-[#374151]">{{ row.entity_type ?? '—' }}</span>
          </template>
          <template #ip_address="{ row }">
            <span class="text-xs text-[#9CA3AF]">{{ row.ip_address ?? '—' }}</span>
          </template>
          <template #created_at="{ row }">
            <span class="text-xs text-[#9CA3AF] whitespace-nowrap">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </AppTable>

        <div v-if="activityData?.meta" class="px-4 border-t border-[#E5E7EB]">
          <AppPagination :meta="activityData.meta" :model-value="aPage" show-size-selector :size="aSize" @update:model-value="setAPage" @update:size="setASize" />
        </div>
      </div>
    </template>
  </div>
</template>
