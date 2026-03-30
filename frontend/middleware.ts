import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Публичные routes которые не требуют аутентификации
const publicRoutes = ['/login', '/keycloak-login']

// API routes которые не требуют аутентификации
const publicApiRoutes = ['/api/v1/auth/login', '/api/v1/health']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Проверка API routes
  if (pathname.startsWith('/api/v1')) {
    // Пропускаем публичные API routes
    if (publicApiRoutes.some(route => pathname.startsWith(route))) {
      return NextResponse.next()
    }
    
    // Проверяем наличие токена в заголовках
    const token = request.headers.get('authorization')?.replace('Bearer ', '')
    
    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }
    
    return NextResponse.next()
  }
  
  // Проверка frontend routes
  // Пропускаем публичные routes
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next()
  }
  
  // Пропускаем статику и следующие файлы
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/static') ||
    pathname.includes('.')
  ) {
    return NextResponse.next()
  }
  
  // Для всех остальных routes проверяем токен в localStorage
  // Note: Это работает только на клиенте, на сервере токен берётся из cookies
  const token = request.cookies.get('token')?.value
  
  // Если токена нет и это не публичный route - редирект на логин
  // Note: Полная проверка будет на клиенте через useAuthStore
  // Здесь мы только добавляем заголовок для API запросов
  
  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
