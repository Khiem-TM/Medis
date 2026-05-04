<script setup lang="ts">
import { useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'

const router = useRouter()

const features = [
  {
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    title: 'Kiểm tra tương tác thuốc',
    desc: 'Phát hiện các cặp thuốc nguy hiểm khi dùng cùng nhau. Hỗ trợ đến 20 thuốc mỗi lần kiểm tra.',
    color: 'bg-error-container',
    textColor: 'text-error',
  },
  {
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    title: 'Tra cứu thuốc toàn diện',
    desc: 'Hàng nghìn thuốc với thông tin chi tiết: dạng bào chế, phân loại, sản phẩm thương mại, cảnh báo an toàn.',
    color: 'bg-primary-fixed',
    textColor: 'text-primary',
  },
  {
    icon: '8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
    title: 'Chatbot AI sức khỏe',
    desc: 'Đặt câu hỏi về triệu chứng, thuốc và sức khỏe. Được hỗ trợ bởi GPT-4o-mini, kết nối hồ sơ cá nhân.',
    color: 'bg-secondary-container',
    textColor: 'text-secondary',
  },
  {
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    title: 'Quản lý đơn thuốc',
    desc: 'Lưu trữ và theo dõi đơn thuốc cá nhân. Kiểm tra tương tác ngay trong đơn.',
    color: 'bg-primary-fixed',
    textColor: 'text-primary',
  },
  {
    icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    title: 'Hồ sơ sức khỏe cá nhân',
    desc: 'Lưu hồ sơ khám bệnh, triệu chứng và kết luận của bác sĩ theo thời gian.',
    color: 'bg-error-container',
    textColor: 'text-error',
  },
  {
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    title: 'Gợi ý thuốc từ AI',
    desc: 'Nhập triệu chứng, nhận gợi ý thuốc phù hợp từ AI. Chỉ mang tính tham khảo.',
    color: 'bg-tertiary-fixed',
    textColor: 'text-tertiary',
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
  <div class="min-h-screen bg-surface">
    <!-- Navbar -->
    <nav class="fixed top-0 left-0 right-0 z-50 bg-card/90 backdrop-blur-xl border-b border-outline-variant">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span class="text-lg font-bold text-on-surface">Medis</span>
        </div>
        <div class="hidden md:flex items-center gap-6 text-sm text-outline">
          <button @click="router.push('/drugs')" class="hover:text-on-surface transition-colors">Tra cứu thuốc</button>
          <button @click="router.push('/interactions')" class="hover:text-on-surface transition-colors">Tương tác</button>
        </div>
        <div class="flex items-center gap-2">
          <AppButton variant="ghost" size="sm" @click="router.push('/login')">Đăng nhập</AppButton>
          <AppButton variant="gradient" size="sm" @click="router.push('/register')">Đăng ký miễn phí</AppButton>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="pt-32 pb-20 px-6 relative overflow-hidden">
      <!-- Background gradient -->
      <div class="absolute inset-0 bg-gradient-to-br from-primary to-primary-container opacity-95" />
      <!-- Blurred circles -->
      <div class="absolute top-10 right-1/4 w-96 h-96 rounded-full bg-white/10 blur-3xl" />
      <div class="absolute bottom-0 left-1/4 w-64 h-64 rounded-full bg-white/10 blur-2xl" />

      <div class="relative max-w-6xl mx-auto">
        <div class="max-w-3xl">
          <div class="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm border border-white/30 text-white text-xs font-medium px-3 py-1.5 rounded-full mb-6">
            <span class="w-1.5 h-1.5 bg-tertiary-fixed rounded-full animate-pulse" />
            Được hỗ trợ bởi GPT-4o-mini
          </div>
          <h1 class="text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6">
            Quản lý sức khỏe<br />
            <span class="text-primary-fixed-dim">thông minh hơn</span>
          </h1>
          <p class="text-xl text-white/80 mb-8 leading-relaxed max-w-2xl">
            Tra cứu thuốc, kiểm tra tương tác, chatbot AI và quản lý đơn thuốc — tất cả trong một ứng dụng.
          </p>
          <div class="flex flex-wrap items-center gap-3">
            <AppButton variant="gradient" size="lg" @click="router.push('/register')"
              class="!bg-white !text-primary hover:!opacity-90 !font-semibold">
              Bắt đầu miễn phí
            </AppButton>
            <button @click="router.push('/drugs')"
              class="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-white/40 text-white text-base font-medium hover:bg-white/10 transition-colors">
              Tra cứu thuốc ngay
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Floating interaction card -->
        <div class="absolute right-0 top-1/2 -translate-y-1/2 hidden xl:block w-72">
          <div class="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-5">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <span class="text-sm font-semibold text-white">Kiểm tra tương tác</span>
            </div>
            <div class="space-y-2">
              <div class="flex items-center justify-between bg-white/10 rounded-lg px-3 py-2">
                <span class="text-xs text-white/90">Aspirin + Warfarin</span>
                <span class="text-xs font-bold text-red-300">⚠️ Nguy hiểm</span>
              </div>
              <div class="flex items-center justify-between bg-white/10 rounded-lg px-3 py-2">
                <span class="text-xs text-white/90">Metformin + Insulin</span>
                <span class="text-xs font-bold text-yellow-300">⚡ Thận trọng</span>
              </div>
              <div class="flex items-center justify-between bg-white/10 rounded-lg px-3 py-2">
                <span class="text-xs text-white/90">Paracetamol</span>
                <span class="text-xs font-bold text-green-300">✓ An toàn</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats -->
    <section class="py-12 border-y border-outline-variant bg-card">
      <div class="max-w-6xl mx-auto px-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div v-for="stat in stats" :key="stat.label" class="text-center">
            <p class="text-3xl font-bold text-primary">{{ stat.value }}</p>
            <p class="text-sm text-outline mt-1">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="py-20 px-6">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-on-surface">Tất cả những gì bạn cần</h2>
          <p class="text-outline mt-3 text-lg">Một nền tảng toàn diện cho sức khỏe cá nhân</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="feat in features"
            :key="feat.title"
            class="bg-card border border-outline-variant rounded-2xl p-6 hover:border-primary hover:shadow-md transition-all group"
          >
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center mb-4', feat.color]">
              <svg :class="['w-5 h-5', feat.textColor]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="feat.icon" />
              </svg>
            </div>
            <h3 class="font-semibold text-on-surface mb-2 group-hover:text-primary transition-colors">{{ feat.title }}</h3>
            <p class="text-sm text-outline leading-relaxed">{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20 px-6 bg-gradient-to-r from-primary to-primary-container">
      <div class="max-w-2xl mx-auto text-center">
        <h2 class="text-3xl font-bold text-white mb-4">Sẵn sàng bắt đầu?</h2>
        <p class="text-primary-fixed mb-8 text-lg">Đăng ký miễn phí và trải nghiệm ngay hôm nay</p>
        <button
          @click="router.push('/register')"
          class="inline-flex items-center gap-2 bg-white text-primary hover:bg-primary-fixed transition-colors text-base px-8 py-3 font-semibold rounded-xl"
        >
          Tạo tài khoản miễn phí
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="py-8 px-6 border-t border-outline-variant bg-card">
      <div class="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 bg-primary rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span class="font-bold text-on-surface">Medis</span>
        </div>
        <p class="text-sm text-outline text-center">© 2026 Medis. Chỉ mang tính tham khảo, không thay thế ý kiến bác sĩ.</p>
        <div class="flex items-center gap-4 text-xs text-outline">
          <a href="#" class="hover:text-primary transition-colors">Chính sách bảo mật</a>
          <a href="#" class="hover:text-primary transition-colors">Điều khoản</a>
          <a href="#" class="hover:text-primary transition-colors">Liên hệ</a>
        </div>
      </div>
    </footer>
  </div>
</template>
