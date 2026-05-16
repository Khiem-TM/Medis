import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useOnboardingStore } from '@/stores/onboarding.store'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
    layout?: 'app' | 'auth' | 'none'
    title?: string
    skipOnboarding?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
      meta: { layout: 'none', title: 'Medis' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { layout: 'auth', requiresGuest: true, title: 'Đăng nhập' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { layout: 'auth', requiresGuest: true, title: 'Đăng ký' },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/auth/ForgotPasswordView.vue'),
      meta: { layout: 'auth', requiresGuest: true, title: 'Quên mật khẩu' },
    },
    {
      path: '/verify-otp',
      name: 'verify-otp',
      component: () => import('@/views/auth/OtpVerifyView.vue'),
      meta: { layout: 'auth', requiresGuest: true, title: 'Xác nhận OTP' },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/auth/ResetPasswordView.vue'),
      meta: { layout: 'auth', requiresGuest: true, title: 'Đặt lại mật khẩu' },
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: () => import('@/views/auth/VerifyEmailView.vue'),
      meta: { layout: 'auth', title: 'Xác thực email', skipOnboarding: true },
    },
    {
      path: '/auth/callback',
      name: 'oauth-callback',
      component: () => import('@/views/auth/OAuthCallbackView.vue'),
      meta: { layout: 'auth', title: 'Đang đăng nhập...', skipOnboarding: true },
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('@/views/onboarding/OnboardingView.vue'),
      meta: { layout: 'none', requiresAuth: true, title: 'Thiết lập sức khỏe', skipOnboarding: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/dashboard/DashboardView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Tổng quan' },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/profile/ProfileView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Hồ sơ cá nhân' },
    },
    {
      path: '/profile/prescriptions',
      name: 'prescriptions',
      component: () => import('@/views/profile/PrescriptionsView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Đơn thuốc' },
    },
    {
      path: '/profile/prescriptions/:id',
      name: 'prescription-detail',
      component: () => import('@/views/profile/PrescriptionDetailView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Chi tiết đơn thuốc' },
    },
    {
      path: '/profile/health',
      name: 'health-profiles',
      component: () => import('@/views/profile/HealthProfilesView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Hồ sơ sức khỏe' },
    },
    {
      path: '/profile/health/:id',
      name: 'health-profile-detail',
      component: () => import('@/views/profile/HealthProfileDetailView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Chi tiết hồ sơ' },
    },
    {
      path: '/drugs',
      name: 'drugs',
      component: () => import('@/views/drugs/DrugSearchView.vue'),
      meta: { layout: 'app', title: 'Tra cứu thuốc', skipOnboarding: true },
    },
    {
      path: '/drugs/:id',
      name: 'drug-detail',
      component: () => import('@/views/drugs/DrugDetailView.vue'),
      meta: { layout: 'app', title: 'Chi tiết thuốc', skipOnboarding: true },
    },
    {
      path: '/market-drugs/:id',
      name: 'market-drug-detail',
      component: () => import('@/views/drugs/MarketDrugDetailView.vue'),
      meta: { layout: 'app', title: 'Chi tiết thuốc thị trường', skipOnboarding: true },
    },
    {
      path: '/interactions',
      name: 'interactions',
      component: () => import('@/views/interactions/InteractionCheckerView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Kiểm tra tương tác' },
    },
    {
      path: '/chatbot',
      name: 'chatbot',
      component: () => import('@/views/chatbot/ChatbotView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Chatbot AI' },
    },
    {
      path: '/recommendations',
      name: 'recommendations',
      component: () => import('@/views/recommendations/RecommendationView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Gợi ý thuốc AI' },
    },
    {
      path: '/schedule',
      name: 'schedule',
      component: () => import('@/views/profile/ScheduleView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Lịch dùng thuốc' },
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('@/views/errors/ForbiddenView.vue'),
      meta: { layout: 'none', title: 'Không có quyền truy cập', skipOnboarding: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/errors/NotFoundView.vue'),
      meta: { layout: 'none', title: 'Không tìm thấy trang', skipOnboarding: true },
    },
  ],
})

let initializationPromise: Promise<void> | null = null

async function safeLoadOnboardingStatus() {
  const onboardingStore = useOnboardingStore()
  try {
    return await onboardingStore.loadStatus()
  } catch {
    return null
  }
}

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.initialized) {
    if (!initializationPromise) {
      initializationPromise = authStore.initialize()
    }
    await initializationPromise
  }

  if (to.meta.title) {
    document.title = `${to.meta.title} | Medis`
  }

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    const status = await safeLoadOnboardingStatus()
    if (!status) {
      return { name: 'dashboard' }
    }
    return status.onboarding_completed ? { name: 'dashboard' } : { name: 'onboarding' }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (authStore.isAuthenticated) {
    const status = await safeLoadOnboardingStatus()
    if (!status) {
      return true
    }

    if (!status.onboarding_completed && !to.meta.skipOnboarding) {
      return { name: 'onboarding' }
    }

    if (status.onboarding_completed && to.name === 'onboarding' && !to.query.update) {
      return { name: 'dashboard' }
    }
  }

  return true
})

export default router
