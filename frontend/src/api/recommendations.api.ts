import { useMutation } from '@tanstack/vue-query'
import { api } from './axios'

export interface DrugSuggestion {
  drug_name: string
  active_ingredient: string
  indication: string
  reference_dosage: string
  suitability_score: number
  warnings: string | null
  drug_id: string | null
  has_interaction: boolean
}

export interface RecommendationResult {
  request_id: string
  symptoms: string
  suggestions: DrugSuggestion[]
  general_advice: string
  see_doctor_if: string
  generated_at: string
}

export interface RecommendationRequest {
  symptoms: string
  health_profile_ids?: number[]
  current_prescription_id?: number
}

export const recommendationApi = {
  recommend: (data: RecommendationRequest) =>
    api.post<{ success: boolean; data: RecommendationResult }>('/recommendations', data).then((r) => r.data.data),
  export: (data: RecommendationResult) =>
    api.post('/recommendations/export', data, { responseType: 'blob' }).then((r) => r.data as Blob),
}

export function useRecommendationMutation() {
  return useMutation({
    mutationFn: recommendationApi.recommend,
  })
}
