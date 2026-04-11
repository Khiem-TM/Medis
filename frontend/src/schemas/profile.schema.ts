import { z } from 'zod'
import { PASSWORD_REGEX } from './auth.schema'

export const updateProfileSchema = z.object({
  full_name: z.string().optional(),
  phone: z.string().optional(),
  date_of_birth: z.string().optional(),
  gender: z.enum(['male', 'female', 'other']).optional(),
  address: z.string().optional(),
  occupation: z.string().optional(),
})

export const changePasswordSchema = z
  .object({
    old_password: z.string().min(1, 'Mật khẩu hiện tại không được để trống'),
    new_password: z
      .string()
      .regex(PASSWORD_REGEX, 'Mật khẩu cần có chữ hoa, chữ thường, số và ký tự đặc biệt (@$!%*?&)'),
    confirm_password: z.string().min(1, 'Xác nhận mật khẩu không được để trống'),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirm_password'],
  })
  .refine((d) => d.old_password !== d.new_password, {
    message: 'Mật khẩu mới phải khác mật khẩu hiện tại',
    path: ['new_password'],
  })

export type UpdateProfileInput = z.infer<typeof updateProfileSchema>
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>
