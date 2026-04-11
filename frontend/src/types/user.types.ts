export interface UpdateProfileRequest {
  full_name?: string
  phone?: string
  date_of_birth?: string
  gender?: 'male' | 'female' | 'other'
  address?: string
  occupation?: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}
