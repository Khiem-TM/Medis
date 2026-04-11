export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  username: string
  email: string
  full_name: string | null
  phone: string | null
  date_of_birth: string | null
  gender: string | null
  address: string | null
  occupation: string | null
  avatar_url: string | null
  auth_provider: 'local' | 'google'
  google_id: string | null
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  full_name: string
  phone: string
  email: string
  username: string
  password: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export interface ResendVerificationRequest {
  email: string
}
