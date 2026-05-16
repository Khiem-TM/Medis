export type KidneyFunction = 'normal' | 'mild_impairment' | 'moderate_impairment' | 'severe_impairment'
export type LiverFunction = 'normal' | 'mild_impairment' | 'moderate_impairment' | 'severe_impairment'

export interface AllergyItem {
  drug: string
  reaction?: string | null
}

export interface MedicationItem {
  name: string
  dosage?: string | null
  frequency?: string | null
}

export interface HealthBaseline {
  id: number
  user_id: number
  height_cm: number | null
  weight_kg: number | null
  blood_type: string | null
  chronic_conditions: string | null
  allergies: string | null
  current_medications: string | null
  is_pregnant: boolean
  is_breastfeeding: boolean
  kidney_function: KidneyFunction
  liver_function: LiverFunction
  health_goals: string | null
  onboarding_completed: boolean
  onboarding_step: number
}

export interface OnboardingStep1Request {
  height_cm?: number | null
  weight_kg?: number | null
  blood_type?: string | null
  is_pregnant: boolean
  is_breastfeeding: boolean
  kidney_function: KidneyFunction
  liver_function: LiverFunction
}

export interface OnboardingStep2Request {
  conditions_text?: string | null
  allergies_text?: string | null
  conditions?: string[]
  allergies?: AllergyItem[]
}

export interface OnboardingStep3Request {
  medications_text?: string | null
  medications?: MedicationItem[]
  health_goals?: string[]
}

export interface ParsedConditionsResponse {
  conditions: string[]
  allergies: AllergyItem[]
  medications: MedicationItem[]
  raw_text: string
}
