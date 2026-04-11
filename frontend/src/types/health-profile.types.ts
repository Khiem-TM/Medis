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
  date_from?: string
  date_to?: string
}
