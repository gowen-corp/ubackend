from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.core.database import get_db
from app.models.tables import entities
from app.schemas import EntityCreate, EntityUpdate, EntityResponse

router = APIRouter()


@router.get("/", response_model=List[EntityResponse])
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка сущностей"""
    query = select(entities)
    
    if is_active is not None:
        query = query.where(entities.c.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(entities.c.created_at.desc())
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: int, db: AsyncSession = Depends(get_db)):
    """Получение сущности по ID"""
    query = select(entities).where(entities.c.id == entity_id)
    result = await db.execute(query)
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return dict(row)


@router.post("/", response_model=EntityResponse, status_code=201)
async def create_entity(
    entity: EntityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание новой сущности"""
    # Проверка уникальности имени
    check_query = select(entities).where(entities.c.name == entity.name)
    check_result = await db.execute(check_query)
    if check_result.fetchone():
        raise HTTPException(status_code=400, detail="Entity with this name already exists")
    
    query = entities.insert().values(
        name=entity.name,
        description=entity.description,
        schema=entity.schema,
        tenant_id=entity.tenant_id
    )
    result = await db.execute(query)
    await db.flush()
    
    entity_id = result.inserted_primary_key[0]
    
    # Получаем созданную сущность
    get_query = select(entities).where(entities.c.id == entity_id)
    get_result = await db.execute(get_query)
    row = get_result.fetchone()
    
    return dict(row)


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: int,
    entity: EntityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление сущности"""
    # Проверка существования
    check_query = select(entities).where(entities.c.id == entity_id)
    check_result = await db.execute(check_query)
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Проверка уникальности имени при изменении
    if entity.name:
        name_check = select(entities).where(
            entities.c.name == entity.name,
            entities.c.id != entity_id
        )
        name_result = await db.execute(name_check)
        if name_result.fetchone():
            raise HTTPException(status_code=400, detail="Entity with this name already exists")
    
    # Формируем данные для обновления
    update_data = {k: v for k, v in entity.model_dump().items() if v is not None}
    
    query = entities.update().where(entities.c.id == entity_id).values(**update_data)
    await db.execute(query)
    await db.flush()
    
    # Получаем обновлённую сущность
    get_query = select(entities).where(entities.c.id == entity_id)
    get_result = await db.execute(get_query)
    row = get_result.fetchone()
    
    return dict(row)


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(entity_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление сущности (мягкое)"""
    # Проверка существования
    check_query = select(entities).where(entities.c.id == entity_id)
    check_result = await db.execute(check_query)
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Мягкое удаление
    query = entities.update().where(entities.c.id == entity_id).values(
        is_active=False,
        updated_at=func.now()
    )
    await db.execute(query)
    await db.flush()
    
    return None
