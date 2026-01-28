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

// Watch Images
export type ImageSource = 'user_upload' | 'google_images' | 'url_import'

export interface WatchImage {
  id: string
  watch_id: string
  file_path: string
  file_name: string
  file_size: number
  mime_type: string
  width: number | null
  height: number | null
  is_primary: boolean
  sort_order: number
  source: ImageSource
  created_at: string
  url: string
}

export interface WatchImageUpdate {
  is_primary?: boolean
  sort_order?: number
}

// Service History
export interface ServiceDocument {
  id: string
  service_history_id: string
  file_path: string
  file_name: string
  file_size: number
  mime_type: string
  created_at: string
  url: string
}

export interface ServiceHistory {
  id: string
  watch_id: string
  service_date: string
  provider: string
  service_type: string | null
  description: string | null
  cost: number | null
  cost_currency: string
  next_service_due: string | null
  created_at: string
  updated_at: string
  documents: ServiceDocument[]
}

export interface ServiceHistoryCreate {
  service_date: string
  provider: string
  service_type?: string
  description?: string
  cost?: number
  cost_currency?: string
  next_service_due?: string
}

export interface ServiceHistoryUpdate {
  service_date?: string
  provider?: string
  service_type?: string
  description?: string
  cost?: number
  cost_currency?: string
  next_service_due?: string
}

// Market Values
export interface MarketValue {
  id: string
  watch_id: string
  value: number
  currency: string
  source: string  // 'manual' | 'chrono24' | 'api'
  notes: string | null
  recorded_at: string
}

export interface MarketValueCreate {
  value: number
  currency?: string
  source?: string
  notes?: string
  recorded_at?: string
}

export interface MarketValueUpdate {
  value?: number
  currency?: string
  source?: string
  notes?: string
  recorded_at?: string
}

export interface WatchAnalytics {
  watch_id: string
  current_value: number | null
  current_currency: string
  purchase_price: number | null
  purchase_currency: string
  total_return: number | null
  roi_percentage: number | null
  annualized_return: number | null
  value_change_30d: number | null
  value_change_90d: number | null
  value_change_1y: number | null
  total_valuations: number
  first_valuation_date: string | null
  latest_valuation_date: string | null
}

export interface WatchPerformance {
  watch_id: string
  model: string
  brand: string
  roi: number
  current_value: number
  purchase_price: number
}

export interface CollectionAnalytics {
  total_watches: number
  total_current_value: string  // Decimal as string
  total_purchase_price: string  // Decimal as string
  currency: string
  total_return: string  // Decimal as string
  average_roi: number
  top_performers: WatchPerformance[]
  worst_performers: WatchPerformance[]
  value_by_brand: Record<string, number>
  value_by_collection: Record<string, number>
  total_valuations: number
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
  case_material: string | null
  dial_color: string | null
  strap_material: string | null
  lug_width: number | null
  water_resistance: number | null
  power_reserve: number | null
  condition: ConditionEnum | null
  current_market_value: number | null
  current_market_currency: string | null
  last_value_update: string | null
  notes: string | null
  created_at: string
  updated_at: string
  brand?: Brand
  movement_type?: MovementType
  complications?: Complication[]
  collection?: Collection
  images?: WatchImage[]
  service_history?: ServiceHistory[]
  market_values?: MarketValue[]
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
  case_material?: string | null
  dial_color?: string | null
  strap_material?: string | null
  lug_width?: number | null
  water_resistance?: number | null
  power_reserve?: number | null
  complication_ids?: string[]
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
  case_material?: string | null
  dial_color?: string | null
  strap_material?: string | null
  lug_width?: number | null
  water_resistance?: number | null
  power_reserve?: number | null
  complication_ids?: string[]
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
  primary_image: WatchImage | null
}

export interface WatchFilters {
  collection_id?: string
  brand_id?: string
  movement_type_id?: string
  condition?: ConditionEnum
  search?: string
  min_price?: number
  max_price?: number
  min_value?: number
  max_value?: number
  purchase_date_from?: string
  purchase_date_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

// Saved Searches
export interface SavedSearch {
  id: string
  user_id: string
  name: string
  filters: WatchFilters
  created_at: string
  updated_at: string
}

export interface SavedSearchCreate {
  name: string
  filters: WatchFilters
}

export interface SavedSearchUpdate {
  name?: string
  filters?: WatchFilters
}

// Comparison Context
export interface ComparisonContextType {
  selectedWatchIds: string[]
  isCompareMode: boolean
  toggleWatch: (id: string) => void
  clearSelection: () => void
  setCompareMode: (enabled: boolean) => void
  canSelectMore: boolean
}
