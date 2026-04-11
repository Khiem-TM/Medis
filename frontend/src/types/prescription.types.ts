export interface PrescriptionItem {
  id: string
  prescription_id: string
  drug_id: string | null
  drug_name: string
  dosage: string
  frequency: string | null
  duration: string | null
}

export interface Prescription {
  id: string
  user_id: string
  name: string
  status: 'active' | 'completed'
  notes: string | null
  items: PrescriptionItem[]
  created_at: string
  updated_at: string
}

export interface CreatePrescriptionItemRequest {
  drug_id?: string
  drug_name: string
  dosage: string
  frequency?: string
  duration?: string
}

export interface CreatePrescriptionRequest {
  name: string
  status?: 'active' | 'completed'
  notes?: string
  items: CreatePrescriptionItemRequest[]
}

export interface UpdatePrescriptionRequest {
  name?: string
  status?: 'active' | 'completed'
  notes?: string
  items?: CreatePrescriptionItemRequest[]
}

export interface PrescriptionSearchParams {
  page?: number
  size?: number
  search?: string
  status?: 'active' | 'completed' | ''
}
