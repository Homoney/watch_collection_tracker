export interface User {
  id: string
  email: string
  full_name: string | null
  default_currency: string
  theme: string
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface ApiError {
  detail: string
}

// Reference Data
export interface Brand {
  id: string
  name: string
  sort_order: number
}

export interface MovementType {
  id: string
  name: string
  sort_order: number
}

export interface Complication {
  id: string
  name: string
  sort_order: number
}

// Collections
export interface Collection {
  id: string
  user_id: string
  name: string
  description: string | null
  color: string
  is_default: boolean
  watch_count: number
  created_at: string
  updated_at: string
}

export interface CollectionCreate {
  name: string
  description?: string | null
  color?: string
  is_default?: boolean
}

export interface CollectionUpdate {
  name?: string
  description?: string | null
  color?: string
  is_default?: boolean
}

// Watches
export type ConditionEnum = 'mint' | 'excellent' | 'good' | 'fair' | 'poor'

export interface Watch {
  id: string
  user_id: string
  brand_id: string
  model: string
  reference_number: string | null
  serial_number: string | null
  collection_id: string | null
  movement_type_id: string | null
  purchase_date: string | null
  retailer: string | null
  purchase_price: number | null
  purchase_currency: string
  case_diameter: number | null
  case_thickness: number | null
  lug_width: number | null
  water_resistance: number | null
  power_reserve: number | null
  complications: string[]
  condition: ConditionEnum | null
  current_market_value: number | null
  current_market_currency: string
  last_value_update: string | null
  notes: string | null
  created_at: string
  updated_at: string
  brand?: Brand
  movement_type?: MovementType
  collection?: Collection
}

export interface WatchCreate {
  brand_id: string
  model: string
  reference_number?: string | null
  serial_number?: string | null
  collection_id?: string | null
  movement_type_id?: string | null
  purchase_date?: string | null
  retailer?: string | null
  purchase_price?: number | null
  purchase_currency?: string
  case_diameter?: number | null
  case_thickness?: number | null
  lug_width?: number | null
  water_resistance?: number | null
  power_reserve?: number | null
  complications?: string[]
  condition?: ConditionEnum | null
  current_market_value?: number | null
  current_market_currency?: string
  last_value_update?: string | null
  notes?: string | null
}

export interface WatchUpdate {
  brand_id?: string
  model?: string
  reference_number?: string | null
  serial_number?: string | null
  collection_id?: string | null
  movement_type_id?: string | null
  purchase_date?: string | null
  retailer?: string | null
  purchase_price?: number | null
  purchase_currency?: string
  case_diameter?: number | null
  case_thickness?: number | null
  lug_width?: number | null
  water_resistance?: number | null
  power_reserve?: number | null
  complications?: string[]
  condition?: ConditionEnum | null
  current_market_value?: number | null
  current_market_currency?: string
  last_value_update?: string | null
  notes?: string | null
}

export interface WatchListItem {
  id: string
  brand_id: string
  model: string
  reference_number: string | null
  collection_id: string | null
  purchase_date: string | null
  purchase_price: number | null
  purchase_currency: string
  condition: ConditionEnum | null
  created_at: string
  brand?: Brand
  collection?: Collection
}

export interface WatchFilters {
  collection_id?: string
  brand_id?: string
  movement_type_id?: string
  condition?: ConditionEnum
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
