import { z } from 'zod'

export const healthProfileSchema = z.object({
  diagnosis_name: z.string().min(1, 'Tên chẩn đoán không được để trống'),
  exam_date: z.string().min(1, 'Ngày khám không được để trống'),
  facility: z.string().optional(),
  doctor: z.string().optional(),
  symptoms: z.string().optional(),
  conclusion: z.string().optional(),
  prescription_id: z.string().optional(),
  notes: z.string().optional(),
})

export type HealthProfileInput = z.infer<typeof healthProfileSchema>
