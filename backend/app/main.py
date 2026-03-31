from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import logging
from app.config import settings
from app.api.router import router as api_router
from app.core.database import init_db
from app.core.logging import setup_logging, logging_middleware, health_checker
from app.core.rate_limiter import rate_limit_middleware

# Настройка логирования
setup_logging(settings.LOG_LEVEL)

logger = structlog.get_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/openapi.json",
)

# Middleware (порядок важен!)
# CORS должен быть ПЕРВЫМ middleware!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)
app.middleware("http")(logging_middleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    Health check endpoint с метриками
    
    Returns:
        status: healthy/unhealthy
        uptime_seconds: время работы
        total_requests: всего запросов
        total_errors: всего ошибок
        error_rate: процент ошибок
    """
    return await health_checker.check()


@app.get("/ready")
async def readiness_check():
    """
    Readiness probe для Kubernetes
    
    Проверяет готовность приложения принимать запросы.
    """
    return {"status": "ready"}


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup", module="main")
    await init_db()
    logger.info("Database initialized", module="main")
    
    # Инициализация ролей по умолчанию
    from app.core.database import async_session_maker
    async with async_session_maker() as db:
        from app.services.local_auth_service import LocalAuthService
        local_auth = LocalAuthService(db)
        roles = await local_auth.get_or_create_default_roles()
        logger.info(f"Default roles initialized: {[r['name'] for r in roles]}")
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown", module="main")
