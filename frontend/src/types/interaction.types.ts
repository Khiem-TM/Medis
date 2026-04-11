export type Severity = 'minor' | 'moderate' | 'major'

export interface DrugInteraction {
  id: string
  drug_id_1: string
  drug_id_2: string
  drug_name_1?: string
  drug_name_2?: string
  interaction_type: string | null
  severity: Severity
  description: string | null
  recommendation: string | null
}

export interface InteractionPair {
  drug_1_id: string
  drug_1_name: string
  drug_2_id: string
  drug_2_name: string
  has_interaction: boolean
  interaction: DrugInteraction | null
}

export interface InteractionCheckResult {
  total_pairs: number
  interaction_count: number
  has_interaction: boolean
  pairs: InteractionPair[]
}

export interface InteractionCheckRequest {
  drug_ids: string[]
}

export interface CreateInteractionRequest {
  drug_id_1: string
  drug_id_2: string
  interaction_type?: string
  severity: Severity
  description?: string
  recommendation?: string
}

export interface AdminInteractionSearchParams {
  page?: number
  size?: number
  severity?: Severity | ''
  drug_id?: string
}
