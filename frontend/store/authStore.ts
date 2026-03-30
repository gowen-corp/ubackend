import { create } from 'zustand'
import { authApi, User } from '@/lib/api'

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  
  login: (username: string, password?: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: typeof window !== 'undefined' ? localStorage.getItem('token') : null,
  isLoading: false,
  isAuthenticated: false,
  
  login: async (username: string, password?: string) => {
    set({ isLoading: true })
    try {
      const response = await authApi.login(username, password)
      const token = response.data.access_token
      
      localStorage.setItem('token', token)
      set({ token, isAuthenticated: true })
      
      // Загружаем информацию о пользователе
      await get().checkAuth()
    } finally {
      set({ isLoading: false })
    }
  },
  
  logout: async () => {
    try {
      await authApi.logout()
    } catch (e) {
      // Игнорируем ошибки логаута
    }
    
    get().clearAuth()
  },
  
  checkAuth: async () => {
    const token = get().token
    if (!token) {
      set({ isAuthenticated: false, user: null })
      return
    }
    
    try {
      const response = await authApi.me()
      set({
        user: response.data,
        isAuthenticated: true,
      })
    } catch (e) {
      get().clearAuth()
    }
  },
  
  clearAuth: () => {
    localStorage.removeItem('token')
    set({
      token: null,
      user: null,
      isAuthenticated: false,
    })
  },
}))
