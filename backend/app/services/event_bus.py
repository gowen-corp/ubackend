import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import event_outbox
from app.config import settings


class EventBus:
    """
    Event Bus с использованием Transactional Outbox pattern
    
    Гарантирует:
    - Доставка событий даже при сбоях
    - Консистентность между БД и событиями
    - Idempotency обработки
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> int:
        """
        Публикация события в outbox
        
        Вызывается ВНУТРИ той же транзакции, что и основное изменение
        """
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())
        
        query = event_outbox.insert().values(
            event_type=event_type,
            payload=payload,
            status="pending",
            idempotency_key=idempotency_key
        )
        
        result = await self.db.execute(query)
        await self.db.flush()
        
        return result.inserted_primary_key[0]
    
    async def get_pending_events(self, limit: int = 100) -> list:
        """Получение pending событий для обработки"""
        query = select(event_outbox).where(
            event_outbox.c.status == "pending",
            or_(
                event_outbox.c.next_retry_at.is_(None),
                event_outbox.c.next_retry_at <= func.now()
            )
        ).limit(limit)
        
        result = await self.db.execute(query)
        return [dict(row) for row in result.fetchall()]
    
    async def mark_processed(self, event_id: int) -> None:
        """Отметка события как обработанного"""
        query = event_outbox.update().where(
            event_outbox.c.id == event_id
        ).values(
            status="processed",
            processed_at=func.now()
        )
        await self.db.execute(query)
    
    async def mark_failed(
        self,
        event_id: int,
        retry_count: int,
        max_retries: int = 3
    ) -> None:
        """
        Отметка события как неудачного
        
        Если есть попытки — планирует повторную попытку с exponential backoff
        """
        if retry_count < max_retries:
            # Exponential backoff: 1min, 2min, 4min, 8min...
            delay_minutes = 2 ** retry_count
            next_retry = datetime.utcnow() + timedelta(minutes=delay_minutes)
            
            query = event_outbox.update().where(
                event_outbox.c.id == event_id
            ).values(
                retry_count=retry_count + 1,
                next_retry_at=next_retry
            )
        else:
            # Превышено количество попыток
            query = event_outbox.update().where(
                event_outbox.c.id == event_id
            ).values(
                status="failed"
            )
        
        await self.db.execute(query)
    
    async def get_event_by_idempotency_key(
        self,
        idempotency_key: str
    ) -> Optional[Dict]:
        """Проверка существования события по idempotency key"""
        query = select(event_outbox).where(
            event_outbox.c.idempotency_key == idempotency_key
        )
        result = await self.db.execute(query)
        row = result.fetchone()
        
        if row:
            return dict(row)
        return None
