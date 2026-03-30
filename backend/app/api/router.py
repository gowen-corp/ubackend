from fastapi import APIRouter
from . import health, entities, records

router = APIRouter()

# Подключаем роуты модулей
router.include_router(health.router, tags=["Health"])
router.include_router(entities.router, prefix="/entities", tags=["Entities"])
router.include_router(records.router, prefix="/records", tags=["Records"])


@router.get("/")
async def root():
    return {"message": "Welcome to uBackend API"}
