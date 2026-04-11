export type ActivityAction =
  | 'LOGIN'
  | 'LOGOUT'
  | 'REGISTER'
  | 'DRUG_SEARCH'
  | 'INTERACTION_CHECK'
  | 'PRESCRIPTION_CREATE'
  | 'PRESCRIPTION_UPDATE'
  | 'PRESCRIPTION_DELETE'
  | 'PRESCRIPTION_VIEW'
  | 'HEALTH_PROFILE_CREATE'
  | 'HEALTH_PROFILE_UPDATE'
  | 'HEALTH_PROFILE_DELETE'
  | 'HEALTH_PROFILE_VIEW'
  | 'CHATBOT_MESSAGE'
  | 'PROFILE_UPDATE'
  | 'PASSWORD_CHANGE'

export interface ActivityLog {
  id: string
  user_id: string | null
  action: ActivityAction
  entity_type: string | null
  entity_id: string | null
  detail: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface ActivityLogSearchParams {
  page?: number
  size?: number
  action?: ActivityAction | ''
  date_from?: string
  date_to?: string
}

export interface DeleteActivityLogsRequest {
  ids?: string[]
  delete_all?: boolean
}
