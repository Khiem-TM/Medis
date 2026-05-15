export interface DrugBrandName {
  id: number
  drug_id: string
  name: string
  route: string | null
  strength: string | null
  dosage_form: string | null
  country: string | null
  image_url: string | null
}

export interface DrugWarning {
  id: number
  drug_id: string
  warning_text: string
}

export interface DrugListItem {
  id: string
  generic_name: string
  description: string | null
  name?: string
  atc_code?: string | null
  dosage_form?: string | null
  classification?: string | null
}

export interface DrugDetail extends DrugListItem {
  chemical_formula: string | null
  molecular_formula: string | null
  brand_names: DrugBrandName[]
  warnings: DrugWarning[]
  dosage_forms: string[]
  categories: string[]
  atc_codes: string[]
  created_at: string
  products?: DrugBrandName[]
}

export interface DrugSearchParams {
  page?: number
  size?: number
  search?: string
}

export interface CreateDrugRequest {
  id: string
  generic_name?: string
  name?: string
  description?: string
  chemical_formula?: string
  molecular_formula?: string
  atc_code?: string
  dosage_form?: string
  classification?: string
}

export interface UpdateDrugRequest {
  generic_name?: string
  name?: string
  description?: string
  chemical_formula?: string
  molecular_formula?: string
  atc_code?: string
  dosage_form?: string
  classification?: string
}

export interface CreateDrugProductRequest {
  name: string
  route?: string
  strength?: string
  dosage_form?: string
  country?: string
  image_url?: string
}
