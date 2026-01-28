import axios, { AxiosError } from 'axios'
import type {
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
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && originalRequest) {
      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        try {
          const response = await axios.post<TokenResponse>(
            `${API_URL}/v1/auth/refresh`,
            { refresh_token: refreshToken }
          )

          const { access_token, refresh_token } = response.data

          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }

    return Promise.reject(error)
  }
)

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
      `/v1/watches/collection/analytics?currency=${currency}`
    )
    return response.data
  },
}
