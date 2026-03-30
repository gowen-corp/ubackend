import structlog
from typing import Dict, Any

logger = structlog.get_logger()


async def process_event(ctx: Dict, event_type: str, payload: Dict[str, Any]) -> bool:
    """
    Обработчик событий из event_outbox
    """
    logger.info(f"Processing event: {event_type}", payload=payload)
    
    # Здесь будет логика обработки событий
    # Например, запуск workflow
    
    return True


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
