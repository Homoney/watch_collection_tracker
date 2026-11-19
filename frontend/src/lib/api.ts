import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { getAccessToken, setAccessToken } from './tokenStore'
import type {
  ReferencePhotoResult,
  SpecLookupResult,
  WatchBaseKeyStatus,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  Brand,
  MovementType,
  Complication,
  Collection,
  CollectionCreate,
  CollectionUpdate,
  Watch,
  WatchCreate,
  WatchUpdate,
  WatchListItem,
  WatchFilters,
  PaginatedResponse,
  WatchImage,
  WatchImageUpdate,
  ServiceHistory,
  ServiceHistoryCreate,
  ServiceHistoryUpdate,
  ServiceDocument,
  MarketValue,
  MarketValueCreate,
  MarketValueUpdate,
  WatchAnalytics,
  CollectionAnalytics,
  SavedSearch,
  SavedSearchCreate,
  SavedSearchUpdate,
  MovementAccuracyReadingCreate,
  MovementAccuracyReadingUpdate,
  MovementAccuracyReading,
  MovementAccuracyReadingWithDrift,
  AccuracyAnalytics,
  AtomicTimeResponse,
} from '@/types'

// Use relative URL so it works from any hostname/IP
const API_URL = '/api'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Single in-flight refresh shared by every request that hit a 401
let refreshPromise: Promise<string> | null = null

// Get a new access token using the HttpOnly refresh cookie.
export const refreshAccessToken = (): Promise<string> => {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<TokenResponse>(`${API_URL}/v1/auth/refresh`, null, { withCredentials: true })
      .then((response) => {
        setAccessToken(response.data.access_token)
        return response.data.access_token
      })
      .catch((err) => {
        setAccessToken(null)
        throw err
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

const NO_REFRESH_PATHS = ['/v1/auth/login', '/v1/auth/register', '/v1/auth/refresh']

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined
    const url = originalRequest?.url ?? ''

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !NO_REFRESH_PATHS.some((p) => url.endsWith(p))
    ) {
      originalRequest._retry = true
      try {
        const accessToken = await refreshAccessToken()
        originalRequest.headers.Authorization = `Bearer ${accessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Setup status: setup_required while no account exists; admin_signup when
// that first sign-up also becomes the admin
interface SetupStatus {
  setup_required: boolean
  admin_signup: boolean
}

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/v1/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/v1/auth/register', data)
    return response.data
  },

  setupStatus: async (): Promise<SetupStatus> => {
    const response = await api.get<SetupStatus>('/v1/auth/setup-status')
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/v1/auth/logout')
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/v1/auth/me')
    return response.data
  },

  updateMe: async (data: Partial<User>): Promise<User> => {
    const response = await api.put<User>('/v1/auth/me', data)
    return response.data
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.post('/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
}

// Reference Data API
export const referenceApi = {
  listBrands: async (): Promise<Brand[]> => {
    const response = await api.get<Brand[]>('/v1/reference/brands')
    return response.data
  },

  listMovementTypes: async (): Promise<MovementType[]> => {
    const response = await api.get<MovementType[]>('/v1/reference/movement-types')
    return response.data
  },

  listComplications: async (): Promise<Complication[]> => {
    const response = await api.get<Complication[]>('/v1/reference/complications')
    return response.data
  },
}

// Collections API
export const collectionsApi = {
  list: async (): Promise<Collection[]> => {
    const response = await api.get<Collection[]>('/v1/collections/')
    return response.data
  },

  create: async (data: CollectionCreate): Promise<Collection> => {
    const response = await api.post<Collection>('/v1/collections/', data)
    return response.data
  },

  get: async (id: string): Promise<Collection> => {
    const response = await api.get<Collection>(`/v1/collections/${id}`)
    return response.data
  },

  update: async (id: string, data: CollectionUpdate): Promise<Collection> => {
    const response = await api.put<Collection>(`/v1/collections/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/v1/collections/${id}`)
  },
}

// Watches API
export const watchesApi = {
  list: async (
    filters?: WatchFilters,
    limit = 20,
    offset = 0
  ): Promise<PaginatedResponse<WatchListItem>> => {
    const params = new URLSearchParams()

    if (filters?.collection_id) params.append('collection_id', filters.collection_id)
    if (filters?.brand_id) params.append('brand_id', filters.brand_id)
    if (filters?.movement_type_id) params.append('movement_type_id', filters.movement_type_id)
    if (filters?.condition) params.append('condition', filters.condition)
    if (filters?.search) params.append('search', filters.search)
    if (filters?.sort_by) params.append('sort_by', filters.sort_by)
    if (filters?.sort_order) params.append('sort_order', filters.sort_order)

    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    const response = await api.get<PaginatedResponse<WatchListItem>>(
      `/v1/watches/?${params.toString()}`
    )
    return response.data
  },

  create: async (data: WatchCreate): Promise<Watch> => {
    const response = await api.post<Watch>('/v1/watches/', data)
    return response.data
  },

  get: async (id: string): Promise<Watch> => {
    const response = await api.get<Watch>(`/v1/watches/${id}`)
    return response.data
  },

  update: async (id: string, data: WatchUpdate): Promise<Watch> => {
    const response = await api.put<Watch>(`/v1/watches/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/v1/watches/${id}`)
  },
}

// Images API
export const imagesApi = {
  upload: async (watchId: string, file: File): Promise<WatchImage> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<WatchImage>(
      `/v1/watches/${watchId}/images`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    )
    return response.data
  },

  list: async (watchId: string): Promise<WatchImage[]> => {
    const response = await api.get<WatchImage[]>(
      `/v1/watches/${watchId}/images`
    )
    return response.data
  },

  update: async (
    watchId: string,
    imageId: string,
    data: WatchImageUpdate
  ): Promise<WatchImage> => {
    const response = await api.patch<WatchImage>(
      `/v1/watches/${watchId}/images/${imageId}`,
      data
    )
    return response.data
  },

  delete: async (watchId: string, imageId: string): Promise<void> => {
    await api.delete(`/v1/watches/${watchId}/images/${imageId}`)
  },
}

// Service History API
export const serviceHistoryApi = {
  list: async (watchId: string): Promise<ServiceHistory[]> => {
    const response = await api.get<ServiceHistory[]>(
      `/v1/watches/${watchId}/service-history`
    )
    return response.data
  },

  create: async (
    watchId: string,
    data: ServiceHistoryCreate
  ): Promise<ServiceHistory> => {
    const response = await api.post<ServiceHistory>(
      `/v1/watches/${watchId}/service-history`,
      data
    )
    return response.data
  },

  get: async (watchId: string, serviceId: string): Promise<ServiceHistory> => {
    const response = await api.get<ServiceHistory>(
      `/v1/watches/${watchId}/service-history/${serviceId}`
    )
    return response.data
  },

  update: async (
    watchId: string,
    serviceId: string,
    data: ServiceHistoryUpdate
  ): Promise<ServiceHistory> => {
    const response = await api.put<ServiceHistory>(
      `/v1/watches/${watchId}/service-history/${serviceId}`,
      data
    )
    return response.data
  },

  delete: async (watchId: string, serviceId: string): Promise<void> => {
    await api.delete(`/v1/watches/${watchId}/service-history/${serviceId}`)
  },

  // Document operations
  uploadDocument: async (
    watchId: string,
    serviceId: string,
    file: File
  ): Promise<ServiceDocument> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<ServiceDocument>(
      `/v1/watches/${watchId}/service-history/${serviceId}/documents`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },

  listDocuments: async (
    watchId: string,
    serviceId: string
  ): Promise<ServiceDocument[]> => {
    const response = await api.get<ServiceDocument[]>(
      `/v1/watches/${watchId}/service-history/${serviceId}/documents`
    )
    return response.data
  },

  deleteDocument: async (
    watchId: string,
    serviceId: string,
    docId: string
  ): Promise<void> => {
    await api.delete(
      `/v1/watches/${watchId}/service-history/${serviceId}/documents/${docId}`
    )
  },
}

// Market Values API
export const marketValuesApi = {
  list: async (
    watchId: string,
    params?: { start_date?: string; end_date?: string; limit?: number }
  ): Promise<MarketValue[]> => {
    const queryParams = new URLSearchParams()
    if (params?.start_date) queryParams.append('start_date', params.start_date)
    if (params?.end_date) queryParams.append('end_date', params.end_date)
    if (params?.limit) queryParams.append('limit', params.limit.toString())

    const response = await api.get<MarketValue[]>(
      `/v1/watches/${watchId}/market-values?${queryParams.toString()}`
    )
    return response.data
  },

  create: async (
    watchId: string,
    data: MarketValueCreate
  ): Promise<MarketValue> => {
    const response = await api.post<MarketValue>(
      `/v1/watches/${watchId}/market-values`,
      data
    )
    return response.data
  },

  get: async (watchId: string, valueId: string): Promise<MarketValue> => {
    const response = await api.get<MarketValue>(
      `/v1/watches/${watchId}/market-values/${valueId}`
    )
    return response.data
  },

  update: async (
    watchId: string,
    valueId: string,
    data: MarketValueUpdate
  ): Promise<MarketValue> => {
    const response = await api.put<MarketValue>(
      `/v1/watches/${watchId}/market-values/${valueId}`,
      data
    )
    return response.data
  },

  delete: async (watchId: string, valueId: string): Promise<void> => {
    await api.delete(`/v1/watches/${watchId}/market-values/${valueId}`)
  },

  // Analytics
  getWatchAnalytics: async (watchId: string): Promise<WatchAnalytics> => {
    const response = await api.get<WatchAnalytics>(
      `/v1/watches/${watchId}/analytics`
    )
    return response.data
  },

  getCollectionAnalytics: async (currency = 'USD'): Promise<CollectionAnalytics> => {
    const response = await api.get<CollectionAnalytics>(
      `/v1/collection-analytics?currency=${currency}`
    )
    return response.data
  },
}

// Saved Searches API
export const savedSearchesApi = {
  list: async (): Promise<SavedSearch[]> => {
    const response = await api.get<SavedSearch[]>('/v1/saved-searches/')
    return response.data
  },

  create: async (data: SavedSearchCreate): Promise<SavedSearch> => {
    const response = await api.post<SavedSearch>('/v1/saved-searches/', data)
    return response.data
  },

  get: async (searchId: string): Promise<SavedSearch> => {
    const response = await api.get<SavedSearch>(`/v1/saved-searches/${searchId}`)
    return response.data
  },

  update: async (searchId: string, data: SavedSearchUpdate): Promise<SavedSearch> => {
    const response = await api.put<SavedSearch>(
      `/v1/saved-searches/${searchId}`,
      data
    )
    return response.data
  },

  delete: async (searchId: string): Promise<void> => {
    await api.delete(`/v1/saved-searches/${searchId}`)
  },
}

// User Management API (Admin only)
export const usersApi = {
  list: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/v1/users/')
    return response.data
  },

  get: async (userId: string): Promise<User> => {
    const response = await api.get<User>(`/v1/users/${userId}`)
    return response.data
  },

  updateRole: async (userId: string, role: string): Promise<User> => {
    const response = await api.patch<User>(`/v1/users/${userId}`, { role })
    return response.data
  },

  resetPassword: async (userId: string, newPassword: string): Promise<void> => {
    await api.post(`/v1/users/${userId}/reset-password`, { new_password: newPassword })
  },

  delete: async (userId: string): Promise<void> => {
    await api.delete(`/v1/users/${userId}`)
  },
}

// Movement Accuracy API
export const movementAccuracyApi = {
  getAtomicTime: async (timezone: string = 'UTC'): Promise<AtomicTimeResponse> => {
    const response = await api.get<AtomicTimeResponse>(`/v1/atomic-time?tz=${timezone}`)
    return response.data
  },

  create: async (watchId: string, data: MovementAccuracyReadingCreate): Promise<MovementAccuracyReading> => {
    const response = await api.post<MovementAccuracyReading>(`/v1/watches/${watchId}/accuracy-readings`, data)
    return response.data
  },

  list: async (watchId: string): Promise<MovementAccuracyReadingWithDrift[]> => {
    const response = await api.get<MovementAccuracyReadingWithDrift[]>(`/v1/watches/${watchId}/accuracy-readings`)
    return response.data
  },

  get: async (watchId: string, readingId: string): Promise<MovementAccuracyReadingWithDrift> => {
    const response = await api.get<MovementAccuracyReadingWithDrift>(
      `/v1/watches/${watchId}/accuracy-readings/${readingId}`
    )
    return response.data
  },

  update: async (watchId: string, readingId: string, data: MovementAccuracyReadingUpdate): Promise<MovementAccuracyReading> => {
    const response = await api.put<MovementAccuracyReading>(
      `/v1/watches/${watchId}/accuracy-readings/${readingId}`,
      data
    )
    return response.data
  },

  delete: async (watchId: string, readingId: string): Promise<void> => {
    await api.delete(`/v1/watches/${watchId}/accuracy-readings/${readingId}`)
  },

  getAnalytics: async (watchId: string): Promise<AccuracyAnalytics> => {
    const response = await api.get<AccuracyAnalytics>(`/v1/watches/${watchId}/accuracy-analytics`)
    return response.data
  },
}

// Reference look-up: fills the watch form from outside sources
export const specLookupApi = {
  lookup: async (params: {
    reference: string
    brand_id?: string
    caliber?: string
    watchbase_id?: number
  }): Promise<SpecLookupResult> => {
    const response = await api.get<SpecLookupResult>('/v1/spec-lookup', { params })
    return response.data
  },
}

// Admin settings
export const settingsApi = {
  getWatchBaseKey: async (): Promise<WatchBaseKeyStatus> => {
    const response = await api.get<WatchBaseKeyStatus>('/v1/settings/watchbase-key')
    return response.data
  },
  setWatchBaseKey: async (apiKey: string): Promise<WatchBaseKeyStatus> => {
    const response = await api.put<WatchBaseKeyStatus>('/v1/settings/watchbase-key', {
      api_key: apiKey,
    })
    return response.data
  },
  clearWatchBaseKey: async (): Promise<WatchBaseKeyStatus> => {
    const response = await api.delete<WatchBaseKeyStatus>('/v1/settings/watchbase-key')
    return response.data
  },
}

// WatchBase's photo of a watch, saved as a labelled private reference photo
export const referencePhotoApi = {
  save: async (watchId: string, watchbaseId?: number): Promise<ReferencePhotoResult> => {
    const response = await api.post<ReferencePhotoResult>(
      `/v1/watches/${watchId}/reference-photo`,
      watchbaseId ? { watchbase_id: watchbaseId } : {}
    )
    return response.data
  },
}
