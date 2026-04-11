import type { UserResponse } from './auth.types'

export interface AdminUserStats {
  prescription_count: number
  health_profile_count: number
  activity_log_count: number
}

export interface AdminUserDetail extends UserResponse {
  stats: AdminUserStats
}

export interface UpdateAdminUserRequest {
  full_name?: string
  phone?: string
  role?: 'user' | 'admin'
  is_active?: boolean
}

export interface AdminUserSearchParams {
  page?: number
  size?: number
  search?: string
  role?: 'user' | 'admin' | ''
  is_active?: boolean | ''
}

export interface AdminStats {
  total_users: number
  active_users: number
  new_users_today: number
  total_drugs: number
  total_interactions: number
  total_prescriptions: number
  total_health_profiles: number
  total_chat_messages: number
}

export type SystemLogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

export interface SystemLog {
  id: string
  level: SystemLogLevel
  source: string | null
  message: string
  detail: Record<string, unknown> | null
  created_at: string
}

export interface SystemLogSearchParams {
  page?: number
  size?: number
  level?: SystemLogLevel | ''
}

export interface AdminActivityLogSearchParams {
  page?: number
  size?: number
  user_id?: string
  action?: string
  date_from?: string
  date_to?: string
}
