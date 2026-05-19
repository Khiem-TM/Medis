<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMarketDrugDetail } from '@/api/market-drugs.api'

const route = useRoute()
const router = useRouter()

const productId = computed(() => Number(route.params.id))
const { data: product, isLoading, isError } = useMarketDrugDetail(productId)

const copiedRegNum = ref(false)

function copyRegNum() {
  navigator.clipboard.writeText(product.value?.registration_number ?? '').then(() => {
    copiedRegNum.value = true
    setTimeout(() => { copiedRegNum.value = false }, 1500)
  })
}

function goCheckInteractions() {
  router.push(`/interactions?mode=market&product_id=${productId.value}`)
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
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
      <div class="rounded-2xl p-6 flex gap-6" style="background:white;border:1px solid rgba(15,23,42,0.08);">
        <div class="w-52 h-52 rounded-xl flex-shrink-0" style="background:rgba(15,23,42,0.04);" />
        <div class="flex-1 space-y-3 pt-2">
          <div class="h-6 rounded-lg w-3/4" style="background:rgba(15,23,42,0.06);" />
          <div class="h-4 rounded-lg w-1/2" style="background:rgba(15,23,42,0.04);" />
          <div class="h-4 rounded-lg w-1/3" style="background:rgba(15,23,42,0.04);" />
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="isError" class="flex flex-col items-center justify-center py-20 rounded-2xl border" style="background:rgba(239,68,68,0.04);border-color:rgba(239,68,68,0.2);">
      <p class="font-medium" style="color:#DC2626;">Không tìm thấy sản phẩm hoặc đã xảy ra lỗi.</p>
    </div>

    <template v-else-if="product">
      <!-- Page header -->
      <div class="flex items-start justify-between flex-wrap gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest mb-1" style="color:#00685d;">Sản phẩm thị trường · DAV</p>
          <h1 class="text-3xl font-extrabold leading-tight" style="color:#0A0F1E;">{{ product.product_name }}</h1>
          <!-- Badges row -->
          <div class="flex flex-wrap items-center gap-2 mt-3">
            <button
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono text-xs font-bold border transition-all"
              style="background:rgba(0,104,93,0.08);border-color:rgba(0,104,93,0.2);color:#005048;"
              @click="copyRegNum"
            >
              Số ĐK · {{ product.registration_number }}
              <svg v-if="!copiedRegNum" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
              <svg v-else class="w-3.5 h-3.5" style="color:#059669;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
            </button>
            <span
              class="px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1.5"
              :style="product.is_expired ? 'background:rgba(239,68,68,0.1);color:#DC2626;' : 'background:rgba(16,185,129,0.1);color:#059669;'"
            >
              <span class="w-1.5 h-1.5 rounded-full inline-block" :style="product.is_expired ? 'background:#EF4444;' : 'background:#10B981;'" />
              {{ product.is_expired ? 'Hết hạn đăng ký' : 'Còn hiệu lực' }}
            </span>
            <span v-if="product.is_withdrawn" class="px-2.5 py-1 rounded-full text-xs font-bold" style="background:rgba(245,158,11,0.1);color:#D97706;">
              Đã rút khỏi thị trường
            </span>
            <span v-if="product.dosage_form" class="px-2.5 py-1 rounded-full text-xs font-medium" style="background:rgba(0,104,93,0.08);color:#00685d;">
              {{ product.dosage_form }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-semibold transition-all hover:bg-gray-50"
            style="border-color:rgba(15,23,42,0.12);color:#1F2937;"
            :disabled="product.resolved_drug_ids.length === 0"
            @click="goCheckInteractions"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
            Kiểm tra tương tác
          </button>
        </div>
      </div>

      <!-- Hero card -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 4px rgba(15,23,42,0.05);">
        <div class="flex flex-col sm:flex-row gap-0">
          <!-- Product image -->
          <div class="sm:w-56 flex-shrink-0 flex items-center justify-center p-6 relative overflow-hidden" style="background:linear-gradient(135deg,rgba(0,104,93,0.06),rgba(0,104,93,0.03));border-right:1px solid rgba(15,23,42,0.06);">
            <div class="absolute inset-0" style="background:radial-gradient(circle at 30% 30%,rgba(0,137,123,0.15),transparent 60%);" />
            <img
              v-if="product.image_url"
              :src="product.image_url"
              :alt="product.product_name"
              class="relative z-10 w-40 h-40 object-contain"
            />
            <div v-else class="relative z-10 w-40 h-40 flex items-center justify-center rounded-xl" style="background:rgba(0,104,93,0.06);">
              <svg class="w-16 h-16" style="color:rgba(0,104,93,0.25);" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <p class="absolute bottom-3 left-0 right-0 text-center text-xs" style="color:#9CA3AF;">Ảnh minh hoạ</p>
          </div>

          <!-- Info grid -->
          <div class="flex-1 p-6">
            <div class="grid grid-cols-2 gap-x-8 gap-y-4">
              <div v-if="product.dosage_form">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Dạng bào chế</p>
                <p class="text-sm font-medium" style="color:#0A0F1E;">{{ product.dosage_form }}</p>
              </div>
              <div v-if="product.route_name">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Đường dùng</p>
                <p class="text-sm font-medium" style="color:#0A0F1E;">{{ product.route_name }}</p>
              </div>
              <div v-if="product.packaging">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Quy cách đóng gói</p>
                <p class="text-sm font-medium" style="color:#0A0F1E;">{{ product.packaging }}</p>
              </div>
              <div v-if="product.quality_standard">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Tiêu chuẩn</p>
                <p class="text-sm font-medium" style="color:#0A0F1E;">{{ product.quality_standard }}</p>
              </div>
              <div v-if="product.shelf_life">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Tuổi thọ</p>
                <p class="text-sm font-medium" style="color:#0A0F1E;">{{ product.shelf_life }}</p>
              </div>
              <div v-if="product.registration_date">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Ngày cấp ĐK</p>
                <p class="text-sm font-medium" style="color:#0A0F1E;">{{ new Date(product.registration_date).toLocaleDateString('vi-VN') }}</p>
              </div>
              <div v-if="product.expiry_date">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Hết hạn ĐK</p>
                <p class="text-sm font-medium" :style="product.is_expired ? 'color:#DC2626;' : 'color:#0A0F1E;'">{{ new Date(product.expiry_date).toLocaleDateString('vi-VN') }}</p>
              </div>
              <div v-if="product.registration_number">
                <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Số đăng ký</p>
                <p class="text-sm font-mono font-bold" style="color:#0A0F1E;">{{ product.registration_number }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Ingredients -->
      <div class="rounded-2xl overflow-hidden" style="background:white;border:1px solid rgba(15,23,42,0.08);box-shadow:0 1px 4px rgba(15,23,42,0.05);">
        <div class="px-6 py-4 border-b flex items-center gap-2" style="border-color:rgba(15,23,42,0.06);">
          <div class="w-6 h-6 rounded-lg flex items-center justify-center" style="background:rgba(57,73,171,0.1);">
            <svg class="w-3.5 h-3.5" style="color:#3949AB;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          </div>
          <h2 class="font-semibold" style="color:#0A0F1E;">Thành phần hoạt chất</h2>
        </div>
        <div class="divide-y" style="border-color:rgba(15,23,42,0.04);">
          <div
            v-for="(ing, idx) in product.ingredient_summary"
            :key="idx"
            class="flex items-center gap-4 px-6 py-4"
          >
            <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style="background:rgba(57,73,171,0.1);">
              <span class="text-xs font-bold" style="color:#3949AB;">{{ idx + 1 }}</span>
            </div>
            <span class="flex-1 text-sm font-medium" style="color:#0A0F1E;">{{ ing }}</span>
            <RouterLink
              v-if="product.resolved_drug_ids[idx]"
              :to="`/drugs/${product.resolved_drug_ids[idx]}`"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all hover:opacity-80 flex-shrink-0"
              style="background:rgba(57,73,171,0.08);border-color:rgba(57,73,171,0.22);color:#3949AB;"
            >
              Xem hoạt chất →
            </RouterLink>
          </div>
          <div v-if="!product.ingredient_summary.length" class="flex flex-col items-center py-10">
            <p class="text-sm" style="color:#9CA3AF;">Chưa có dữ liệu thành phần.</p>
          </div>
        </div>
        <!-- Raw ingredients fallback -->
        <div v-if="product.raw_ingredients_text" class="px-6 py-4 border-t" style="border-color:rgba(15,23,42,0.06);">
          <p class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#9CA3AF;">Nguyên liệu thô (DAV)</p>
          <p class="text-sm" style="color:#4B5563;">{{ product.raw_ingredients_text }}</p>
        </div>
      </div>

      <!-- DDI warning -->
      <div
        v-if="product.resolved_drug_ids.length === 0"
        class="flex items-start gap-3 rounded-2xl px-6 py-4"
        style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.25);"
      >
        <svg class="w-5 h-5 flex-shrink-0 mt-0.5" style="color:#D97706;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p class="text-sm" style="color:#92400E;">
          Thuốc này chưa được mapping sang cơ sở dữ liệu tương tác thuốc (DDI). Không thể kiểm tra tương tác tự động.
        </p>
      </div>
    </template>
  </div>
</template>
