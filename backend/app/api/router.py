from fastapi import APIRouter
from . import health, entities, records, auth, schema

router = APIRouter()

# Подключаем роуты модулей
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(entities.router, prefix="/entities", tags=["Entities"])
router.include_router(records.router, prefix="/records", tags=["Records"])
router.include_router(schema.router, tags=["Schema"])


@router.get("/")
async def root():
    return {"message": "Welcome to uBackend API", "docs": "/api/v1/docs"}
