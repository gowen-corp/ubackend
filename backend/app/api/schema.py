"""
API endpoints для управления схемой сущности
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any, Dict

from app.core.database import get_db
from app.services.schema_service import EntitySchemaService, SchemaField, FieldType
from app.schemas import EntitySchemaField, EntitySchemaUpdate, FieldCreate, FieldUpdate

router = APIRouter()


@router.get("/entities/{entity_id}/schema")
async def get_entity_schema(
    entity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение схемы сущности"""
    service = EntitySchemaService(db)
    schema = await service.get_entity_schema(entity_id)
    
    if schema is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return schema


@router.get("/entities/{entity_id}/schema/fields")
async def get_entity_fields(
    entity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка полей схемы"""
    service = EntitySchemaService(db)
    fields = await service.get_schema_fields(entity_id)
    return {"fields": fields}


@router.put("/entities/{entity_id}/schema")
async def update_entity_schema(
    entity_id: int,
    schema: EntitySchemaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Полное обновление схемы сущности"""
    service = EntitySchemaService(db)
    
    try:
        updated_schema = await service.update_entity_schema(
            entity_id,
            schema.model_dump()
        )
        return updated_schema
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/entities/{entity_id}/schema/fields")
async def add_field_to_schema(
    entity_id: int,
    field: FieldCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление поля к схеме сущности"""
    service = EntitySchemaService(db)
    
    try:
        schema = await service.add_field_to_schema(
            entity_id,
            field.name,
            field.type,
            required=field.required,
            description=field.description,
            default=field.default,
            min_length=field.min_length,
            max_length=field.max_length,
            minimum=field.minimum,
            maximum=field.maximum,
            pattern=field.pattern,
            enum=field.enum,
            reference_entity_id=field.reference_entity_id,
            items_type=field.items_type
        )
        return schema
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/entities/{entity_id}/schema/fields/{field_name}")
async def update_field_in_schema(
    entity_id: int,
    field_name: str,
    field: FieldUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление поля в схеме"""
    service = EntitySchemaService(db)
    
    try:
        schema = await service.update_field_in_schema(
            entity_id,
            field_name,
            **field.model_dump(exclude_unset=True)
        )
        return schema
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/entities/{entity_id}/schema/fields/{field_name}")
async def remove_field_from_schema(
    entity_id: int,
    field_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Удаление поля из схемы"""
    service = EntitySchemaService(db)
    
    try:
        schema = await service.remove_field_from_schema(entity_id, field_name)
        return schema
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
