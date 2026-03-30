from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import workflows, workflow_runs, event_outbox
from app.services.event_bus import EventBus
import structlog

logger = structlog.get_logger()


class WorkflowEngine:
    """
    Workflow Engine для выполнения бизнес-процессов
    
    Поддерживаемые типы шагов:
    - http_request: HTTP запрос к внешнему API
    - send_email: Отправка email
    - delay: Задержка выполнения
    - update_record: Обновление записи
    - create_record: Создание записи
    - trigger_event: Генерация нового события
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_bus = EventBus(db)
    
    async def get_workflows_by_trigger(self, event_type: str) -> List[Dict]:
        """Получение всех активных workflow по типу события"""
        query = select(workflows).where(
            workflows.c.trigger_event == event_type,
            workflows.c.is_active == True
        )
        result = await self.db.execute(query)
        return [dict(row) for row in result.fetchall()]
    
    async def start_workflow(
        self,
        workflow_id: int,
        context: Dict[str, Any]
    ) -> int:
        """Запуск workflow"""
        query = workflow_runs.insert().values(
            workflow_id=workflow_id,
            status="running",
            context=context,
            current_step=0
        )
        result = await self.db.execute(query)
        await self.db.flush()
        
        run_id = result.inserted_primary_key[0]
        
        # Запускаем первый шаг
        await self._execute_step(run_id, 0)
        
        return run_id
    
    async def _execute_step(self, run_id: int, step_index: int) -> None:
        """Выполнение шага workflow"""
        # Получаем данные workflow и run
        run_query = select(workflow_runs).where(workflow_runs.c.id == run_id)
        run_result = await self.db.execute(run_query)
        run = run_result.fetchone()
        
        if not run:
            logger.error(f"Workflow run {run_id} not found")
            return
        
        run_dict = dict(run)
        
        workflow_query = select(workflows).where(
            workflows.c.id == run_dict["workflow_id"]
        )
        workflow_result = await self.db.execute(workflow_query)
        workflow = workflow_result.fetchone()
        
        if not workflow:
            logger.error(f"Workflow {run_dict['workflow_id']} not found")
            return
        
        workflow_dict = dict(workflow)
        steps = workflow_dict.get("steps", [])
        
        # Проверяем, есть ли ещё шаги
        if step_index >= len(steps):
            await self._complete_workflow(run_id)
            return
        
        step = steps[step_index]
        step_type = step.get("type")
        
        logger.info(f"Executing workflow step", run_id=run_id, step=step_index, type=step_type)
        
        try:
            # Обновляем текущий шаг
            await self.db.execute(
                workflow_runs.update().where(
                    workflow_runs.c.id == run_id
                ).values(current_step=step_index)
            )
            
            # Выполняем шаг по типу
            if step_type == "http_request":
                await self._execute_http_request(step, run_dict["context"])
            elif step_type == "send_email":
                await self._execute_send_email(step, run_dict["context"])
            elif step_type == "delay":
                await self._execute_delay(step, run_dict["context"])
            elif step_type == "update_record":
                await self._execute_update_record(step, run_dict["context"])
            elif step_type == "create_record":
                await self._execute_create_record(step, run_dict["context"])
            elif step_type == "trigger_event":
                await self._execute_trigger_event(step, run_dict["context"])
            else:
                logger.warning(f"Unknown step type: {step_type}")
            
            # Переходим к следующему шагу
            await self._execute_step(run_id, step_index + 1)
            
        except Exception as e:
            logger.error(f"Step execution failed", run_id=run_id, error=str(e))
            await self._fail_workflow(run_id, str(e))
    
    async def _execute_http_request(self, step: Dict, context: Dict) -> None:
        """Выполнение HTTP запроса"""
        # Заглушка - реальная реализация через httpx
        logger.info("HTTP request step", url=step.get("url"))
    
    async def _execute_send_email(self, step: Dict, context: Dict) -> None:
        """Отправка email"""
        # Заглушка - реальная реализация через SMTP/SNS
        logger.info("Send email step", to=step.get("to"))
    
    async def _execute_delay(self, step: Dict, context: Dict) -> None:
        """Задержка выполнения"""
        seconds = step.get("seconds", 0)
        logger.info("Delay step", seconds=seconds)
        # В реальной реализации — отложенная задача в ARQ
    
    async def _execute_update_record(self, step: Dict, context: Dict) -> None:
        """Обновление записи"""
        logger.info("Update record step", entity_id=step.get("entity_id"))
    
    async def _execute_create_record(self, step: Dict, context: Dict) -> None:
        """Создание записи"""
        logger.info("Create record step", entity_id=step.get("entity_id"))
    
    async def _execute_trigger_event(self, step: Dict, context: Dict) -> None:
        """Генерация события"""
        event_type = step.get("event_type")
        payload = step.get("payload", {})
        
        # Подставляем данные из контекста
        # Пример: {{user.id}} -> context["user"]["id"]
        payload = self._interpolate_context(payload, context)
        
        await self.event_bus.publish(
            event_type=event_type,
            payload=payload
        )
        
        logger.info("Trigger event step", event_type=event_type)
    
    def _interpolate_context(self, data: Any, context: Dict) -> Any:
        """
        Замена плейсхолдеров в данных на значения из контекста
        
        Пример: "{{user.name}}" -> context["user"]["name"]
        """
        if isinstance(data, str):
            # Простая реализация интерполяции
            if data.startswith("{{") and data.endswith("}}"):
                path = data[2:-2].strip()
                parts = path.split(".")
                value = context
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return data
                return value if value is not None else data
            return data
        elif isinstance(data, dict):
            return {k: self._interpolate_context(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._interpolate_context(item, context) for item in data]
        return data
    
    async def _complete_workflow(self, run_id: int) -> None:
        """Завершение workflow успешно"""
        await self.db.execute(
            workflow_runs.update().where(
                workflow_runs.c.id == run_id
            ).values(
                status="completed",
                completed_at=func.now()
            )
        )
        logger.info("Workflow completed", run_id=run_id)
    
    async def _fail_workflow(self, run_id: int, error: str) -> None:
        """Завершение workflow с ошибкой"""
        await self.db.execute(
            workflow_runs.update().where(
                workflow_runs.c.id == run_id
            ).values(
                status="failed",
                error_message=error,
                completed_at=func.now()
            )
        )
        logger.error("Workflow failed", run_id=run_id, error=error)
