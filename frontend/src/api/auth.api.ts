import { useMutation } from '@tanstack/vue-query'
import { api } from './axios'
import type { TokenResponse, UserResponse, LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest } from '@/types/auth.types'

// Raw API functions
export const authApi = {
  login: (data: LoginRequest) => api.post<TokenResponse>('/auth/login', data).then((r) => r.data),
  register: (data: RegisterRequest) => api.post('/auth/register', data).then((r) => r.data),
  logout: () => api.post('/auth/logout').then((r) => r.data),
  refresh: (refresh_token: string) => api.post<TokenResponse>('/auth/refresh', { refresh_token }).then((r) => r.data),
  forgotPassword: (data: ForgotPasswordRequest) => api.post('/auth/forgot-password', data).then((r) => r.data),
  resetPassword: (data: { token: string; new_password: string }) => api.post('/auth/reset-password', data).then((r) => r.data),
  verifyEmail: (token: string) => api.get(`/auth/verify-email?token=${token}`).then((r) => r.data),
  resendVerification: (email: string) => api.post('/auth/resend-verification', { email }).then((r) => r.data),
  me: () => api.get<UserResponse>('/auth/me').then((r) => r.data),
  forgotPasswordOtp: (data: { email: string }) => api.post('/auth/forgot-password/otp', data).then((r) => r.data),
  verifyResetOtp: (data: { email: string; otp: string }) => api.post<{ reset_token: string }>('/auth/verify-reset-otp', data).then((r) => r.data),
}

// Vue Query mutations
export function useLoginMutation() {
  return useMutation({ mutationFn: authApi.login })
}

export function useRegisterMutation() {
  return useMutation({ mutationFn: authApi.register })
}

export function useLogoutMutation() {
  return useMutation({ mutationFn: authApi.logout })
}

export function useForgotPasswordMutation() {
  return useMutation({ mutationFn: authApi.forgotPassword })
}

export function useResetPasswordMutation() {
  return useMutation({ mutationFn: authApi.resetPassword })
}

export function useResendVerificationMutation() {
  return useMutation({ mutationFn: authApi.resendVerification })
}

export function useForgotPasswordOtpMutation() {
  return useMutation({ mutationFn: authApi.forgotPasswordOtp })
}

export function useVerifyResetOtpMutation() {
  return useMutation({ mutationFn: authApi.verifyResetOtp })
}
