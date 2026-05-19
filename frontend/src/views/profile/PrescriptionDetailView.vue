<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePrescriptionDetail, usePrescriptionInteractions, useCompleteEarlyMutation, useDeletePrescriptionMutation } from '@/api/prescriptions.api'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { formatDate } from '@/utils/format'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { open: confirmOpen, onConfirm, onCancel, confirm } = useConfirm()
const id = computed(() => route.params.id as string)
const showInteractions = ref(false)

const { data: prescription, isLoading } = usePrescriptionDetail(id)
const { data: interactions, isLoading: loadingInteractions, refetch: fetchInteractions } = usePrescriptionInteractions(id)
const { mutate: completeEarly, isPending: completingEarly } = useCompleteEarlyMutation()
const { mutate: deletePrescription, isPending: deleting } = useDeletePrescriptionMutation()

function checkInteractions() {
  showInteractions.value = true
  fetchInteractions()
}

function handleCompleteEarly() {
  completeEarly(id.value, {
    onSuccess: () => toast.success('Đã kết thúc sớm đơn thuốc'),
    onError: (e) => toast.error((e as { message?: string })?.message || 'Không thể kết thúc sớm'),
  })
}

async function handleDelete() {
  const confirmed = await confirm()
  if (!confirmed) return
  deletePrescription(id.value, {
    onSuccess: () => { toast.success('Đã xóa đơn thuốc'); router.back() },
    onError: (e) => toast.error((e as { message?: string })?.message || 'Không thể xóa'),
  })
}

const effectiveInteractions = computed(() => interactions.value ?? prescription.value?.interaction_check ?? null)
const interactionCount = computed(() => effectiveInteractions.value?.interactions.length ?? 0)
const safePairsCount = computed(() => {
  const total = effectiveInteractions.value?.total_pairs ?? 0
  return Math.max(0, total - interactionCount.value)
})

function ringColor(days: number | null): string {
  if (days === null) return '#10B981'
  if (days <= 3) return '#EF4444'
  if (days <= 7) return '#F59E0B'
  return '#10B981'
}

function progressWidth(remaining: number | null, total: number | null): string {
  if (remaining === null || total === null || total === 0) return '0%'
  const elapsed = total - remaining
  return `${Math.max(0, Math.min(100, (elapsed / total) * 100)).toFixed(1)}%`
}

function progressColor(remaining: number | null): string {
  if (remaining === null) return '#00685d'
  if (remaining <= 3) return '#EF4444'
  if (remaining <= 7) return '#F59E0B'
  return '#00685d'
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Page header -->
    <div>
      <p class="text-xs font-semibold uppercase tracking-widest mb-1" style="color:#00685d;">
        Đơn thuốc · #{{ id }}
      </p>
      <h1 class="text-3xl font-extrabold" style="color:#0A0F1E;">Chi tiết đơn</h1>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="space-y-4">
      <div class="rounded-2xl p-6 space-y-4" style="background:white;border:1px solid rgba(15,23,42,0.08);">
        <AppSkeleton class="h-7 w-64" />
        <AppSkeleton class="h-4 w-full" />
        <AppSkeleton class="h-2 w-full rounded-full" />
      </div>
      <div class="rounded-2xl p-6 space-y-3" style="background:white;border:1px solid rgba(15,23,42,0.08);">
        <AppSkeleton v-for="i in 3" :key="i" class="h-16 rounded-xl" />
      </div>
    </div>

    <template v-else-if="prescription">
      <!-- Hero card -->
      <div class="rounded-2xl overflow-hidden" style="background:linear-gradient(145deg,#f0f4ff,#f5f3ff,#fafafa);border:1px solid rgba(15,23,42,0.09);box-shadow:0 2px 12px rgba(15,23,42,0.06);">
        <div class="p-6 space-y-4">
          <!-- Title + action buttons -->
          <div class="flex items-start justify-between gap-4 flex-wrap">
            <h2 class="text-2xl font-extrabold leading-tight" style="color:#0A0F1E;">{{ prescription.name }}</h2>
            <div class="flex items-center gap-2 flex-wrap">
              <button
                v-if="prescription.status === 'active' && prescription.medication_type === 'periodic'"
                @click="handleCompleteEarly"
                :disabled="completingEarly"
                class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-all disabled:opacity-50 hover:bg-amber-50"
                style="border-color:rgba(245,158,11,0.45);color:#D97706;"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                Hoàn thành sớm
              </button>
              <button
                @click="router.back()"
                class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-all hover:bg-gray-50"
                style="border-color:rgba(15,23,42,0.15);color:#374151;"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                Chỉnh sửa
              </button>
              <button
                @click="handleDelete"
                :disabled="deleting"
                class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-all disabled:opacity-50 hover:bg-red-50"
                style="border-color:rgba(239,68,68,0.35);color:#DC2626;"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m0 0a1 1 0 011 1v1H11V6a1 1 0 011-1zm-4 3h8M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8H5z"/></svg>
                Xoá
              </button>
            </div>
          </div>

          <!-- Badges row -->
          <div class="flex flex-wrap items-center gap-2">
            <span
              class="px-3 py-1 rounded-full text-sm font-semibold border"
              :style="prescription.medication_type === 'chronic'
                ? 'background:rgba(237,233,254,0.7);border-color:rgba(124,58,237,0.3);color:#7C3AED;'
                : 'background:rgba(219,234,254,0.7);border-color:rgba(59,130,246,0.3);color:#2563EB;'"
            >{{ prescription.medication_type === 'chronic' ? 'Mãn tính' : 'Định kỳ' }}</span>

            <span
              class="px-3 py-1 rounded-full text-sm font-semibold flex items-center gap-1.5"
              :style="prescription.status === 'active'
                ? 'background:rgba(209,250,229,0.8);color:#059669;'
                : 'background:rgba(243,244,246,1);color:#6B7280;'"
            >
              <span v-if="prescription.status === 'active'" class="w-1.5 h-1.5 rounded-full inline-block" style="background:#10B981;" />
              {{ prescription.status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}
            </span>
          </div>

          <!-- Date + interaction chips row -->
          <div class="flex flex-wrap items-center gap-2">
            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border" style="border-color:rgba(15,23,42,0.15);color:#374151;background:white;">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              {{ formatDate(prescription.start_date) }}
              <span v-if="prescription.end_date"> → {{ formatDate(prescription.end_date) }}</span>
              <span v-else style="color:#9CA3AF;"> · Không thời hạn</span>
            </span>
            <span v-if="prescription.interaction_check?.has_interaction" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold border" style="background:rgba(254,243,199,0.6);border-color:rgba(245,158,11,0.35);color:#D97706;">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              Có tương tác
            </span>
          </div>

          <!-- Divider -->
          <div style="height:1px;background:rgba(15,23,42,0.08);" />

          <!-- Progress section -->
          <template v-if="prescription.medication_type === 'periodic' && prescription.status === 'active' && prescription.days_remaining !== null">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider" style="color:#6B7280;">Tiến độ điều trị</span>
                <span class="text-sm font-semibold" style="color:#0A0F1E;">
                  {{ (prescription.days_total ?? 0) - prescription.days_remaining }} / {{ prescription.days_total ?? '?' }} ngày
                  · còn <span :style="`color:${ringColor(prescription.days_remaining)};`">{{ prescription.days_remaining }} ngày</span>
                </span>
              </div>
              <div class="w-full h-3 rounded-full overflow-hidden" style="background:rgba(15,23,42,0.08);">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="`width:${progressWidth(prescription.days_remaining, prescription.days_total)};background:${progressColor(prescription.days_remaining)};`"
                />
              </div>
            </div>
          </template>

          <!-- Notes -->
          <div v-if="prescription.notes" class="rounded-xl px-4 py-3" style="background:rgba(254,252,232,0.8);border:1px solid rgba(234,179,8,0.2);">
            <p class="text-xs font-semibold mb-1" style="color:#92400E;">Ghi chú điều trị</p>
            <p class="text-sm italic" style="color:#4B5563;">{{ prescription.notes }}</p>
          </div>
        </div>
      </div>

      <!-- Drug items section -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.09);box-shadow:0 1px 4px rgba(15,23,42,0.05);">
        <div class="flex items-center justify-between px-6 py-4">
          <div class="flex items-center gap-3">
            <div class="w-1 h-6 rounded-full" style="background:#00685d;" />
            <h2 class="font-bold text-base" style="color:#0A0F1E;">
              Thuốc trong đơn
              <span class="font-normal text-sm ml-1.5" style="color:#6B7280;">· {{ prescription.items.length }} loại</span>
            </h2>
          </div>
          <button
            @click="router.push('/profile/prescriptions')"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-all hover:bg-gray-50"
            style="border-color:rgba(15,23,42,0.15);color:#374151;"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Thêm thuốc
          </button>
        </div>

        <div class="divide-y" style="border-color:rgba(15,23,42,0.05);">
          <div
            v-for="(item, i) in prescription.items"
            :key="item.id"
            class="flex items-start gap-4 px-6 py-4"
          >
            <!-- Thumbnail -->
            <div class="flex-shrink-0 w-[72px] h-[72px] rounded-xl overflow-hidden flex items-center justify-center" style="background:#EDE9FE;border:1px solid rgba(124,58,237,0.12);">
              <img v-if="item.market_product?.image_url" :src="item.market_product.image_url" :alt="item.drug_name" class="w-full h-full object-cover" />
              <svg v-else class="w-8 h-8" style="color:#7C3AED;opacity:0.6;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
              </svg>
            </div>

            <div class="flex-1 min-w-0">
              <p class="font-bold text-base mb-0.5" style="color:#0A0F1E;">{{ item.drug_name }}</p>
              <p class="text-sm mb-3" style="color:#6B7280;">
                <span class="font-semibold" style="color:#374151;">{{ item.dosage }}</span>
                <span v-if="item.frequency"> · {{ item.frequency }}</span>
                <span v-if="item.duration"> · {{ item.duration }}</span>
              </p>
              <div class="flex flex-wrap gap-2">
                <RouterLink
                  v-if="item.market_product_id"
                  :to="`/drugs/market/${item.market_product_id}`"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all hover:opacity-80"
                  style="border-color:rgba(0,104,93,0.25);color:#00685d;background:white;"
                  @click.stop
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                  Xem sản phẩm thị trường →
                </RouterLink>
                <RouterLink
                  v-if="item.drug_id"
                  :to="`/drugs/${item.drug_id}`"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all hover:opacity-80"
                  style="border-color:rgba(0,104,93,0.25);color:#00685d;background:white;"
                  @click.stop
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                  Xem hoạt chất →
                </RouterLink>
                <span v-if="!item.drug_id && !item.market_product_id" class="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium" style="background:rgba(15,23,42,0.04);color:#9CA3AF;">Chưa liên kết dữ liệu</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Interactions section -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.09);box-shadow:0 1px 4px rgba(15,23,42,0.05);">
        <div class="flex items-center justify-between px-6 py-4 border-b" style="border-color:rgba(15,23,42,0.06);">
          <div class="flex items-center gap-3">
            <div class="w-1 h-6 rounded-full" style="background:#00685d;" />
            <h2 class="font-bold text-base" style="color:#0A0F1E;">Kiểm tra tương tác</h2>
          </div>
          <button
            v-if="!showInteractions || !effectiveInteractions"
            @click="checkInteractions"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-all hover:bg-gray-50"
            style="border-color:rgba(15,23,42,0.15);color:#374151;"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
            Kiểm tra lại
          </button>
        </div>

        <div class="p-6 space-y-3">
          <div v-if="loadingInteractions" class="space-y-3">
            <AppSkeleton v-for="i in 2" :key="i" class="h-20 rounded-xl" />
          </div>

          <template v-else-if="effectiveInteractions">
            <!-- Interaction cards -->
            <div
              v-for="interaction in effectiveInteractions.interactions"
              :key="`${interaction.drug_id}-${interaction.interacts_with_id}`"
              class="rounded-xl p-4"
              style="background:rgba(254,242,242,0.7);border:1px solid rgba(239,68,68,0.2);"
            >
              <!-- Drug pair -->
              <div class="flex items-center gap-2 mb-2 flex-wrap">
                <svg class="w-3.5 h-3.5" style="color:#6B7280;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                <span class="font-bold text-sm" style="color:#0A0F1E;">{{ interaction.drug_name || interaction.drug_id }}</span>
                <svg class="w-4 h-4 rounded-full p-0.5" style="color:#DC2626;background:rgba(239,68,68,0.1);" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                <svg class="w-3.5 h-3.5" style="color:#6B7280;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                <span class="font-bold text-sm" style="color:#0A0F1E;">{{ interaction.interacts_with_name || interaction.interacts_with_id }}</span>
              </div>
              <!-- Description -->
              <p v-if="interaction.interaction_label" class="text-sm mb-3" style="color:#DC2626;">{{ interaction.interaction_label }}</p>
              <!-- Badges -->
              <div class="flex flex-wrap gap-2">
                <span
                  class="text-xs font-semibold px-2.5 py-1 rounded-full"
                  :style="(interaction.source ?? 'database') === 'database'
                    ? 'background:rgba(219,234,254,0.8);border:1px solid rgba(59,130,246,0.3);color:#2563EB;'
                    : 'background:rgba(237,233,254,0.6);border:1px dashed rgba(124,58,237,0.4);color:#7C3AED;'"
                >
                  {{ (interaction.source ?? 'database') === 'database' ? 'Cơ sở dữ liệu' : `AI dự đoán${interaction.confidence_score != null ? ' · ' + Math.round(interaction.confidence_score * 100) + '%' : ''}` }}
                </span>
                <span v-if="interaction.severity" class="text-xs font-semibold px-2.5 py-1 rounded-full border" style="background:rgba(254,242,242,0.8);border-color:rgba(239,68,68,0.3);color:#DC2626;">
                  {{ interaction.severity }}
                </span>
              </div>
            </div>

            <!-- Safe pairs count -->
            <p v-if="safePairsCount > 0" class="flex items-center gap-1.5 text-sm font-medium" style="color:#059669;">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
              {{ safePairsCount }} cặp thuốc an toàn còn lại
            </p>

            <!-- No interactions -->
            <div v-if="!effectiveInteractions.has_interaction" class="flex items-center gap-3 p-4 rounded-xl" style="background:rgba(209,250,229,0.4);border:1px solid rgba(16,185,129,0.2);">
              <svg class="w-5 h-5 flex-shrink-0" style="color:#059669;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <div>
                <p class="text-sm font-semibold" style="color:#059669;">Không phát hiện tương tác nguy hiểm</p>
                <p class="text-xs mt-0.5" style="color:#6B7280;">{{ effectiveInteractions.total_pairs }} cặp thuốc đã kiểm tra</p>
              </div>
            </div>
          </template>

          <!-- Not yet checked -->
          <div v-else class="flex flex-col items-center py-8">
            <svg class="w-10 h-10 mb-3" style="color:rgba(0,104,93,0.25);" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
            <p class="text-sm font-semibold mb-1" style="color:#0A0F1E;">Chưa kiểm tra tương tác</p>
            <p class="text-xs mb-4" style="color:#6B7280;">Nhấn "Kiểm tra lại" để phân tích các thuốc trong đơn</p>
            <button
              @click="checkInteractions"
              class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white"
              style="background:linear-gradient(135deg,#00685d,#00897B);"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
              Kiểm tra tương tác
            </button>
          </div>
        </div>
      </div>

      <!-- Quick actions -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.09);box-shadow:0 1px 4px rgba(15,23,42,0.05);">
        <div class="px-6 pt-5 pb-2">
          <p class="text-xs font-bold uppercase tracking-widest" style="color:#9CA3AF;">Thao tác nhanh</p>
        </div>
        <div class="divide-y" style="border-color:rgba(15,23,42,0.05);">
          <button
            class="w-full flex items-center gap-3 px-6 py-4 text-left transition-colors hover:bg-gray-50"
            @click="router.push('/schedule')"
          >
            <svg class="w-5 h-5 flex-shrink-0" style="color:#6B7280;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <span class="text-sm font-medium" style="color:#0A0F1E;">Đặt nhắc nhở uống thuốc</span>
          </button>
          <button
            class="w-full flex items-center gap-3 px-6 py-4 text-left transition-colors hover:bg-gray-50"
            @click="router.push('/chatbot')"
          >
            <svg class="w-5 h-5 flex-shrink-0" style="color:#6B7280;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.347.347a3.75 3.75 0 01-5.303 0l-.347-.347z"/></svg>
            <span class="text-sm font-medium" style="color:#0A0F1E;">Hỏi AI về đơn này</span>
          </button>
          <button
            class="w-full flex items-center gap-3 px-6 py-4 text-left transition-colors hover:bg-blue-50 rounded-b-2xl"
            style="border:1.5px solid transparent;"
            @click="navigator.clipboard.writeText(window.location.href).then(() => {}).catch(() => {})"
          >
            <svg class="w-5 h-5 flex-shrink-0" style="color:#6B7280;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
            <span class="text-sm font-medium" style="color:#0A0F1E;">Chia sẻ đơn</span>
          </button>
        </div>
      </div>
    </template>

    <AppConfirmDialog :open="confirmOpen" title="Xóa đơn thuốc" message="Bạn có chắc muốn xóa đơn thuốc này? Hành động này không thể hoàn tác." danger :loading="deleting" @confirm="onConfirm" @cancel="onCancel" />
  </div>
</template>
