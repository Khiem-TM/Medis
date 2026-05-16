import type { AllergyItem, KidneyFunction, LiverFunction, MedicationItem } from './onboarding.types'

export interface HealthProfile {
  id: string
  user_id: string
  diagnosis_name: string
  exam_date: string
  facility: string | null
  doctor: string | null
  symptoms: string | null
  conclusion: string | null
  notes: string | null
  prescription_id: string | null
  created_at: string
  updated_at: string
}

export interface CreateHealthProfileRequest {
  diagnosis_name: string
  exam_date: string
  facility?: string
  doctor?: string
  symptoms?: string
  conclusion?: string
  notes?: string
  prescription_id?: string
}

export interface UpdateHealthProfileRequest {
  diagnosis_name?: string
  exam_date?: string
  facility?: string
  doctor?: string
  symptoms?: string
  conclusion?: string
  notes?: string
  prescription_id?: string
}

export interface HealthProfileSearchParams {
  page?: number
  size?: number
  search?: string
  exam_date_from?: string
  exam_date_to?: string
}

export interface HealthBaselineStructured {
  id: number
  user_id: number
  height_cm: number | null
  weight_kg: number | null
  blood_type: string | null
  chronic_conditions: string[]
  allergies: AllergyItem[]
  current_medications: MedicationItem[]
  is_pregnant: boolean
  is_breastfeeding: boolean
  kidney_function: KidneyFunction
  liver_function: LiverFunction
  health_goals: string[]
  onboarding_completed: boolean
  onboarding_step: number
  created_at: string
  updated_at: string
}

export interface UpdateHealthBaselineRequest {
  height_cm?: number | null
  weight_kg?: number | null
  blood_type?: string | null
  chronic_conditions?: string[]
  allergies?: AllergyItem[]
  current_medications?: MedicationItem[]
  is_pregnant?: boolean
  is_breastfeeding?: boolean
  kidney_function?: KidneyFunction
  liver_function?: LiverFunction
  health_goals?: string[]
}

export interface HealthSummary {
  baseline: HealthBaselineStructured
  recent_visits: HealthProfile[]
  total_visits: number
  active_prescriptions: number
  active_reminders: number
  last_exam_date: string | null
}
