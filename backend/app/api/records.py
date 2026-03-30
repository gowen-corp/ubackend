from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from app.core.database import get_db
from app.services.query_core import QueryCore
from app.schemas import RecordCreate, RecordUpdate, RecordResponse, RecordListResponse

router = APIRouter()


class RecordCreate(BaseModel):
    entity_id: int
    data: Dict[str, Any] = {}
    tenant_id: Optional[int] = None


class RecordUpdate(BaseModel):
    data: Dict[str, Any]


class RecordResponse(BaseModel):
    id: int
    entity_id: int
    data: Dict[str, Any]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: str
    updated_at: Optional[str]


@router.get("/", response_model=RecordListResponse)
async def list_records(
    entity_id: int = Query(..., description="Entity ID to filter records"),
    filters: Optional[str] = Query(None, description="JSON encoded filters"),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка записей с фильтрацией
    
    Пример filters (URL encoded JSON):
    {"status": {"eq": "active"}, "price": {"gt": 100}}
    """
    import json
    
    query_core = QueryCore(db)
    
    # Парсим фильтры из JSON строки
    parsed_filters = None
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid filters JSON")
    
    result = await query_core.list_records(
        entity_id=entity_id,
        filters=parsed_filters,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/{record_id}", response_model=RecordResponse)
async def get_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """Получение записи по ID"""
    query_core = QueryCore(db)
    record = await query_core.get_record(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return record


@router.post("/", response_model=RecordResponse, status_code=201)
async def create_record(
    record: RecordCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание новой записи"""
    query_core = QueryCore(db)
    
    # Проверка существования сущности
    from sqlalchemy import select
    from app.models.tables import entities
    
    entity_check = await db.execute(
        select(entities.c.id).where(entities.c.id == record.entity_id)
    )
    if not entity_check.fetchone():
        raise HTTPException(status_code=400, detail="Entity not found")
    
    created = await query_core.create_record(
        entity_id=record.entity_id,
        data=record.data,
        tenant_id=record.tenant_id
    )
    
    return created


@router.put("/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: int,
    record: RecordUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление записи"""
    query_core = QueryCore(db)
    
    updated = await query_core.update_record(
        record_id=record_id,
        data=record.data
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return updated


@router.delete("/{record_id}", status_code=204)
async def delete_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление записи (мягкое)"""
    query_core = QueryCore(db)
    
    success = await query_core.delete_record(record_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return None
