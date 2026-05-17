export type IntakeStatus = 'pending' | 'taken' | 'late' | 'missed'

export interface MedicationIntakeLog {
  id: number
  user_id: number
  reminder_id: number | null
  prescription_item_id: number | null
  drug_name: string
  scheduled_date: string
  scheduled_time: string
  status: IntakeStatus
  taken_at: string | null
  notes: string | null
  created_at: string
}

export interface DayStats {
  date: string
  scheduled: number
  taken: number
  missed: number
}

export interface IntakeStatsResponse {
  period: 'week' | 'month'
  total_scheduled: number
  total_taken: number
  total_missed: number
  total_pending: number
  adherence_rate: number
  on_time_rate: number
  by_day: DayStats[]
}

export interface ConfirmIntakeRequest {
  notes?: string
}
