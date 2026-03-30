import structlog
from typing import Dict, Any
from app.services.event_bus import EventBus
from app.services.workflow_engine import WorkflowEngine
from app.core.database import async_session_maker

logger = structlog.get_logger()


async def process_event(ctx: Dict, event_id: int) -> bool:
    """
    Обработчик событий из event_outbox
    """
    async with async_session_maker() as db:
        try:
            # Получаем событие
            from sqlalchemy import select
            from app.models.tables import event_outbox
            
            query = select(event_outbox).where(event_outbox.c.id == event_id)
            result = await db.execute(query)
            event = result.fetchone()
            
            if not event:
                logger.error(f"Event {event_id} not found")
                return False
            
            event_dict = dict(event)
            event_type = event_dict["event_type"]
            payload = event_dict["payload"]
            
            logger.info(f"Processing event: {event_type}", event_id=event_id, payload=payload)
            
            # Запускаем workflow, связанные с этим событием
            workflow_engine = WorkflowEngine(db)
            workflows = await workflow_engine.get_workflows_by_trigger(event_type)
            
            for workflow in workflows:
                await workflow_engine.start_workflow(
                    workflow_id=workflow["id"],
                    context={"event": payload}
                )
            
            # Отмечаем событие как обработанное
            event_bus = EventBus(db)
            await event_bus.mark_processed(event_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event_id}: {e}")
            # Обновляем счетчик попыток
            from sqlalchemy import update
            from app.models.tables import event_outbox
            
            await db.execute(
                update(event_outbox)
                .where(event_outbox.c.id == event_id)
                .values(retry_count=event_outbox.c.retry_count + 1)
            )
            return False


async def send_notification(ctx: Dict, user_id: int, message: str) -> bool:
    """
    Пример задачи - отправка уведомления
    """
    logger.info(f"Sending notification to user {user_id}", message=message)
    return True


async def execute_workflow_step(ctx: Dict, workflow_id: int, step_data: Dict) -> bool:
    """
    Выполнение шага workflow
    """
    logger.info(f"Executing workflow {workflow_id} step", step=step_data)
    return True


async def process_outbox_events(ctx: Dict) -> int:
    """
    Периодическая задача - обработка pending событий из outbox
    
    Запускается по расписанию (например, каждую секунду)
    """
    async with async_session_maker() as db:
        event_bus = EventBus(db)
        events = await event_bus.get_pending_events(limit=50)
        
        processed_count = 0
        for event in events:
            # Планируем обработку каждого события
            await process_event(ctx, event["id"])
            processed_count += 1
        
        return processed_count
