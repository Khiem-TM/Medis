<script setup lang="ts" generic="T extends Record<string, unknown>">
import AppSkeleton from './AppSkeleton.vue'
import AppEmptyState from './AppEmptyState.vue'

export interface TableColumn {
  key: string
  label: string
  width?: string
  align?: 'left' | 'center' | 'right'
}

defineProps<{
  columns: TableColumn[]
  data: T[]
  loading?: boolean
  emptyMessage?: string
  skeletonRows?: number
}>()
</script>

<template>
  <div class="w-full overflow-x-auto rounded-xl border border-[#E5E7EB]">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-[#F9FAFB] border-b border-[#E5E7EB]">
          <th
            v-for="col in columns"
            :key="col.key"
            :style="col.width ? `width: ${col.width}` : ''"
            :class="[
              'px-4 py-3 font-medium text-[#6B7280] whitespace-nowrap',
              col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left',
            ]"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>

      <tbody class="divide-y divide-[#E5E7EB] bg-white">
        <!-- Loading skeleton -->
        <template v-if="loading">
          <tr v-for="i in skeletonRows ?? 5" :key="i">
            <td v-for="col in columns" :key="col.key" class="px-4 py-3">
              <AppSkeleton class="h-4 w-full" />
            </td>
          </tr>
        </template>

        <!-- Empty state -->
        <tr v-else-if="data.length === 0">
          <td :colspan="columns.length">
            <AppEmptyState :title="emptyMessage ?? 'Không có dữ liệu'" />
          </td>
        </tr>

        <!-- Data rows -->
        <template v-else>
          <tr
            v-for="(row, idx) in data"
            :key="idx"
            class="hover:bg-[#F9FAFB] transition-colors"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-4 py-3 text-[#374151]',
                col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left',
              ]"
            >
              <slot :name="col.key" :row="row" :value="row[col.key]">
                {{ row[col.key] ?? '—' }}
              </slot>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
