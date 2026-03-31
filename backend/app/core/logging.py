"""
Logging and Monitoring Configuration

Интеграция структурированного логирования с возможностью экспорта в:
- stdout (для Docker/Kubernetes)
- Prometheus (метрики)
- OpenTelemetry (трейсинг)
"""
import logging
import sys
from typing import Any, Dict
from contextvars import ContextVar
import structlog
from fastapi import Request, Response
import time
import uuid


# Context vars для request-scoped данных
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Получение текущего request ID"""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Установка request ID для текущего контекста"""
    request_id_var.set(request_id)


# Processor для добавления request_id в логи
def add_request_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Добавляет request_id в каждое логовое сообщение"""
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """
    Настройка структурированного логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    
    structlog.configure(
        processors=[
            # Добавляем context vars
            add_request_id,
            # Добавляем имя логгера и уровень
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            # Добавляем timestamp
            timestamper,
            # Форматируем для JSON
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Настройка стандартного logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


# === Middleware для логирования запросов ===

async def logging_middleware(request: Request, call_next):
    """
    Middleware для логирования HTTP запросов
    
    - Генерирует request_id
    - Логирует метод, путь, статус, время выполнения
    """
    # Генерация request_id
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(request_id)
    
    # Получаем logger
    logger = structlog.get_logger()
    
    # Начало запроса
    start_time = time.time()
    
    # Обработка запроса
    try:
        response = await call_next(request)
        
        # Успешное выполнение
        duration = time.time() - start_time
        
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        
        # Добавляем request_id в заголовки ответа
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        # Ошибка
        duration = time.time() - start_time
        
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
        )
        raise


# === Health Check Metrics ===

class HealthChecker:
    """
    Проверка здоровья приложения с метриками
    
    Использование:
        health_checker = HealthChecker()
        
        @app.get("/health")
        async def health():
            return await health_checker.check()
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.last_check: Dict[str, Any] = {}
    
    async def check(self) -> Dict[str, Any]:
        """Проверка здоровья"""
        self.request_count += 1
        
        uptime = time.time() - self.start_time
        
        self.last_check = {
            "status": "healthy",
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": round(
                self.error_count / max(self.request_count, 1) * 100, 2
            ),
        }
        
        return self.last_check
    
    def record_error(self) -> None:
        """Запись ошибки"""
        self.error_count += 1


# Глобальный health checker
health_checker = HealthChecker()
