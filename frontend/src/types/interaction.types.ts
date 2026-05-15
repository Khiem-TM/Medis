export type Severity = 'minor' | 'moderate' | 'major'

export type InteractionSource = 'database' | 'model_predicted'

export interface DrugEventType {
  id: number
  event_name: string
  description?: string
  source_event_id?: number
}

export interface DrugInteraction {
  drug_id: string
  interacts_with_id: string
  interacts_with_name?: string
  drug_name?: string
  event_type_id?: number
  interaction_label?: string
  source: InteractionSource
  confidence_score?: number
  event_type?: DrugEventType
}

export interface SafePair {
  drug_id_1: string
  drug_id_2: string
  drug_1_name?: string
  drug_2_name?: string
}

export interface InteractionCheckResult {
  checked_drugs: string[]
  total_pairs: number
  has_interaction: boolean
  interactions: DrugInteraction[]
  safe_pairs: SafePair[]
  prediction_count: number
  message?: string
}

export interface InteractionCheckRequest {
  drug_ids: string[]
}

export interface CreateInteractionRequest {
  drug_id: string
  interacts_with_id: string
  interacts_with_name?: string
}

export interface UpdateInteractionRequest {
  interacts_with_name?: string
}

export interface AdminInteractionSearchParams {
  page?: number
  size?: number
  drug_id?: string
}
