export interface PaginationMeta {
  total: number
  page: number
  size: number
  total_pages: number
}

export interface PaginatedResponse<T> {
  items: T[]
  meta: PaginationMeta
}

export interface PaginationParams {
  page?: number
  size?: number
}

export interface ApiError {
  message: string
  status: number
  detail?: string | Record<string, unknown>
}
