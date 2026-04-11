import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresAdmin?: boolean
    requiresGuest?: boolean
    layout?: 'app' | 'auth' | 'admin' | 'none'
    title?: string
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    // Public / Guest
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
      meta: { layout: 'none', title: 'Medis - Quản lý Thuốc & Sức khỏe' },
    },
    {
      path: '/design-system',
      name: 'design-system',
      component: () => import('@/views/DesignSystemView.vue'),
      meta: { layout: 'none', title: 'Design System' },
    },

    // Auth routes (guest only)
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
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/auth/ResetPasswordView.vue'),
      meta: { layout: 'auth', requiresGuest: true, title: 'Đặt lại mật khẩu' },
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: () => import('@/views/auth/VerifyEmailView.vue'),
      meta: { layout: 'auth', title: 'Xác nhận email' },
    },
    {
      path: '/auth/callback',
      name: 'oauth-callback',
      component: () => import('@/views/auth/OAuthCallbackView.vue'),
      meta: { layout: 'auth', title: 'Đang đăng nhập...' },
    },

    // Authenticated app routes
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
      meta: { layout: 'app', requiresAuth: true, title: 'Hồ sơ khám bệnh' },
    },
    {
      path: '/profile/health/:id',
      name: 'health-profile-detail',
      component: () => import('@/views/profile/HealthProfileDetailView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Chi tiết hồ sơ khám' },
    },

    // Drug routes (public, optional auth)
    {
      path: '/drugs',
      name: 'drugs',
      component: () => import('@/views/drugs/DrugSearchView.vue'),
      meta: { layout: 'app', title: 'Tra cứu thuốc' },
    },
    {
      path: '/drugs/:id',
      name: 'drug-detail',
      component: () => import('@/views/drugs/DrugDetailView.vue'),
      meta: { layout: 'app', title: 'Chi tiết thuốc' },
    },

    // Interaction checker (requires auth)
    {
      path: '/interactions',
      name: 'interactions',
      component: () => import('@/views/interactions/InteractionCheckerView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Kiểm tra tương tác thuốc' },
    },

    // Chatbot (requires auth)
    {
      path: '/chatbot',
      name: 'chatbot',
      component: () => import('@/views/chatbot/ChatbotView.vue'),
      meta: { layout: 'app', requiresAuth: true, title: 'Chatbot AI Sức khỏe' },
    },

    // Admin routes
    {
      path: '/admin',
      redirect: '/admin/users',
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/views/admin/AdminUsersView.vue'),
      meta: { layout: 'admin', requiresAdmin: true, title: 'Quản lý người dùng' },
    },
    {
      path: '/admin/users/:id',
      name: 'admin-user-detail',
      component: () => import('@/views/admin/AdminUserDetailView.vue'),
      meta: { layout: 'admin', requiresAdmin: true, title: 'Chi tiết người dùng' },
    },
    {
      path: '/admin/drugs',
      name: 'admin-drugs',
      component: () => import('@/views/admin/AdminDrugsView.vue'),
      meta: { layout: 'admin', requiresAdmin: true, title: 'Quản lý thuốc' },
    },
    {
      path: '/admin/interactions',
      name: 'admin-interactions',
      component: () => import('@/views/admin/AdminInteractionsView.vue'),
      meta: { layout: 'admin', requiresAdmin: true, title: 'Quản lý tương tác' },
    },
    {
      path: '/admin/logs',
      name: 'admin-logs',
      component: () => import('@/views/admin/AdminLogsView.vue'),
      meta: { layout: 'admin', requiresAdmin: true, title: 'Nhật ký hệ thống' },
    },

    // Error pages
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('@/views/errors/ForbiddenView.vue'),
      meta: { layout: 'none', title: 'Không có quyền truy cập' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/errors/NotFoundView.vue'),
      meta: { layout: 'none', title: 'Không tìm thấy trang' },
    },
  ],
})

let initializationPromise: Promise<void> | null = null

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  // Initialize auth state once on first navigation
  if (!authStore.initialized) {
    if (!initializationPromise) {
      initializationPromise = authStore.initialize()
    }
    await initializationPromise
  }

  // Set page title
  if (to.meta.title) {
    document.title = `${to.meta.title} | Medis`
  }

  // Admin guard (also requires auth)
  if (to.meta.requiresAdmin) {
    if (!authStore.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (!authStore.isAdmin) {
      return { name: 'forbidden' }
    }
    return true
  }

  // Auth guard
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    return true
  }

  // Guest guard: redirect authenticated users away from auth pages
  if (to.meta.requiresGuest) {
    if (authStore.isAuthenticated) {
      return { name: 'dashboard' }
    }
    return true
  }

  return true
})

export default router
