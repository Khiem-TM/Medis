import axios from 'axios'
import type { AxiosRequestConfig } from 'axios'
import type { ApiError } from '@/types/api.types'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'
const REFRESH_TOKEN_KEY = 'medis_refresh_token'

// Simple in-memory token store to avoid circular dep with Pinia store
export const tokenManager = {
  accessToken: null as string | null,

  setAccessToken(token: string | null) {
    this.accessToken = token
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },

  setRefreshToken(token: string | null) {
    if (token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, token)
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
  },

  clear() {
    this.accessToken = null
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: string) => void
  reject: (error: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token!)
    }
  })
  failedQueue = []
}

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach access token
api.interceptors.request.use((config) => {
  if (tokenManager.accessToken) {
    config.headers.Authorization = `Bearer ${tokenManager.accessToken}`
  }
  return config
})

// Response interceptor: handle 401 + token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }
    const url = originalRequest.url ?? ''

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !url.includes('/auth/refresh') &&
      !url.includes('/auth/login')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers = {
            ...originalRequest.headers,
            Authorization: `Bearer ${token}`,
          }
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = tokenManager.getRefreshToken()
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        tokenManager.setAccessToken(data.access_token)
        tokenManager.setRefreshToken(data.refresh_token)
        processQueue(null, data.access_token)

        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${data.access_token}`,
        }
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        tokenManager.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // Normalize error
    const detail = error.response?.data?.detail
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).join(', ')
      : detail || error.response?.data?.message || error.message || 'An error occurred'

    const apiError: ApiError = {
      message,
      status: error.response?.status || 0,
      detail: error.response?.data?.detail,
    }

    return Promise.reject(apiError)
  },
)

export default api
