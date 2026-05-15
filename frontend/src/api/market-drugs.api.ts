import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { PaginatedResponse } from '@/types/api.types'
import type { MarketDrugProduct, MarketDrugProductDetail, MarketDrugSearchParams } from '@/types/market-drug.types'

export const marketDrugKeys = {
  all: ['market-drugs'] as const,
  list: (params: MarketDrugSearchParams) => [...marketDrugKeys.all, 'list', params] as const,
  detail: (id: number | string) => [...marketDrugKeys.all, 'detail', id] as const,
}

export interface MarketInteractionCheckResult {
  products: { product_id: number; product_name: string; ddi_drug_ids: string[] }[]
  unmapped_products: number[]
  ddi_result: import('@/types/interaction.types').InteractionCheckResult | null
}

export const marketDrugsApi = {
  search: (params: MarketDrugSearchParams) =>
    api.get<PaginatedResponse<MarketDrugProduct>>('/market-drugs', { params }).then((r) => r.data),
  get: (id: number | string) =>
    api.get<MarketDrugProductDetail>(`/market-drugs/${id}`).then((r) => r.data),
  checkInteractions: (market_product_ids: number[]) =>
    api.post<MarketInteractionCheckResult>('/market-drugs/check-interactions', { market_product_ids }).then((r) => r.data),
}

export function useMarketDrugSearch(params: Ref<MarketDrugSearchParams>) {
  return useQuery({
    queryKey: computed(() => marketDrugKeys.list(params.value)),
    queryFn: () => marketDrugsApi.search(params.value),
  })
}

export function useMarketDrugDetail(id: Ref<number | string>) {
  return useQuery({
    queryKey: computed(() => marketDrugKeys.detail(id.value)),
    queryFn: () => marketDrugsApi.get(id.value),
    enabled: computed(() => !!id.value),
  })
}
