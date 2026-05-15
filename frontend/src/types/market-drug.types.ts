export interface MarketDrugProduct {
  id: number
  registration_number: string
  product_name: string
  normalized_product_name?: string | null
  dosage_form?: string | null
  packaging?: string | null
  route_name?: string | null
  is_expired: boolean
  is_withdrawn: boolean
  image_url?: string | null
  ingredient_summary: string[]
  resolved_drug_ids: string[]
}

export interface MarketDrugProductDetail extends MarketDrugProduct {
  source_product_id?: number | null
  old_registration_number?: string | null
  quality_standard?: string | null
  shelf_life?: string | null
  decision_number?: string | null
  issue_batch?: string | null
  registration_date?: string | null
  expiry_date?: string | null
  raw_ingredients_text?: string | null
  created_at: string
  updated_at: string
}

export interface MarketDrugSearchParams {
  page?: number
  size?: number
  search?: string
}
