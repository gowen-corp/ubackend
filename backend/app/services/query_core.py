from typing import Dict, List, Any, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import records, entities
from app.config import settings


class FilterOperator:
    """Поддерживаемые операторы фильтрации"""
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    LIKE = "like"
    CONTAINS = "contains"


class QueryCore:
    """
    Ядро для работы с записями (JSONB storage)
    
    Реализует:
    - CRUD операции
    - Фильтрацию через JSONB
    - Сортировку
    - Пагинацию
    - RBAC фильтрацию
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_record(
        self,
        entity_id: int,
        data: Dict[str, Any],
        tenant_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict:
        """Создание записи"""
        query = records.insert().values(
            entity_id=entity_id,
            tenant_id=tenant_id,
            data=data,
            created_by=created_by
        )
        result = await self.db.execute(query)
        await self.db.flush()
        
        record_id = result.inserted_primary_key[0]
        return await self.get_record(record_id)
    
    async def get_record(self, record_id: int) -> Optional[Dict]:
        """Получение записи по ID"""
        query = select(records).where(records.c.id == record_id)
        result = await self.db.execute(query)
        row = result.fetchone()
        
        if row:
            return dict(row)
        return None
    
    async def list_records(
        self,
        entity_id: int,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 20,
        rbac_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Получение списка записей с фильтрацией, сортировкой и пагинацией
        """
        # Ограничение page_size
        page_size = min(page_size, settings.MAX_PAGE_SIZE)
        
        # Базовый запрос
        query = select(records).where(
            records.c.entity_id == entity_id,
            records.c.deleted_at.is_(None)  # Soft delete
        )
        
        # Применяем RBAC фильтр
        if rbac_filter:
            query = query.where(self._build_jsonb_filter(rbac_filter))
        
        # Применяем пользовательские фильтры
        if filters:
            query = query.where(self._build_jsonb_filter(filters))
        
        # Сортировка
        if sort_by:
            sort_column = self._get_jsonb_column(sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        
        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # Получаем общее количество записей
        count_query = select(func.count()).select_from(
            records
        ).where(
            records.c.entity_id == entity_id,
            records.c.deleted_at.is_(None)
        )
        if rbac_filter:
            count_query = count_query.where(self._build_jsonb_filter(rbac_filter))
        if filters:
            count_query = count_query.where(self._build_jsonb_filter(filters))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def update_record(
        self,
        record_id: int,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[Dict]:
        """Обновление записи"""
        update_data = {"data": data, "updated_by": updated_by}
        
        query = records.update().where(
            records.c.id == record_id
        ).values(**update_data).returning(records)
        
        result = await self.db.execute(query)
        await self.db.flush()
        
        row = result.fetchone()
        if row:
            return dict(row)
        return None
    
    async def delete_record(self, record_id: int) -> bool:
        """
        Мягкое удаление записи (soft delete)
        """
        query = records.update().where(
            records.c.id == record_id
        ).values(deleted_at=func.now())
        
        result = await self.db.execute(query)
        await self.db.flush()
        
        return result.rowcount > 0
    
    def _build_jsonb_filter(self, filters: Dict[str, Any]) -> Any:
        """
        Построение WHERE условия из JSONB фильтров
        
        Пример filters:
        {
            "status": {"eq": "active"},
            "price": {"gt": 100},
            "name": {"like": "%test%"}
        }
        """
        conditions = []
        
        for field, condition in filters.items():
            if isinstance(condition, dict):
                for operator, value in condition.items():
                    jsonb_path = records.c.data.op('->>')(field)
                    
                    if operator == FilterOperator.EQ:
                        conditions.append(jsonb_path == str(value))
                    elif operator == FilterOperator.NE:
                        conditions.append(jsonb_path != str(value))
                    elif operator == FilterOperator.GT:
                        conditions.append(jsonb_path.cast(float) > value)
                    elif operator == FilterOperator.GTE:
                        conditions.append(jsonb_path.cast(float) >= value)
                    elif operator == FilterOperator.LT:
                        conditions.append(jsonb_path.cast(float) < value)
                    elif operator == FilterOperator.LTE:
                        conditions.append(jsonb_path.cast(float) <= value)
                    elif operator == FilterOperator.IN:
                        conditions.append(jsonb_path.in_([str(v) for v in value]))
                    elif operator == FilterOperator.LIKE:
                        conditions.append(jsonb_path.like(value))
                    elif operator == FilterOperator.CONTAINS:
                        conditions.append(
                            records.c.data.op('@>')(func.jsonb_build_object(field, value))
                        )
            else:
                # Простое равенство
                jsonb_path = records.c.data.op('->>')(field)
                conditions.append(jsonb_path == str(condition))
        
        return and_(*conditions) if conditions else True
    
    def _get_jsonb_column(self, field: str):
        """Получение колонки JSONB для сортировки"""
        return records.c.data.op('->>')(field)
    
    async def get_entity_schema(self, entity_id: int) -> Optional[Dict]:
        """Получение схемы сущности"""
        query = select(entities.c.schema).where(entities.c.id == entity_id)
        result = await self.db.execute(query)
        row = result.fetchone()
        
        if row:
            return row[0]
        return None
