<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMarketDrugDetail } from '@/api/market-drugs.api'

const route = useRoute()
const router = useRouter()

const productId = computed(() => Number(route.params.id))
const { data: product, isLoading, isError } = useMarketDrugDetail(productId)

function goCheckInteractions() {
  router.push(`/interactions?mode=market&product_id=${productId.value}`)
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <!-- Back button -->
    <button
      type="button"
      class="flex items-center gap-2 text-sm mb-6 transition-colors hover:opacity-70"
      style="color: #5A6985;"
      @click="router.back()"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      Quay lại
    </button>

    <!-- Loading -->
    <div v-if="isLoading" class="space-y-6">
      <div class="bg-white rounded-2xl p-6 animate-pulse" style="border: 1px solid rgba(12,29,66,0.08);">
        <div class="flex gap-6">
          <div class="w-52 h-52 rounded-xl bg-gray-100 flex-shrink-0" />
          <div class="flex-1 space-y-3 pt-2">
            <div class="h-7 bg-gray-100 rounded w-3/4" />
            <div class="h-4 bg-gray-100 rounded w-1/2" />
            <div class="h-4 bg-gray-100 rounded w-1/3" />
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="isError" class="text-center py-16">
      <p class="text-sm" style="color: #EF4444;">Không tìm thấy sản phẩm hoặc đã xảy ra lỗi.</p>
    </div>

    <!-- Content -->
    <template v-else-if="product">
      <!-- Hero Card -->
      <div class="bg-white rounded-2xl overflow-hidden mb-4" style="border: 1px solid rgba(12,29,66,0.08);">
        <div class="flex flex-col sm:flex-row gap-0">
          <!-- Image panel -->
          <div
            class="sm:w-56 flex-shrink-0 flex items-center justify-center p-6"
            style="background: #F8FAFB; border-right: 1px solid rgba(12,29,66,0.06);"
          >
            <img
              v-if="product.image_url"
              :src="product.image_url"
              :alt="product.product_name"
              class="w-40 h-40 object-contain"
            />
            <div v-else class="w-40 h-40 flex items-center justify-center rounded-xl" style="background: #EFF6FF;">
              <svg class="w-16 h-16" style="color: #93C5FD;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
          </div>

          <!-- Info panel -->
          <div class="flex-1 p-6">
            <!-- Status badges -->
            <div class="flex flex-wrap gap-2 mb-3">
              <span
                class="text-xs font-medium px-2.5 py-1 rounded-full"
                :style="product.is_expired
                  ? 'background: #FEE2E2; color: #DC2626;'
                  : 'background: #DCFCE7; color: #16A34A;'"
              >
                {{ product.is_expired ? 'Hết hạn đăng ký' : 'Còn hiệu lực' }}
              </span>
              <span
                v-if="product.is_withdrawn"
                class="text-xs font-medium px-2.5 py-1 rounded-full"
                style="background: #FEF3C7; color: #D97706;"
              >
                Đã rút số đăng ký
              </span>
              <span
                v-if="product.dosage_form"
                class="text-xs font-medium px-2.5 py-1 rounded-full"
                style="background: #EFF6FF; color: #1D4FD8;"
              >
                {{ product.dosage_form }}
              </span>
            </div>

            <!-- Name -->
            <h1 class="text-2xl font-bold mb-1" style="color: #0C1D42;">{{ product.product_name }}</h1>

            <!-- Registration number -->
            <p class="text-sm font-mono mb-4" style="color: #8A95AC;">Số ĐK: {{ product.registration_number }}</p>

            <!-- Key info grid -->
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2 text-sm">
              <div v-if="product.packaging">
                <dt class="text-xs font-medium uppercase tracking-wide mb-0.5" style="color: #B5BCCB;">Đóng gói</dt>
                <dd style="color: #2A3A5E;">{{ product.packaging }}</dd>
              </div>
              <div v-if="product.route_name">
                <dt class="text-xs font-medium uppercase tracking-wide mb-0.5" style="color: #B5BCCB;">Đường dùng</dt>
                <dd style="color: #2A3A5E;">{{ product.route_name }}</dd>
              </div>
              <div v-if="product.quality_standard">
                <dt class="text-xs font-medium uppercase tracking-wide mb-0.5" style="color: #B5BCCB;">Tiêu chuẩn</dt>
                <dd style="color: #2A3A5E;">{{ product.quality_standard }}</dd>
              </div>
              <div v-if="product.shelf_life">
                <dt class="text-xs font-medium uppercase tracking-wide mb-0.5" style="color: #B5BCCB;">Tuổi thọ</dt>
                <dd style="color: #2A3A5E;">{{ product.shelf_life }}</dd>
              </div>
              <div v-if="product.registration_date">
                <dt class="text-xs font-medium uppercase tracking-wide mb-0.5" style="color: #B5BCCB;">Ngày cấp ĐK</dt>
                <dd style="color: #2A3A5E;">{{ new Date(product.registration_date).toLocaleDateString('vi-VN') }}</dd>
              </div>
              <div v-if="product.expiry_date">
                <dt class="text-xs font-medium uppercase tracking-wide mb-0.5" style="color: #B5BCCB;">Hết hạn ĐK</dt>
                <dd style="color: #2A3A5E;">{{ new Date(product.expiry_date).toLocaleDateString('vi-VN') }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <!-- Ingredients Card -->
      <div class="bg-white rounded-2xl p-6 mb-4" style="border: 1px solid rgba(12,29,66,0.08);">
        <h2 class="text-base font-semibold mb-4" style="color: #0C1D42;">Thành phần hoạt chất</h2>

        <!-- Structured ingredients with DDI mapping -->
        <ul v-if="product.ingredient_summary.length > 0" class="space-y-2">
          <li
            v-for="(ing, idx) in product.ingredient_summary"
            :key="idx"
            class="flex items-start gap-3"
          >
            <span class="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style="background: #1D4FD8;" />
            <span class="text-sm" style="color: #2A3A5E;">{{ ing }}</span>
            <span
              v-if="product.resolved_drug_ids[idx]"
              class="text-xs px-2 py-0.5 rounded-full font-mono ml-auto flex-shrink-0"
              style="background: #EFF6FF; color: #1D4FD8;"
            >
              DDI: {{ product.resolved_drug_ids[idx] }}
            </span>
          </li>
        </ul>

        <!-- Raw ingredients fallback -->
        <div v-if="product.raw_ingredients_text" class="mt-4 pt-4" style="border-top: 1px solid rgba(12,29,66,0.06);">
          <p class="text-xs font-medium uppercase tracking-wide mb-1" style="color: #B5BCCB;">Nguyên liệu thô (DAV)</p>
          <p class="text-sm" style="color: #8A95AC;">{{ product.raw_ingredients_text }}</p>
        </div>
      </div>

      <!-- DDI warning if no mapping -->
      <div
        v-if="product.resolved_drug_ids.length === 0"
        class="rounded-xl px-4 py-3 mb-4 flex items-start gap-3"
        style="background: #FFFBEB; border: 1px solid #FDE68A;"
      >
        <svg class="w-5 h-5 flex-shrink-0 mt-0.5" style="color: #D97706;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p class="text-sm" style="color: #92400E;">
          Thuốc này chưa được mapping sang cơ sở dữ liệu tương tác thuốc (DDI). Không thể kiểm tra tương tác tự động.
        </p>
      </div>

      <!-- CTA -->
      <button
        type="button"
        :disabled="product.resolved_drug_ids.length === 0"
        class="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-all"
        :class="product.resolved_drug_ids.length > 0
          ? 'text-white hover:opacity-90 active:scale-95'
          : 'cursor-not-allowed opacity-40 text-white'"
        style="background: #1D4FD8;"
        @click="goCheckInteractions"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        Kiểm tra tương tác thuốc
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </button>
    </template>
  </div>
</template>
