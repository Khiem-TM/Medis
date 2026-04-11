export interface DrugProduct {
  id: string
  drug_id: string
  trade_name: string
  route: string | null
  dosage: string | null
  formulation: string | null
  origin: string | null
}

export interface DrugWarning {
  id: string
  drug_id: string
  warning_text: string
}

export interface DrugListItem {
  id: string
  name: string
  atc_code: string | null
  description: string | null
  dosage_form: string | null
  classification: string | null
}

export interface DrugDetail extends DrugListItem {
  products: DrugProduct[]
  warnings: DrugWarning[]
}

export interface DrugSearchParams {
  page?: number
  size?: number
  search?: string
  dosage_form?: string
}

export interface CreateDrugRequest {
  id: string
  name: string
  atc_code?: string
  description?: string
  dosage_form?: string
  classification?: string
}

export interface UpdateDrugRequest {
  name?: string
  atc_code?: string
  description?: string
  dosage_form?: string
  classification?: string
}

export interface CreateDrugProductRequest {
  trade_name: string
  route?: string
  dosage?: string
  formulation?: string
  origin?: string
}
