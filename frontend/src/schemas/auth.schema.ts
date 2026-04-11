import { z } from 'zod'

export const PASSWORD_REGEX = /^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[@$!%*?&]).{6,}$/
const PASSWORD_MSG = 'Mật khẩu cần có chữ hoa, chữ thường, số và ký tự đặc biệt (@$!%*?&), tối thiểu 6 ký tự'

export const loginSchema = z.object({
  username: z.string().min(1, 'Tên đăng nhập không được để trống'),
  password: z.string().min(1, 'Mật khẩu không được để trống'),
})

export const registerSchema = z
  .object({
    full_name: z.string().min(1, 'Họ tên không được để trống').trim(),
    phone: z.string().min(1, 'Số điện thoại không được để trống'),
    email: z.string().email('Email không hợp lệ'),
    username: z
      .string()
      .min(3, 'Tên đăng nhập tối thiểu 3 ký tự')
      .max(30, 'Tên đăng nhập tối đa 30 ký tự')
      .regex(/^[a-zA-Z0-9_]+$/, 'Chỉ dùng chữ cái, số và gạch dưới'),
    password: z.string().regex(PASSWORD_REGEX, PASSWORD_MSG),
    confirm_password: z.string().min(1, 'Xác nhận mật khẩu không được để trống'),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirm_password'],
  })

export const forgotPasswordSchema = z.object({
  email: z.string().email('Email không hợp lệ'),
})

export const resetPasswordSchema = z
  .object({
    new_password: z.string().regex(PASSWORD_REGEX, PASSWORD_MSG),
    confirm_new_password: z.string().min(1, 'Xác nhận mật khẩu không được để trống'),
  })
  .refine((d) => d.new_password === d.confirm_new_password, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirm_new_password'],
  })

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>
