import { z } from 'zod'

export const prescriptionItemSchema = z.object({
  drug_id: z.string().optional(),
  drug_name: z.string().min(1, 'Tên thuốc không được để trống'),
  dosage: z.string().min(1, 'Liều dùng không được để trống'),
  frequency: z.string().optional(),
  duration: z.string().optional(),
})

export const prescriptionSchema = z.object({
  name: z.string().min(1, 'Tên đơn thuốc không được để trống'),
  notes: z.string().optional(),
  status: z.enum(['active', 'completed']).default('active'),
  items: z.array(prescriptionItemSchema).min(1, 'Đơn thuốc cần ít nhất 1 thuốc'),
})

export type PrescriptionInput = z.infer<typeof prescriptionSchema>
export type PrescriptionItemInput = z.infer<typeof prescriptionItemSchema>
