<script setup lang="ts">
import { computed } from 'vue'
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
</script>

<template>
  <div class="w-full max-w-6xl mx-auto px-4 py-8 space-y-8">
    <!-- Back button -->
    <button
      @click="router.back()"
      class="w-14 h-10 rounded-xl flex items-center justify-center bg-surface-container-lowest border border-outline-variant text-on-surface shadow-sm hover:bg-surface-container-low transition-all mb-4"
    >
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
    </button>

    <!-- Loading -->
    <div v-if="isLoading" class="space-y-6">
      <div class="bg-surface-container-lowest rounded-3xl p-8 border border-outline-variant/30 shadow-sm animate-pulse">
        <div class="flex items-center gap-4 mb-6">
          <div class="w-14 h-14 bg-gray-100 rounded-2xl" />
          <div class="space-y-2 flex-1">
            <div class="h-8 bg-gray-100 rounded-lg w-1/3" />
            <div class="h-4 bg-gray-100 rounded-lg w-1/4" />
          </div>
        </div>
        <div class="h-20 bg-gray-50 rounded-2xl w-full" />
      </div>
    </div>

    <div v-else-if="error" class="bg-error-container/20 text-error p-6 rounded-2xl text-center border border-error/20">
      <p class="font-medium">Không tìm thấy thông tin hoạt chất này.</p>
    </div>

    <template v-else-if="drug">
      <!-- Drug Hero Section -->
      <div class="bg-surface-container-lowest rounded-3xl overflow-hidden border border-outline-variant/30 shadow-sm">
        <div class="p-8">
          <div class="flex flex-col md:flex-row justify-between items-start gap-6">
            <div class="flex-1">
              <div class="flex items-center gap-4 mb-4">
                <div class="w-14 h-14 rounded-2xl bg-primary-fixed/20 flex items-center justify-center text-primary flex-shrink-0">
                  <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
                  </svg>
                </div>
                <div>
                  <h1 class="text-3xl font-extrabold text-on-surface tracking-tight">{{ drug.generic_name }}</h1>
                  <div class="flex flex-wrap gap-2 mt-2">
                    <span v-for="atc in drug.atc_codes" :key="atc" class="text-xs font-mono font-bold px-2.5 py-1 bg-surface-container-low text-on-surface-variant rounded-lg">
                      ATC: {{ atc }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="flex flex-wrap gap-3 mb-6">
                <span v-for="category in drug.categories" :key="category" class="px-3 py-1 bg-secondary-fixed/20 text-secondary text-xs font-bold rounded-full">
                  {{ category }}
                </span>
                <span v-for="form in drug.dosage_forms" :key="form" class="px-3 py-1 bg-primary-fixed/20 text-primary text-xs font-bold rounded-full">
                  {{ form }}
                </span>
              </div>

              <p class="text-[15px] text-on-surface-variant leading-relaxed max-w-4xl">
                {{ drug.description || 'Chưa có mô tả chi tiết cho hoạt chất này.' }}
              </p>
            </div>
            
            <button 
              @click="router.push({ path: '/interactions', query: { drug: drug.id } })"
              class="bg-[#1D4FD8] text-white px-6 py-3 rounded-2xl text-sm font-bold shadow-lg shadow-blue-200 hover:scale-[1.02] active:scale-95 transition-all flex items-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Kiểm tra tương tác
            </button>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Left Column: Warnings & Interactions -->
        <div class="lg:col-span-2 space-y-8">
          <!-- Warnings -->
          <div v-if="drug.warnings.length > 0" class="bg-surface-container-lowest rounded-3xl p-8 border border-error/10 shadow-sm">
            <h2 class="text-lg font-bold text-on-surface mb-5 flex items-center gap-2">
              <div class="w-8 h-8 rounded-lg bg-error-container/20 flex items-center justify-center text-error">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              Cảnh báo quan trọng
            </h2>
            <div class="space-y-4">
              <div v-for="w in drug.warnings" :key="w.id" class="p-4 bg-error-container/10 rounded-2xl border border-error/5 flex gap-4">
                <div class="w-2 h-2 rounded-full bg-error mt-2 shrink-0" />
                <p class="text-[14px] text-on-surface-variant leading-relaxed">{{ w.warning_text }}</p>
              </div>
            </div>
          </div>

          <!-- Interactions -->
          <div class="bg-surface-container-lowest rounded-3xl p-8 border border-outline-variant/30 shadow-sm">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-lg font-bold text-on-surface">Tương tác thuốc đã biết</h2>
              <span v-if="interactions" class="px-3 py-1 bg-surface-container-low text-on-surface-variant text-xs font-bold rounded-full">
                {{ interactions.items.length }} tương tác
              </span>
            </div>
            
            <div v-if="interactions && interactions.items.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="inter in interactions.items"
                :key="`${inter.drug_id}-${inter.interacts_with_id}`"
                class="group p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-xl hover:shadow-gray-100 transition-all duration-300"
              >
                <div class="flex items-center justify-between mb-3">
                  <p class="font-bold text-on-surface text-[15px]">
                    {{ inter.drug_id === id ? (inter.interacts_with_name || inter.interacts_with_id) : (inter.drug_name || inter.drug_id) }}
                  </p>
                  <span class="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant">
                    {{ inter.source || 'DB' }}
                  </span>
                </div>
                <p v-if="inter.interaction_label" class="text-xs text-on-surface-variant line-clamp-3 leading-relaxed">
                  {{ inter.interaction_label }}
                </p>
                <div v-if="inter.confidence_score != null" class="mt-4 flex items-center gap-2">
                  <div class="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-[#00C2A8]" :style="`width: ${inter.confidence_score * 100}%`" />
                  </div>
                  <span class="text-[10px] font-bold text-[#00897B] shrink-0">
                    {{ (inter.confidence_score * 100).toFixed(0) }}% tin cậy
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-10 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
              <p class="text-sm text-gray-400">Không tìm thấy dữ liệu tương tác trong cơ sở dữ liệu.</p>
            </div>
          </div>
        </div>

        <!-- Right Column: Brand Names -->
        <div class="space-y-8">
          <div class="bg-surface-container-lowest rounded-3xl border border-outline-variant/30 shadow-sm overflow-hidden">
            <div class="p-6 border-b soft-divider bg-surface-container-low/30">
              <h2 class="font-bold text-on-surface">Tên biệt dược</h2>
            </div>
            <div class="divide-y soft-divider max-h-[600px] overflow-y-auto">
              <div v-for="p in drug.brand_names" :key="p.id" class="p-5 hover:bg-surface-container-low transition-colors">
                <p class="font-bold text-on-surface text-sm mb-1">{{ p.name }}</p>
                <div class="flex flex-wrap gap-x-3 gap-y-1 mt-2">
                  <div class="flex items-center gap-1 text-[11px] text-outline">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    {{ p.strength || 'N/A' }}
                  </div>
                  <div class="flex items-center gap-1 text-[11px] text-outline">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    {{ p.country || 'N/A' }}
                  </div>
                </div>
              </div>
              <div v-if="drug.brand_names.length === 0" class="p-10 text-center text-sm text-gray-400">
                Không có dữ liệu biệt dược.
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
