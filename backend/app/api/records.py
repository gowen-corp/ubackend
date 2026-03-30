from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.core.database import get_db
from app.services.query_core import QueryCore
from app.models.tables import records, entities
from sqlalchemy import select

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


@router.get("/")
async def list_records(
    entity_id: int = Query(..., description="ID сущности"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получить список записей для сущности с пагинацией"""
    query_core = QueryCore(db)
    
    result = await query_core.list_records(
        entity_id=entity_id,
        page=page,
        page_size=page_size
    )
    
    return result


@router.post("/", response_model=RecordResponse)
async def create_record(
    record: RecordCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новую запись"""
    # Проверка существования сущности
    entity_query = select(entities).where(entities.c.id == record.entity_id)
    result = await db.execute(entity_query)
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Entity not found")
    
    query_core = QueryCore(db)
    created_record = await query_core.create_record(
        entity_id=record.entity_id,
        data=record.data,
        tenant_id=record.tenant_id
    )
    
    return created_record


@router.get("/{record_id}", response_model=RecordResponse)
async def get_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """Получить запись по ID"""
    query_core = QueryCore(db)
    record = await query_core.get_record(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return record


@router.put("/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: int,
    record: RecordUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить запись"""
    query_core = QueryCore(db)
    updated_record = await query_core.update_record(
        record_id=record_id,
        data=record.data
    )
    
    if not updated_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return updated_record


@router.delete("/{record_id}")
async def delete_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить запись (soft delete)"""
    query_core = QueryCore(db)
    success = await query_core.delete_record(record_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return {"message": "Record deleted"}
