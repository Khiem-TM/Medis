<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'
import { useIntersectionObserver } from '@vueuse/core'

const router = useRouter()

const features = [
  {
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', // Pill/Prescription
    title: 'Quản lý đơn thuốc',
    desc: 'Lưu trữ và theo dõi toàn bộ đơn thuốc, tự động kiểm tra tương tác khi thêm thuốc mới.'
  },
  {
    icon: 'M13 10V3L4 14h7v7l9-11h-7z', // Bolt
    title: 'Kiểm tra tương tác',
    desc: 'Kiểm tra tương tác giữa 2–20 loại thuốc chỉ trong vài giây với độ chính xác cao.'
  },
  {
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z', // Robot
    title: 'Chatbot AI',
    desc: 'Hỏi đáp sức khỏe 24/7 với AI hiểu ngữ cảnh hồ sơ bệnh của bạn.'
  },
  {
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z', // Search
    title: 'Tra cứu thuốc',
    desc: 'Tìm kiếm 5.000+ hoạt chất và hàng nghìn thuốc thương mại từ danh mục DAV.'
  },
  {
    icon: 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z', // Sparkle
    title: 'Gợi ý thuốc AI',
    desc: 'Nhập triệu chứng, nhận gợi ý thuốc phù hợp kèm điểm tương thích và cảnh báo.'
  },
  {
    icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9', // Bell
    title: 'Nhắc uống thuốc',
    desc: 'Đặt lịch nhắc thông minh, nhận thông báo real-time đúng giờ.'
  }
]

const steps = [
  {
    num: 1,
    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    title: 'Tạo tài khoản',
    desc: 'Đăng ký miễn phí, xác thực email hoặc dùng Google.'
  },
  {
    num: 2,
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    title: 'Nhập hồ sơ sức khỏe',
    desc: 'Điền bệnh nền, dị ứng, thuốc đang dùng — AI sẽ dùng để cá nhân hóa.'
  },
  {
    num: 3,
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    title: 'Bắt đầu quản lý',
    desc: 'Tạo đơn thuốc, kiểm tra tương tác, chat với AI.'
  },
  {
    num: 4,
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    title: 'Dễ dàng sử dụng',
    desc: 'Giao diện trực quan, tối ưu cho cả điện thoại và máy tính.'
  }
]

const stats = [
  { value: '5.000+', label: 'Hoạt chất thuốc' },
  { value: '10.000+', label: 'Tương tác đã ghi nhận' },
  { value: 'AI-Powered', label: 'Gợi ý thông minh' },
  { value: 'Miễn phí', label: 'Không cần thẻ tín dụng' }
]

const sectionRefs = ref<HTMLElement[]>([])
function observeSection(el: any) {
  if (el && !sectionRefs.value.includes(el)) {
    sectionRefs.value.push(el)
  }
}

const isScrolled = ref(false)
const chatStep = ref(0)

onMounted(() => {
  window.addEventListener('scroll', () => {
    isScrolled.value = window.scrollY > 20
  })

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('opacity-100', 'translate-y-0')
        entry.target.classList.remove('opacity-0', 'translate-y-8')
        if (entry.target.id === 'chatbot-section' && chatStep.value === 0) {
          setTimeout(() => chatStep.value = 1, 600) // User message
          setTimeout(() => chatStep.value = 2, 1400) // AI thinking...
          setTimeout(() => chatStep.value = 3, 2800) // AI response
        }
        observer.unobserve(entry.target)
      }
    })
  }, { threshold: 0.1 })

  // Need a small timeout to let the DOM update and refs to populate
  setTimeout(() => {
    sectionRefs.value.forEach((el) => {
      observer.observe(el)
    })
  }, 100)
})

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div class="min-h-screen bg-[#FAFAFA] font-sans selection:bg-primary/20 selection:text-primary">
    
    <!-- 1. Sticky Navbar -->
    <nav :class="[
      'fixed top-0 left-0 right-0 z-50 transition-all duration-300 w-full flex justify-center',
      isScrolled ? 'bg-white/80 backdrop-blur-md border-b border-outline-variant shadow-sm py-3' : 'bg-transparent py-5'
    ]">
      <div class="w-full max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-3 items-center">
        <!-- Logo -->
        <div class="flex items-center gap-3 cursor-pointer justify-self-start" @click="scrollToTop">
          <img src="@/assets/logo.png" alt="Medis Logo" class="w-10 h-10 object-contain rounded-xl shadow-sm" />
          <span class="text-xl font-extrabold tracking-tight text-on-surface">Medis</span>
        </div>
        
        <!-- Nav Links -->
        <div class="hidden md:flex items-center justify-center gap-8 text-sm font-semibold text-outline justify-self-center">
          <a href="#features" class="hover:text-primary transition-colors">Tính năng</a>
          <button @click="router.push('/drugs')" class="hover:text-primary transition-colors">Tra cứu thuốc</button>
          <a href="#how-it-works" class="hover:text-primary transition-colors">Giới thiệu</a>
        </div>
        
        <!-- Actions -->
        <div class="flex items-center gap-3 justify-self-end">
          <button @click="router.push('/login')" class="hidden sm:block text-sm font-semibold text-on-surface hover:text-primary transition-colors px-4 py-2">Đăng nhập</button>
          <AppButton variant="gradient" class="!rounded-full px-6 py-2.5 shadow-md hover:shadow-lg transition-all transform hover:scale-105" @click="router.push('/register')">Bắt đầu miễn phí</AppButton>
        </div>
      </div>
    </nav>

    <!-- 2. Hero Section -->
    <section class="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-6 overflow-hidden w-full flex justify-center">
      <!-- Background Mesh Gradient -->
      <div class="absolute inset-0 z-0 overflow-hidden pointer-events-none flex justify-center">
        <div class="absolute top-[-10%] right-[-10%] w-[800px] h-[800px] rounded-full bg-gradient-to-br from-[#00897B]/20 to-[#3949AB]/15 blur-3xl opacity-70" />
        <div class="absolute bottom-[-15%] left-[-10%] w-[600px] h-[600px] rounded-full bg-[#00897B]/10 blur-3xl opacity-60" />
      </div>

      <div class="w-full max-w-7xl mx-auto relative z-10 flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-8">
        <!-- Left Text -->
        <div class="w-full lg:w-[55%] flex-shrink-0 opacity-0 translate-y-8 transition-all duration-700 ease-out" :ref="observeSection">
          <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-outline-variant shadow-sm mb-6">
            <span class="relative flex h-2.5 w-2.5">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
            </span>
            <span class="text-xs font-bold text-on-surface uppercase tracking-wide">Medis AI Assistant v2.0</span>
          </div>
          <h1 class="text-5xl lg:text-[4.5rem] font-extrabold text-on-surface leading-[1.15] mb-6 tracking-tight">
            Quản lý thuốc & sức khỏe <br/>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-primary to-[#3949AB]">thông minh hơn</span> với AI
          </h1>
          <p class="text-lg text-outline mb-10 leading-relaxed max-w-xl">
            Tra cứu 5.000+ hoạt chất, kiểm tra tương tác thuốc, nhận gợi ý từ AI và theo dõi sức khỏe cá nhân — tất cả trong một nơi.
          </p>
          <div class="flex flex-wrap items-center gap-4">
            <AppButton variant="gradient" size="lg" class="!rounded-full px-8 py-4 text-base shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all" @click="router.push('/register')">
              Bắt đầu miễn phí &rarr;
            </AppButton>
            <button class="inline-flex items-center gap-2 px-6 py-4 rounded-full text-on-surface font-semibold hover:bg-surface-container-low transition-colors group">
              <span class="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center group-hover:scale-110 transition-transform">
                <svg class="w-4 h-4 text-primary ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </span>
              Xem demo
            </button>
          </div>
        </div>

        <!-- Right Visual Mockup -->
        <div class="w-full lg:w-[45%] flex justify-center lg:justify-end relative perspective-1000 opacity-0 translate-y-8 transition-all duration-700 delay-200 ease-out" :ref="observeSection">
          <div class="relative w-full max-w-[28rem] transform lg:rotate-y-[-8deg] lg:rotate-x-[4deg] transition-transform duration-700 hover:rotate-0 shadow-2xl rounded-3xl bg-white border border-white/40 overflow-hidden">
            <!-- Mockup Header -->
            <div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-error" />
              <div class="w-3 h-3 rounded-full bg-tertiary" />
              <div class="w-3 h-3 rounded-full bg-primary" />
            </div>
            <!-- Mockup Body -->
            <div class="p-6 bg-surface">
              <div class="flex items-center justify-between mb-6">
                <h3 class="font-bold text-on-surface text-lg">Kiểm tra tương tác</h3>
                <span class="bg-error-container text-error text-xs font-bold px-2 py-1 rounded-md">2 Cảnh báo</span>
              </div>
              
              <div class="space-y-4">
                <div class="p-4 rounded-2xl bg-white border border-error-container/50 shadow-sm flex gap-4 items-start relative overflow-hidden">
                  <div class="absolute left-0 top-0 bottom-0 w-1 bg-error" />
                  <div class="w-10 h-10 rounded-full bg-error-container text-error flex items-center justify-center flex-shrink-0">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  </div>
                  <div>
                    <h4 class="font-bold text-on-surface mb-1">Aspirin &times; Warfarin</h4>
                    <p class="text-xs text-outline leading-relaxed">Tăng nguy cơ chảy máu nghiêm trọng. Sự kết hợp này cần được theo dõi chặt chẽ bởi bác sĩ.</p>
                  </div>
                </div>

                <div class="p-4 rounded-2xl bg-white border border-tertiary-fixed shadow-sm flex gap-4 items-start">
                  <div class="w-10 h-10 rounded-full bg-tertiary-fixed text-tertiary flex items-center justify-center flex-shrink-0">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  </div>
                  <div>
                    <h4 class="font-bold text-on-surface mb-1">Paracetamol &times; Vitamin C</h4>
                    <p class="text-xs text-outline leading-relaxed">Không tìm thấy tương tác đáng lo ngại. An toàn khi sử dụng chung theo liều khuyến cáo.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- Decorative Blur Behind Mockup -->
          <div class="absolute inset-0 bg-primary/20 blur-[100px] -z-10 rounded-full" />
        </div>
      </div>
    </section>

    <!-- 3. Stats Bar -->
    <section class="border-y border-outline-variant bg-white py-10 opacity-0 translate-y-4 transition-all duration-700 ease-out w-full flex justify-center" :ref="observeSection">
      <div class="w-full max-w-7xl mx-auto px-6">
        <div class="grid grid-cols-2 md:grid-cols-4 divide-x divide-outline-variant/50">
          <div v-for="stat in stats" :key="stat.label" class="text-center px-4">
            <p class="text-3xl lg:text-4xl font-extrabold text-on-surface mb-2">{{ stat.value }}</p>
            <p class="text-sm font-medium text-outline uppercase tracking-wider">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. Features Grid -->
    <section id="features" class="py-24 bg-[#FAFAFA] opacity-0 translate-y-8 transition-all duration-700 ease-out w-full flex justify-center" :ref="observeSection">
      <div class="w-full max-w-7xl mx-auto px-6">
        <div class="text-center max-w-3xl mx-auto mb-16">
          <h2 class="text-4xl font-bold text-on-surface mb-4">Tất cả những gì bạn cần</h2>
          <p class="text-lg text-outline">Công cụ y tế chuyên sâu kết hợp trí tuệ nhân tạo, thiết kế riêng cho việc theo dõi và cải thiện sức khỏe.</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="feat in features" :key="feat.title" class="bg-white rounded-[1.5rem] p-8 border border-outline-variant shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group">
            <div class="w-12 h-12 rounded-2xl bg-primary-fixed text-primary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" :d="feat.icon" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-on-surface mb-3">{{ feat.title }}</h3>
            <p class="text-outline leading-relaxed">{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 5. How It Works -->
    <section id="how-it-works" class="py-32 bg-[#F0FAF9] relative opacity-0 translate-y-8 transition-all duration-700 ease-out w-full flex justify-center" :ref="observeSection">
      <div class="w-full max-w-7xl mx-auto px-6">
        <div class="text-center mb-20">
          <h2 class="text-4xl lg:text-5xl font-bold text-on-surface mb-6">Bắt đầu chỉ trong 4 bước</h2>
          <p class="text-xl text-outline">Thiết lập hồ sơ sức khỏe thông minh trong vài phút.</p>
        </div>
        
        <div class="relative max-w-6xl mx-auto">
          <!-- Connecting Line (Desktop) -->
          <div class="hidden md:block absolute top-12 left-[8%] right-[8%] h-0.5 border-t-2 border-dashed border-primary/30" />
          
          <div class="grid md:grid-cols-4 gap-8 relative z-10">
            <div v-for="(step, index) in steps" :key="step.num" 
                 class="relative text-center opacity-0 translate-y-8 transition-all duration-700"
                 :style="{ transitionDelay: `${index * 250}ms` }"
                 :ref="observeSection">
              <div class="w-24 h-24 mx-auto bg-white rounded-full flex items-center justify-center shadow-lg border border-primary/10 mb-8 relative group hover:scale-110 transition-transform cursor-default">
                <!-- Badge -->
                <div class="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-[#3949AB] text-white font-bold flex items-center justify-center border-2 border-white shadow-sm">
                  {{ step.num }}
                </div>
                <svg class="w-10 h-10 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="step.icon" />
                </svg>
              </div>
              <h3 class="text-xl font-bold text-on-surface mb-4">{{ step.title }}</h3>
              <p class="text-outline leading-relaxed max-w-xs mx-auto text-sm">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 6. Deep Dives -->
    <section class="py-32 bg-white overflow-hidden w-full flex justify-center">
      <div class="w-full max-w-7xl mx-auto px-6 space-y-48">
        <!-- Block A: Interaction -->
        <div class="grid lg:grid-cols-2 gap-16 items-center opacity-0 translate-y-8 transition-all duration-700 ease-out" :ref="observeSection">
          <div>
            <div class="inline-block px-3 py-1 rounded-full bg-error-container text-error text-sm font-bold uppercase tracking-wider mb-6">
              Tương tác thuốc
            </div>
            <h2 class="text-4xl font-bold text-on-surface leading-tight mb-6">Phát hiện tương tác nguy hiểm trước khi quá muộn</h2>
            <p class="text-lg text-outline mb-8 leading-relaxed">
              Hệ thống kiểm tra qua 3 tầng: cache tốc độ cao &rarr; cơ sở dữ liệu 10.000+ tương tác &rarr; mô hình ML dự đoán. Kết quả trả về trong dưới 1 giây.
            </p>
            <ul class="space-y-4">
              <li class="flex items-center gap-3">
                <div class="w-6 h-6 rounded-full bg-primary-fixed text-primary flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                </div>
                <span class="text-on-surface font-medium">Hỗ trợ thuốc generic & thuốc thương mại</span>
              </li>
              <li class="flex items-center gap-3">
                <div class="w-6 h-6 rounded-full bg-primary-fixed text-primary flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                </div>
                <span class="text-on-surface font-medium">Nguồn gốc rõ ràng (Database / AI predicted)</span>
              </li>
              <li class="flex items-center gap-3">
                <div class="w-6 h-6 rounded-full bg-primary-fixed text-primary flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                </div>
                <span class="text-on-surface font-medium">Hỗ trợ xuất báo cáo định dạng Excel</span>
              </li>
            </ul>
          </div>
          <div class="relative group">
            <div class="absolute inset-0 bg-error/10 blur-3xl rounded-full translate-x-10 translate-y-10 group-hover:bg-error/20 transition-colors" />
            <div class="bg-white border border-outline-variant shadow-2xl rounded-2xl p-8 relative z-10 transition-all duration-500 hover:scale-[1.03] hover:shadow-error/10">
              <div class="flex items-center justify-between mb-6 pb-6 border-b border-outline-variant">
                <div>
                  <h4 class="font-bold text-on-surface text-lg">Kết quả phân tích</h4>
                  <p class="text-sm text-outline">Tìm thấy 1 tương tác nguy hiểm</p>
                </div>
                <span class="bg-error text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-sm animate-pulse">Nguy cơ cao</span>
              </div>
              <div class="p-6 bg-error-container/30 border border-error-container rounded-xl transition-colors hover:bg-error-container/40">
                <div class="flex items-center gap-3 mb-3">
                  <span class="font-extrabold text-error text-lg">Warfarin</span>
                  <div class="w-8 h-px bg-error/30" />
                  <span class="font-extrabold text-error text-lg">Aspirin</span>
                </div>
                <p class="text-base text-on-surface-variant leading-relaxed">Tăng nguy cơ chảy máu tiêu hóa. Không nên sử dụng chung trừ khi có chỉ định đặc biệt từ bác sĩ chuyên khoa tim mạch.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Block B: AI -->
        <div id="chatbot-section" class="grid lg:grid-cols-2 gap-20 items-center opacity-0 translate-y-8 transition-all duration-700 ease-out" :ref="observeSection">
          <div class="order-2 lg:order-1 relative">
            <div class="absolute inset-0 bg-[#3949AB]/10 blur-3xl rounded-full -translate-x-10 -translate-y-10" />
            <div class="bg-surface border border-outline-variant shadow-2xl rounded-2xl overflow-hidden relative z-10 flex flex-col h-[450px] transition-transform duration-500 hover:scale-[1.02]">
              <div class="bg-white px-6 py-4 border-b border-outline-variant flex items-center gap-4 shadow-sm">
                <div class="w-12 h-12 rounded-full bg-gradient-to-br from-[#3949AB] to-primary flex items-center justify-center shadow-inner group cursor-pointer">
                  <svg class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                </div>
                <div>
                  <p class="font-bold text-base text-on-surface">Medis AI</p>
                  <p class="text-xs text-primary font-bold flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                    Đang hoạt động
                  </p>
                </div>
              </div>
              <div class="flex-1 p-8 space-y-10 overflow-y-auto bg-[#F8F9FA]">
                <!-- Bubble 1 -->
                <div v-if="chatStep >= 1" class="flex justify-end animate-in fade-in slide-in-from-right duration-500">
                  <div class="bg-primary text-white rounded-2xl rounded-tr-sm px-5 py-3 max-w-[80%] shadow-md text-base leading-relaxed">
                    <p>Tôi bị ho khan kèm sốt nhẹ, có thể uống Panadol không?</p>
                  </div>
                </div>
                <!-- Thinking Indicator -->
                <div v-if="chatStep === 2" class="flex justify-start animate-in fade-in slide-in-from-left duration-300">
                  <div class="bg-white border border-outline-variant text-on-surface rounded-2xl rounded-tl-sm px-5 py-3 shadow-sm flex items-center gap-1.5">
                    <span class="w-2 h-2 bg-outline-variant rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                    <span class="w-2 h-2 bg-outline-variant rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                    <span class="w-2 h-2 bg-outline-variant rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                  </div>
                </div>

                <!-- Bubble 2 -->
                <div v-if="chatStep >= 3" class="flex justify-start animate-in fade-in zoom-in duration-700">
                  <div class="bg-white border border-outline-variant text-on-surface rounded-2xl rounded-tl-sm px-5 py-4 max-w-[90%] shadow-md relative">
                    <div class="absolute -top-3 left-5 bg-[#F0FAF9] border border-[#00897B]/20 text-[#00897B] text-[11px] font-bold px-3 py-1 rounded-full flex items-center gap-1.5 shadow-sm">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      Cố vấn sức khỏe AI
                    </div>
                    <p class="text-base mt-1 leading-relaxed">Chào bạn, dựa trên hồ sơ bạn cung cấp, bạn đang dùng thuốc hạ áp <strong>Amlodipine</strong>. Panadol (Paracetamol) an toàn và không tương tác với Amlodipine. Bạn có thể uống 1 viên 500mg mỗi 4-6 tiếng, nhưng không quá 4 viên/ngày nhé.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="order-1 lg:order-2 lg:pl-10">
            <div class="inline-block px-4 py-1.5 rounded-full bg-[#3949AB]/10 text-[#3949AB] text-sm font-bold uppercase tracking-widest mb-8">
              AI Thông minh
            </div>
            <h2 class="text-4xl lg:text-5xl font-bold text-on-surface leading-tight mb-8 tracking-tight">Chatbot AI hiểu hồ sơ sức khỏe của bạn</h2>
            <p class="text-xl text-outline mb-10 leading-relaxed font-medium">
              Không chỉ trả lời chung chung — AI tự động phân tích bệnh nền, thuốc đang dùng và lịch sử khám bệnh của bạn để đưa ra tư vấn cá nhân hóa, an toàn và chính xác nhất.
            </p>
            <AppButton variant="outline" class="!rounded-full border-2 px-8 py-3 text-lg hover:bg-surface-container-low transition-colors" @click="router.push('/register')">Khám phá tính năng AI</AppButton>
          </div>
        </div>
      </div>
    </section>

    <!-- 8. CTA Section -->
    <section class="py-32 px-6 relative overflow-hidden opacity-0 translate-y-8 transition-all duration-700 ease-out w-full flex justify-center" :ref="observeSection">
      <!-- Gradient Background -->
      <div class="absolute inset-0 bg-gradient-to-br from-[#00897B] via-[#00796B] to-[#3949AB] opacity-95"></div>
      <!-- Decorative pattern -->
      <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(white 1px, transparent 1px); background-size: 24px 24px;"></div>
      
      <div class="relative w-full max-w-4xl mx-auto text-center z-10 py-10">
        <h2 class="text-5xl lg:text-6xl font-extrabold text-white mb-8 tracking-tight">Bắt đầu quản lý sức khỏe<br/>thông minh hơn ngay hôm nay</h2>
        <p class="text-2xl text-white/80 mb-12 font-medium">Hoàn toàn miễn phí. Không cần thẻ tín dụng.</p>
        <button
          @click="router.push('/register')"
          class="inline-flex items-center gap-3 bg-white text-[#00897B] hover:bg-surface-container-low transition-all transform hover:scale-110 text-xl px-12 py-5 font-bold rounded-full shadow-2xl"
        >
          Tạo tài khoản miễn phí &rarr;
        </button>
      </div>
    </section>

    <!-- 9. Footer -->
    <footer class="bg-[#1C1C1E] text-white pt-20 pb-10 px-6 w-full flex justify-center">
      <div class="w-full max-w-7xl mx-auto">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          <div class="md:col-span-1">
            <div class="flex items-center gap-2 mb-4">
              <img src="@/assets/logo.png" alt="Medis Logo" class="w-8 h-8 object-contain rounded-lg" />
              <span class="text-2xl font-bold tracking-tight">Medis</span>
            </div>
            <p class="text-white/60 text-sm leading-relaxed">
              Quản lý sức khỏe thông minh, sống khỏe mỗi ngày. Được xây dựng dành riêng cho người Việt.
            </p>
          </div>
          
          <div>
            <h4 class="font-bold mb-4 text-white/90">Tính năng</h4>
            <ul class="space-y-3 text-sm text-white/60">
              <li><a href="#" class="hover:text-white transition-colors">Tra cứu thuốc</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Kiểm tra tương tác</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Quản lý đơn thuốc</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Chatbot AI</a></li>
            </ul>
          </div>
          
          <div>
            <h4 class="font-bold mb-4 text-white/90">Tài khoản</h4>
            <ul class="space-y-3 text-sm text-white/60">
              <li><a href="#" @click.prevent="router.push('/login')" class="hover:text-white transition-colors">Đăng nhập</a></li>
              <li><a href="#" @click.prevent="router.push('/register')" class="hover:text-white transition-colors">Đăng ký</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Hồ sơ cá nhân</a></li>
            </ul>
          </div>

          <div>
            <h4 class="font-bold mb-4 text-white/90">Pháp lý</h4>
            <ul class="space-y-3 text-sm text-white/60">
              <li><a href="#" class="hover:text-white transition-colors">Điều khoản dịch vụ</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Chính sách bảo mật</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Tuyên bố y tế</a></li>
            </ul>
          </div>
        </div>
        
        <div class="border-t border-white/10 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-white/40">
          <p>© 2026 Medis. All rights reserved.</p>
          <p>Thiết kế với <span class="text-error">&hearts;</span> tại Việt Nam</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Perspective for 3D card effect */
.perspective-1000 {
  perspective: 1000px;
}
</style>
