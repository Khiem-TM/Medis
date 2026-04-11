export interface RecommendedDrug {
  drug_id: string
  drug_name: string
  relevance_score: number
  reason: string
  has_interaction_with_current: boolean
  interaction_details: string | null
}

export interface RecommendationResult {
  symptoms: string
  recommendations: RecommendedDrug[]
  warning: string | null
  disclaimer: string
}

export interface RecommendationRequest {
  symptoms: string
  health_profile_ids?: string[]
  current_prescription_id?: string
}
