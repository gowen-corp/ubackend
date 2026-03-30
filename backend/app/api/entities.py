from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.core.database import get_db
from app.services.query_core import QueryCore
from app.models.tables import entities
from sqlalchemy import select

router = APIRouter()


class EntityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_config: Dict[str, Any] = {}
    tenant_id: Optional[int] = None


class EntityResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    model_config: Dict[str, Any]
    is_active: bool
    version: int


@router.get("/", response_model=List[EntityResponse])
async def list_entities(db: AsyncSession = Depends(get_db)):
    """Получить список всех сущностей"""
    query = select(entities).where(entities.c.is_active == True)
    result = await db.execute(query)
    rows = result.fetchall()
    return [dict(row) for row in rows]


@router.post("/", response_model=EntityResponse)
async def create_entity(entity: EntityCreate, db: AsyncSession = Depends(get_db)):
    """Создать новую сущность"""
    # Проверка уникальности имени
    check_query = select(entities).where(entities.c.name == entity.name)
    result = await db.execute(check_query)
    if result.fetchone():
        raise HTTPException(status_code=400, detail="Entity with this name already exists")
    
    # Создание сущности
    insert_query = entities.insert().values(
        name=entity.name,
        description=entity.description,
        schema=entity.model_config,
        tenant_id=entity.tenant_id
    )
    result = await db.execute(insert_query)
    await db.flush()
    
    entity_id = result.inserted_primary_key[0]
    
    # Получение созданной сущности
    get_query = select(entities).where(entities.c.id == entity_id)
    result = await db.execute(get_query)
    row = result.fetchone()
    
    return dict(row)


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: int, db: AsyncSession = Depends(get_db)):
    """Получить сущность по ID"""
    query = select(entities).where(entities.c.id == entity_id)
    result = await db.execute(query)
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return dict(row)


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: int,
    entity: EntityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить сущность"""
    # Проверка существования
    check_query = select(entities).where(entities.c.id == entity_id)
    result = await db.execute(check_query)
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Обновление
    update_query = entities.update().where(
        entities.c.id == entity_id
    ).values(
        name=entity.name,
        description=entity.description,
        schema=entity.model_config,
        tenant_id=entity.tenant_id,
        version=entities.c.version + 1
    ).returning(entities)
    
    result = await db.execute(update_query)
    row = result.fetchone()
    
    return dict(row)


@router.delete("/{entity_id}")
async def delete_entity(entity_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить сущность (soft delete)"""
    update_query = entities.update().where(
        entities.c.id == entity_id
    ).values(is_active=False)
    
    result = await db.execute(update_query)
    await db.flush()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return {"message": "Entity deleted"}
