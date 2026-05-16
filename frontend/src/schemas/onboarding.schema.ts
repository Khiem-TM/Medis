import { z } from 'zod'

export const onboardingStep1Schema = z.object({
  height_cm: z.number().min(50, 'Chiều cao tối thiểu 50 cm').max(250, 'Chiều cao tối đa 250 cm').nullable().optional(),
  weight_kg: z.number().min(10, 'Cân nặng tối thiểu 10 kg').max(500, 'Cân nặng tối đa 500 kg').nullable().optional(),
  blood_type: z.string().nullable().optional(),
  is_pregnant: z.boolean(),
  is_breastfeeding: z.boolean(),
  kidney_function: z.enum(['normal', 'mild_impairment', 'moderate_impairment', 'severe_impairment']),
  liver_function: z.enum(['normal', 'mild_impairment', 'moderate_impairment', 'severe_impairment']),
})

export const onboardingStep2Schema = z.object({
  conditions_text: z.string().max(1000, 'Tối đa 1000 ký tự').optional(),
  allergies_text: z.string().max(1000, 'Tối đa 1000 ký tự').optional(),
})

export const onboardingStep3Schema = z.object({
  medications_text: z.string().max(1000, 'Tối đa 1000 ký tự').optional(),
  goals_text: z.string().max(500, 'Tối đa 500 ký tự').optional(),
})
