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
  <div class="w-full overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-surface-container-low border-b border-outline-variant">
          <th
            v-for="col in columns"
            :key="col.key"
            :style="col.width ? `width: ${col.width}` : ''"
            :class="[
              'px-4 py-3 font-medium text-outline whitespace-nowrap',
              col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left',
            ]"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>

      <tbody class="divide-y divide-outline-variant bg-card">
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
            class="hover:bg-surface-container-low transition-colors"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-4 py-3 text-on-surface-variant',
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
