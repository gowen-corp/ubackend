from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import logging
from app.config import settings
from app.api.router import router as api_router
from app.core.database import init_db
from app.services.local_auth_service import LocalAuthService

# Настройка логгера
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/openapi.json",
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup", module="main")
    await init_db()
    logger.info("Database initialized", module="main")
    
    # Инициализация ролей по умолчанию
    from app.core.database import async_session_maker
    async with async_session_maker() as db:
        local_auth = LocalAuthService(db)
        roles = await local_auth.get_or_create_default_roles()
        logger.info(f"Default roles initialized: {[r['name'] for r in roles]}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown", module="main")
