import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, tokenManager } from '@/api/axios'
import type { UserResponse } from '@/types/auth.types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserResponse | null>(null)
  const initialized = ref(false)

  const isAuthenticated = computed(() => !!tokenManager.accessToken)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setTokens(accessToken: string, refreshToken: string) {
    tokenManager.setAccessToken(accessToken)
    tokenManager.setRefreshToken(refreshToken)
  }

  function clearAuth() {
    tokenManager.clear()
    user.value = null
  }

  async function fetchCurrentUser() {
    const { data } = await api.get('/auth/me')
    user.value = data
    return data as UserResponse
  }

  async function initialize() {
    if (initialized.value) return
    initialized.value = true

    const refreshToken = tokenManager.getRefreshToken()
    if (!refreshToken) return

    try {
      // Try to get a new access token using the refresh token
      const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken })
      tokenManager.setAccessToken(data.access_token)
      tokenManager.setRefreshToken(data.refresh_token)
      await fetchCurrentUser()
    } catch {
      clearAuth()
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // ignore errors on logout
    } finally {
      clearAuth()
    }
  }

  return {
    user,
    initialized,
    isAuthenticated,
    isAdmin,
    setTokens,
    clearAuth,
    fetchCurrentUser,
    initialize,
    logout,
    // expose for computed access in components
    get accessToken() {
      return tokenManager.accessToken
    },
    get refreshToken() {
      return tokenManager.getRefreshToken()
    },
  }
})
