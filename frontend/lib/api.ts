import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

// Создаём базовый axios инстанс
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерцептор для добавления токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// === Types ===
export interface Entity {
  id: number
  name: string
  description?: string
  schema: Record<string, any>
  is_active: boolean
  version: number
  created_at: string
  updated_at?: string
}

export interface Record {
  id: number
  entity_id: number
  data: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface RecordListResponse {
  items: Record[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface User {
  id: string
  username: string
  email?: string
  roles: string[]
  is_authenticated: boolean
}

// === Entities API ===
export const entitiesApi = {
  list: () => api.get<Entity[]>('/entities'),
  
  get: (id: number) => api.get<Entity>(`/entities/${id}`),
  
  create: (data: { name: string; description?: string; schema?: Record<string, any> }) =>
    api.post<Entity>('/entities', data),
  
  update: (id: number, data: Partial<Entity>) =>
    api.put<Entity>(`/entities/${id}`, data),
  
  delete: (id: number) => api.delete<void>(`/entities/${id}`),
}

// === Records API ===
export const recordsApi = {
  list: (
    entityId: number,
    filters?: Record<string, any>,
    page = 1,
    page_size = 20
  ) => {
    const params = new URLSearchParams({
      entity_id: entityId.toString(),
      page: page.toString(),
      page_size: page_size.toString(),
    })
    
    if (filters) {
      params.append('filters', JSON.stringify(filters))
    }
    
    return api.get<RecordListResponse>(`/records?${params}`)
  },
  
  get: (id: number) => api.get<Record>(`/records/${id}`),
  
  create: (data: { entity_id: number; data: Record<string, any> }) =>
    api.post<Record>('/records', data),
  
  update: (id: number, data: { data: Record<string, any> }) =>
    api.put<Record>(`/records/${id}`, data),
  
  delete: (id: number) => api.delete<void>(`/records/${id}`),
}

// === Auth API ===
export const authApi = {
  login: (username: string, password?: string) =>
    api.post<{ access_token: string; token_type: string }>('/auth/login', {
      username,
      password,
    }),
  
  me: () => api.get<User>('/auth/me'),
  
  logout: () => api.post('/auth/logout'),
  
  getKeycloakConfig: () =>
    api.get<{ url: string; realm: string; clientId: string; enabled: boolean }>(
      '/auth/keycloak-config'
    ),
}
