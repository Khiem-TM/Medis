import { z } from 'zod'

export const recommendationSchema = z.object({
  symptoms: z
    .string()
    .min(10, 'Mô tả triệu chứng ít nhất 10 ký tự')
    .max(1000, 'Mô tả triệu chứng tối đa 1000 ký tự'),
  health_profile_ids: z.array(z.string()).max(5).optional(),
  current_prescription_id: z.string().optional(),
})

export type RecommendationInput = z.infer<typeof recommendationSchema>
