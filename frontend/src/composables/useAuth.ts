import { useAuthStore } from '@/stores/auth.store'
import { useRouter } from 'vue-router'

export function useAuth() {
  const authStore = useAuthStore()
  const router = useRouter()

  async function logout() {
    await authStore.logout()
    router.push('/login')
  }

  return {
    user: authStore.user,
    isAuthenticated: authStore.isAuthenticated,
    isAdmin: authStore.isAdmin,
    logout,
  }
}
