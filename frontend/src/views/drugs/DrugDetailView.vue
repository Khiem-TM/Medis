<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDrugDetail, useDrugInteractions } from '@/api/drugs.api'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)

const { data: drug, isLoading, error } = useDrugDetail(id)
const { data: interactions } = useDrugInteractions(id)

const descExpanded = ref(false)
const showAllWarnings = ref(false)
const copiedId = ref(false)

function copyId() {
  navigator.clipboard.writeText(drug.value?.id ?? '').then(() => {
    copiedId.value = true
    setTimeout(() => { copiedId.value = false }, 1500)
  })
}

const displayedWarnings = computed(() => {
  if (!drug.value) return []
  return showAllWarnings.value ? drug.value.warnings : drug.value.warnings.slice(0, 3)
})
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- Back -->
    <button
      @click="router.back()"
      class="flex items-center gap-2 text-sm font-semibold transition-all hover:opacity-70"
      style="color:#00685d;"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
      Quay lại
    </button>

    <!-- Loading -->
    <div v-if="isLoading" class="space-y-5">
      <div class="rounded-2xl p-6 space-y-4" style="background:white;border:1px solid rgba(15,23,42,0.08);">
        <AppSkeleton class="h-10 w-64" />
        <AppSkeleton class="h-4 w-full" />
        <AppSkeleton class="h-4 w-3/4" />
      </div>
    </div>

    <div v-else-if="error" class="flex flex-col items-center justify-center py-20 rounded-2xl border" style="background:rgba(239,68,68,0.04);border-color:rgba(239,68,68,0.2);">
      <p class="font-medium" style="color:#DC2626;">Không tìm thấy thông tin hoạt chất này.</p>
    </div>

    <template v-else-if="drug">
      <!-- Page header -->
      <div class="flex items-start justify-between flex-wrap gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest mb-1" style="color:#00685d;">Tra cứu hoạt chất · DrugBank</p>
          <h1 class="text-4xl font-extrabold leading-tight" style="background:linear-gradient(135deg,#0A0F1E,#005048,#00897B);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{{ drug.generic_name }}</h1>
          <!-- Code chips -->
          <div class="flex flex-wrap items-center gap-2 mt-3">
            <button
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono text-xs font-bold border transition-all"
              style="background:rgba(0,104,93,0.08);border-color:rgba(0,104,93,0.2);color:#005048;"
              @click="copyId"
            >
              {{ drug.id }}
              <svg v-if="!copiedId" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
              <svg v-else class="w-3.5 h-3.5" style="color:#059669;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
            </button>
            <span v-if="drug.chemical_formula" class="px-3 py-1.5 rounded-lg font-mono text-xs font-bold border" style="background:rgba(15,23,42,0.03);border-color:rgba(15,23,42,0.1);color:#4B5563;">{{ drug.chemical_formula }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-semibold transition-all hover:bg-gray-50"
            style="border-color:rgba(15,23,42,0.12);color:#1F2937;"
            @click="router.push({ path: '/interactions', query: { drug: drug.id } })"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
            Kiểm tra tương tác
          </button>
        </div>
      </div>

      <!-- Category chips -->
      <div class="rounded-2xl p-4" style="background:white;border:1px solid rgba(15,23,42,0.08);">
        <div class="flex flex-wrap items-center gap-2 mb-3">
          <span class="text-xs font-semibold uppercase tracking-wider" style="color:#9CA3AF;min-width:80px;">Mã ATC</span>
          <div class="flex flex-wrap gap-2">
            <span v-for="atc in drug.atc_codes" :key="atc" class="px-2.5 py-1 rounded-lg font-mono text-xs font-bold border" style="background:rgba(57,73,171,0.08);border-color:rgba(57,73,171,0.18);color:#3949AB;">{{ atc }}</span>
            <span v-if="!drug.atc_codes?.length" class="text-xs" style="color:#9CA3AF;">—</span>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2 mb-3">
          <span class="text-xs font-semibold uppercase tracking-wider" style="color:#9CA3AF;min-width:80px;">Phân loại</span>
          <div class="flex flex-wrap gap-2">
            <span v-for="cat in drug.categories" :key="cat" class="px-2.5 py-1 rounded-full text-xs font-medium" style="background:rgba(0,104,93,0.1);color:#00685d;">{{ cat }}</span>
            <span v-if="!drug.categories?.length" class="text-xs" style="color:#9CA3AF;">—</span>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold uppercase tracking-wider" style="color:#9CA3AF;min-width:80px;">Dạng bào chế</span>
          <div class="flex flex-wrap gap-2">
            <span v-for="form in drug.dosage_forms" :key="form" class="px-2.5 py-1 rounded-full text-xs font-medium" style="background:rgba(15,23,42,0.05);color:#4B5563;">{{ form }}</span>
            <span v-if="!drug.dosage_forms?.length" class="text-xs" style="color:#9CA3AF;">—</span>
          </div>
        </div>
      </div>

      <!-- Two column layout -->
      <div class="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5">
        <!-- Left -->
        <div class="space-y-5">
          <!-- Description -->
          <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.08);">
            <div class="px-5 py-4 border-b" style="border-color:rgba(15,23,42,0.06);">
              <h2 class="font-semibold" style="color:#0A0F1E;">Mô tả</h2>
            </div>
            <div class="p-5">
              <div
                class="text-sm leading-relaxed overflow-hidden transition-all"
                :style="`color:#4B5563;max-height:${descExpanded ? 'none' : '120px'};mask-image:${descExpanded ? 'none' : 'linear-gradient(180deg,#000 60%,transparent 100%)'};-webkit-mask-image:${descExpanded ? 'none' : 'linear-gradient(180deg,#000 60%,transparent 100%)'};`"
              >
                {{ drug.description || 'Chưa có mô tả chi tiết cho hoạt chất này.' }}
              </div>
              <button
                class="mt-3 text-sm font-semibold flex items-center gap-1 transition-colors"
                style="color:#00685d;"
                @click="descExpanded = !descExpanded"
              >
                {{ descExpanded ? 'Thu gọn' : 'Đọc thêm' }}
                <svg class="w-3.5 h-3.5 transition-transform" :class="descExpanded ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
              </button>
            </div>
          </div>

          <!-- Warnings -->
          <div v-if="drug.warnings.length > 0" class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(239,68,68,0.15);">
            <div class="px-5 py-4 border-b flex items-center gap-2" style="border-color:rgba(239,68,68,0.1);background:rgba(239,68,68,0.03);">
              <div class="w-6 h-6 rounded-lg flex items-center justify-center" style="background:rgba(239,68,68,0.12);">
                <svg class="w-3.5 h-3.5" style="color:#EF4444;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              </div>
              <h2 class="font-semibold" style="color:#DC2626;">
                Cảnh báo an toàn
                <span class="ml-1 font-normal text-sm" style="color:#EF4444;">· {{ drug.warnings.length }}</span>
              </h2>
            </div>
            <div class="divide-y" style="border-color:rgba(239,68,68,0.08);">
              <div v-for="w in displayedWarnings" :key="w.id" class="flex items-start gap-3 px-5 py-3.5">
                <div class="w-5 h-5 rounded flex items-center justify-center flex-shrink-0 mt-0.5" style="background:rgba(239,68,68,0.1);">
                  <svg class="w-3 h-3" style="color:#EF4444;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01"/></svg>
                </div>
                <p class="text-sm leading-relaxed" style="color:#4B5563;">{{ w.warning_text }}</p>
              </div>
            </div>
            <div v-if="drug.warnings.length > 3" class="px-5 py-3 border-t" style="border-color:rgba(239,68,68,0.08);">
              <button class="text-sm font-semibold flex items-center gap-1" style="color:#EF4444;" @click="showAllWarnings = !showAllWarnings">
                {{ showAllWarnings ? 'Thu gọn' : `Xem thêm ${drug.warnings.length - 3} cảnh báo` }}
                <svg class="w-3.5 h-3.5 transition-transform" :class="showAllWarnings ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
              </button>
            </div>
          </div>

          <!-- Interactions -->
          <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.08);">
            <div class="px-5 py-4 border-b flex items-center justify-between" style="border-color:rgba(15,23,42,0.06);">
              <h2 class="font-semibold" style="color:#0A0F1E;">
                Tương tác thuốc đã biết
                <span v-if="interactions" class="ml-1.5 text-sm font-normal" style="color:#6B7280;">· {{ interactions.items.length }} đã ghi nhận</span>
              </h2>
            </div>
            <div v-if="interactions && interactions.items.length > 0" class="overflow-x-auto">
              <table class="w-full border-collapse">
                <thead>
                  <tr style="background:rgba(15,23,42,0.03);">
                    <th class="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider" style="color:#6B7280;">Thuốc tương tác</th>
                    <th class="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider" style="color:#6B7280;">Mô tả</th>
                    <th class="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider" style="color:#6B7280;">Nguồn</th>
                    <th class="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider" style="color:#6B7280;">Độ tin cậy</th>
                  </tr>
                </thead>
                <tbody class="divide-y" style="border-color:rgba(15,23,42,0.04);">
                  <tr v-for="inter in interactions.items" :key="`${inter.drug_id}-${inter.interacts_with_id}`" class="hover:bg-gray-50 transition-colors">
                    <td class="px-5 py-3.5 font-semibold text-sm" style="color:#0A0F1E;">
                      {{ inter.drug_id === id ? (inter.interacts_with_name || inter.interacts_with_id) : (inter.drug_name || inter.drug_id) }}
                    </td>
                    <td class="px-5 py-3.5 text-sm max-w-xs" style="color:#4B5563;">{{ inter.interaction_label || '—' }}</td>
                    <td class="px-5 py-3.5">
                      <span class="text-xs font-bold px-2 py-1 rounded-full"
                        :style="(inter.source || 'database') === 'database'
                          ? 'background:rgba(0,104,93,0.1);color:#00685d;border:1px solid rgba(0,104,93,0.2);'
                          : 'background:rgba(57,73,171,0.08);color:#3949AB;border:1px dashed rgba(57,73,171,0.3);'"
                      >
                        {{ (inter.source || 'database') === 'database' ? 'Cơ sở dữ liệu' : 'AI dự đoán' }}
                      </span>
                    </td>
                    <td class="px-5 py-3.5">
                      <span v-if="inter.confidence_score != null" class="text-sm font-bold" style="color:#059669;">
                        {{ Math.round(inter.confidence_score * 100) }}%
                      </span>
                      <span v-else class="text-sm" style="color:#9CA3AF;">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="flex flex-col items-center py-12">
              <p class="text-sm" style="color:#9CA3AF;">Không tìm thấy dữ liệu tương tác.</p>
            </div>
          </div>
        </div>

        <!-- Right: Brand names -->
        <div class="space-y-5">
          <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.08);">
            <div class="px-5 py-4 border-b" style="border-color:rgba(15,23,42,0.06);">
              <h2 class="font-semibold" style="color:#0A0F1E;">
                Sản phẩm thị trường
                <span class="ml-1.5 text-sm font-normal" style="color:#6B7280;">· {{ drug.brand_names.length }}</span>
              </h2>
            </div>
            <div class="divide-y max-h-[520px] overflow-y-auto" style="border-color:rgba(15,23,42,0.04);">
              <RouterLink
                v-for="p in drug.brand_names"
                :key="p.id"
                :to="`/drugs/market/${p.id}`"
                class="flex items-center gap-3 px-5 py-4 transition-all hover:bg-gray-50 block"
              >
                <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style="background:rgba(0,104,93,0.08);">
                  <svg class="w-5 h-5" style="color:#00685d;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold truncate" style="color:#0A0F1E;">{{ p.name }}</p>
                  <p class="text-xs mt-0.5" style="color:#6B7280;">{{ [p.strength, p.country].filter(Boolean).join(' · ') || '—' }}</p>
                </div>
                <svg class="w-4 h-4 flex-shrink-0" style="color:#9CA3AF;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
              </RouterLink>
              <div v-if="!drug.brand_names.length" class="flex flex-col items-center py-10">
                <p class="text-sm" style="color:#9CA3AF;">Không có dữ liệu biệt dược.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
