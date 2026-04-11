<script setup lang="ts">
import { useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'

const router = useRouter()

const features = [
  {
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    title: 'Kiểm tra tương tác thuốc',
    desc: 'Phát hiện các cặp thuốc nguy hiểm khi dùng cùng nhau. Hỗ trợ đến 20 thuốc mỗi lần kiểm tra.',
  },
  {
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    title: 'Tra cứu thuốc toàn diện',
    desc: 'Hàng nghìn thuốc với thông tin chi tiết: dạng bào chế, phân loại, sản phẩm thương mại, cảnh báo an toàn.',
  },
  {
    icon: '8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
    title: 'Chatbot AI sức khỏe',
    desc: 'Đặt câu hỏi về triệu chứng, thuốc và sức khỏe. Được hỗ trợ bởi GPT-4o-mini.',
  },
  {
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    title: 'Quản lý đơn thuốc',
    desc: 'Lưu trữ và theo dõi đơn thuốc cá nhân. Kiểm tra tương tác ngay trong đơn.',
  },
  {
    icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    title: 'Hồ sơ sức khỏe cá nhân',
    desc: 'Lưu hồ sơ khám bệnh, triệu chứng và kết luận của bác sĩ theo thời gian.',
  },
  {
    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    title: 'Gợi ý thuốc AI',
    desc: 'Nhập triệu chứng, nhận gợi ý thuốc phù hợp từ AI. Chỉ mang tính tham khảo.',
  },
]

const stats = [
  { value: '10,000+', label: 'Thuốc trong danh mục' },
  { value: '50,000+', label: 'Cặp tương tác đã biết' },
  { value: 'GPT-4o', label: 'AI hỗ trợ' },
  { value: '24/7', label: 'Luôn sẵn sàng' },
]
</script>

<template>
  <div class="min-h-screen bg-white">
    <!-- Navbar -->
    <nav class="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur border-b border-[#E5E7EB]">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-[#10B981] rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <span class="text-lg font-bold text-[#111827]">Medis</span>
        </div>
        <div class="flex items-center gap-3">
          <AppButton variant="ghost" size="sm" @click="router.push('/drugs')">Tra cứu thuốc</AppButton>
          <AppButton variant="outline" size="sm" @click="router.push('/login')">Đăng nhập</AppButton>
          <AppButton size="sm" @click="router.push('/register')">Đăng ký miễn phí</AppButton>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="pt-32 pb-20 px-6 text-center bg-gradient-to-b from-[#D1FAE5]/40 to-white">
      <div class="max-w-3xl mx-auto">
        <div class="inline-flex items-center gap-2 bg-[#D1FAE5] text-[#065F46] text-xs font-medium px-3 py-1.5 rounded-full mb-6">
          <span class="w-1.5 h-1.5 bg-[#10B981] rounded-full animate-pulse" />
          Được hỗ trợ bởi GPT-4o-mini
        </div>
        <h1 class="text-5xl font-bold text-[#111827] leading-tight mb-6">
          Quản lý sức khỏe<br />
          <span class="text-[#10B981]">thông minh hơn</span>
        </h1>
        <p class="text-xl text-[#6B7280] mb-8 leading-relaxed">
          Tra cứu thuốc, kiểm tra tương tác, chatbot AI và quản lý đơn thuốc — tất cả trong một ứng dụng.
        </p>
        <div class="flex items-center justify-center gap-3">
          <AppButton @click="router.push('/register')" class="text-base px-6 py-2.5">
            Bắt đầu miễn phí
          </AppButton>
          <AppButton variant="outline" @click="router.push('/drugs')" class="text-base px-6 py-2.5">
            Tra cứu thuốc ngay
          </AppButton>
        </div>
      </div>
    </section>

    <!-- Stats -->
    <section class="py-12 border-y border-[#E5E7EB] bg-[#F9FAFB]">
      <div class="max-w-6xl mx-auto px-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div v-for="stat in stats" :key="stat.label" class="text-center">
            <p class="text-3xl font-bold text-[#10B981]">{{ stat.value }}</p>
            <p class="text-sm text-[#6B7280] mt-1">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="py-20 px-6">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-[#111827]">Tất cả những gì bạn cần</h2>
          <p class="text-[#6B7280] mt-3 text-lg">Một nền tảng toàn diện cho sức khỏe cá nhân</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="feat in features"
            :key="feat.title"
            class="bg-white border border-[#E5E7EB] rounded-2xl p-6 hover:border-[#10B981] hover:shadow-md transition-all"
          >
            <div class="w-10 h-10 bg-[#D1FAE5] rounded-xl flex items-center justify-center mb-4">
              <svg class="w-5 h-5 text-[#10B981]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="feat.icon" />
              </svg>
            </div>
            <h3 class="font-semibold text-[#111827] mb-2">{{ feat.title }}</h3>
            <p class="text-sm text-[#6B7280] leading-relaxed">{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20 px-6 bg-[#10B981]">
      <div class="max-w-2xl mx-auto text-center">
        <h2 class="text-3xl font-bold text-white mb-4">Sẵn sàng bắt đầu?</h2>
        <p class="text-[#D1FAE5] mb-8 text-lg">Đăng ký miễn phí và trải nghiệm ngay hôm nay</p>
        <AppButton
          @click="router.push('/register')"
          class="bg-white !text-[#10B981] hover:bg-[#F9FAFB] text-base px-8 py-3 font-semibold"
        >
          Tạo tài khoản miễn phí
        </AppButton>
      </div>
    </section>

    <!-- Footer -->
    <footer class="py-8 px-6 border-t border-[#E5E7EB]">
      <div class="max-w-6xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 bg-[#10B981] rounded flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <span class="font-semibold text-[#111827]">Medis</span>
        </div>
        <p class="text-sm text-[#9CA3AF]">© 2024 Medis. Chỉ mang tính tham khảo, không thay thế ý kiến bác sĩ.</p>
      </div>
    </footer>
  </div>
</template>
