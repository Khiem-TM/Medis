import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from '@/api/axios'

export interface InteractionExplainResponse {
  drug_a_id: string
  drug_b_id: string
  drug_a_name: string
  drug_b_name: string
  severity: 'Nghiêm trọng' | 'Cần chú ý' | 'Nhẹ'
  severity_color: 'red' | 'amber' | 'yellow'
  summary: string
  mechanism: string
  symptoms_to_watch: string[]
  what_to_do: string[]
  when_to_see_doctor: string
  can_be_used_together: boolean | null
  confidence_note: string | null
  source: 'database' | 'model_predicted'
  from_cache: boolean
  disclaimer: string
}

const explainKeys = {
  pair: (id1: string, id2: string) => ['interaction-explain', id1, id2] as const,
}

export function useInteractionExplain(
  drugId1: Readonly<Ref<string | null>>,
  drugId2: Readonly<Ref<string | null>>,
  requested: Ref<boolean>,
) {
  return useQuery({
    queryKey: computed(() => explainKeys.pair(drugId1.value ?? '', drugId2.value ?? '')),
    queryFn: async () => {
      const { data } = await api.post<InteractionExplainResponse>(
        '/interactions/explain',
        { drug_id_1: drugId1.value, drug_id_2: drugId2.value },
      )
      return data
    },
    enabled: computed(() => requested.value && !!drugId1.value && !!drugId2.value),
    staleTime: 24 * 60 * 60 * 1000,
    retry: 1,
  })
}
