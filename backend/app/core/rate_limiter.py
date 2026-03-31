"""
Rate Limiting Middleware

Ограничение количества запросов для защиты от злоупотреблений.

Использует Redis для распределённого rate limiting.
"""
import time
from typing import Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """
    Rate limiter с использованием sliding window
    
    Для production использовать Redis backend.
    Для development - in-memory хранилище.
    """
    
    def __init__(self):
        # In-memory хранилище для development
        # Формат: {key: [(timestamp, count), ...]}
        self._store: Dict[str, list] = {}
    
    async def is_allowed(
        self,
        key: str,
        limit: int = 100,
        window_seconds: int = 60
    ) -> tuple[bool, Dict]:
        """
        Проверка ограничения
        
        Args:
            key: Уникальный ключ (например, IP или user_id)
            limit: Максимальное количество запросов в окно
            window_seconds: Размер окна в секундах
        
        Returns:
            (is_allowed, info_dict)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Получаем существующие записи
        records = self._store.get(key, [])
        
        # Удаляем старые записи за пределами окна
        records = [(ts, count) for ts, count in records if ts > window_start]
        
        # Считаем количество запросов в текущем окне
        total_requests = sum(count for _, count in records)
        
        # Информация для заголовков
        info = {
            "limit": limit,
            "remaining": max(0, limit - total_requests),
            "reset": int(window_start + window_seconds),
        }
        
        if total_requests >= limit:
            # Лимит превышен
            info["retry_after"] = int(window_start + window_seconds - now)
            self._store[key] = records
            return False, info
        
        # Добавляем текущий запрос
        records.append((now, 1))
        self._store[key] = records
        
        info["remaining"] = max(0, limit - total_requests - 1)
        
        return True, info
    
    async def cleanup(self):
        """Очистка старых записей (периодически вызывать)"""
        now = time.time()
        for key in list(self._store.keys()):
            self._store[key] = [
                (ts, count) for ts, count in self._store[key]
                if ts > now - 3600  # Храним максимум 1 час
            ]
            if not self._store[key]:
                del self._store[key]


# Глобальный rate limiter
rate_limiter = RateLimiter()


# Конфигурация rate limits
RATE_LIMITS = {
    "default": {"limit": 100, "window": 60},  # 100 запросов в минуту
    "auth": {"limit": 10, "window": 60},      # 10 попыток логина в минуту
    "api": {"limit": 1000, "window": 60},     # 1000 API запросов в минуту
}


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware для rate limiting
    
    Применяет разные лимиты к разным endpoint'ам.
    """
    # Определяем client identifier
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Создаём уникальный ключ
    client_key = f"{client_ip}:{user_agent[:32]}"
    
    # Определяем тип endpoint'а
    path = request.url.path
    
    if path.startswith("/api/v1/auth"):
        limit_config = RATE_LIMITS["auth"]
        limit_key = f"auth:{client_key}"
    elif path.startswith("/api/v1"):
        limit_config = RATE_LIMITS["api"]
        limit_key = f"api:{client_key}"
    else:
        limit_config = RATE_LIMITS["default"]
        limit_key = f"default:{client_key}"
    
    # Проверяем лимит
    is_allowed, info = await rate_limiter.is_allowed(
        limit_key,
        limit=limit_config["limit"],
        window_seconds=limit_config["window"]
    )
    
    if not is_allowed:
        logger.warning(
            "rate_limit_exceeded",
            client_ip=client_ip,
            path=path,
            limit=info["limit"],
            retry_after=info.get("retry_after"),
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too many requests",
                "retry_after": info.get("retry_after", 60),
            },
            headers={
                "Retry-After": str(info.get("retry_after", 60)),
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(info["reset"]),
            }
        )
    
    # Продолжаем обработку запроса
    response = await call_next(request)
    
    # Добавляем заголовки с информацией о лимитах
    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(info["reset"])
    
    return response


# === Periodic cleanup task ===

async def cleanup_rate_limiter():
    """
    Задача для периодической очистки rate limiter
    
    Запускать каждые 5 минут через ARQ cron job.
    """
    await rate_limiter.cleanup()
    logger.info("Rate limiter cleaned up")
