import axios from 'axios'

/**
 * Обрабатывает ошибки API и возвращает понятное сообщение
 * 
 * @param error - Ошибка от axios или другая
 * @param defaultMessage - Сообщение по умолчанию
 * @returns Строка с описанием ошибки
 */
export function handleApiError(
  error: unknown,
  defaultMessage: string = 'Operation failed'
): string {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout. Please try again.'
    } else if (error.request) {
      return 'Network error. Please check your connection.'
    } else {
      const detail = error.response?.data?.detail
      return typeof detail === 'string' ? detail : defaultMessage
    }
  }
  
  if (error instanceof Error) {
    return error.message
  }
  
  return defaultMessage
}

/**
 * Type guard для проверки на AxiosError
 */
export function isAxiosError(error: unknown): error is { 
  code?: string
  request?: unknown
  response?: { data?: { detail?: unknown } }
} {
  return typeof error === 'object' && error !== null && 'request' in error
}
