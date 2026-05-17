import { z } from 'zod'

export const prescriptionItemSchema = z.object({
  market_product_id: z.number().int().positive().optional(),
  drug_id: z.string().optional(),
  drug_name: z.string().optional(),
  dosage: z.string().min(1, 'Liều dùng không được để trống'),
  frequency: z.string().optional(),
  duration: z.string().optional(),
}).superRefine((value, ctx) => {
  if (!value.market_product_id && !value.drug_name?.trim()) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['drug_name'],
      message: 'Vui lòng nhập tên thuốc hoặc chọn từ danh mục',
    })
  }
})

export const prescriptionSchema = z.object({
  name: z.string().min(1, 'Tên đơn thuốc không được để trống'),
  notes: z.string().optional(),
  status: z.enum(['active', 'completed']).default('active'),
  medication_type: z.enum(['chronic', 'periodic']).default('periodic'),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  items: z.array(prescriptionItemSchema).min(1, 'Đơn thuốc cần ít nhất 1 thuốc'),
}).superRefine((data, ctx) => {
  if (data.medication_type === 'periodic' && data.start_date && data.end_date) {
    if (data.end_date < data.start_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['end_date'],
        message: 'Ngày kết thúc phải sau ngày bắt đầu',
      })
    }
  }
})

export type PrescriptionInput = z.infer<typeof prescriptionSchema>
export type PrescriptionItemInput = z.infer<typeof prescriptionItemSchema>
