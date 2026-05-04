export interface MedicationReminder {
  id: number
  user_id: number
  prescription_item_id: number | null
  drug_name: string
  reminder_time: string // "HH:MM"
  frequency: string
  days_of_week: string | null
  is_active: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CreateReminderRequest {
  drug_name: string
  reminder_time: string // "HH:MM"
  frequency?: string
  days_of_week?: string
  prescription_item_id?: number
  notes?: string
}

export interface UpdateReminderRequest {
  drug_name?: string
  reminder_time?: string
  frequency?: string
  days_of_week?: string
  is_active?: boolean
  notes?: string
}
