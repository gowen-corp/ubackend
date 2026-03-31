"""
ARQ Worker Configuration

Worker для обработки фоновых задач:
- Обработка событий из event_outbox
- Отправка уведомлений
- Выполнение workflow steps
"""
from arq.worker import WorkerSettings
from arq.connections import RedisSettings
from app.config import settings
from app.workers.tasks import process_event, send_notification, execute_workflow_step, process_outbox_events


async def startup(ctx):
    from arq.connections import create_pool
    ctx["redis"] = await create_pool(RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=None
    ))


async def shutdown(ctx):
    await ctx["redis"].close()


worker_settings = WorkerSettings(
    functions=[process_event, send_notification, execute_workflow_step, process_outbox_events],
    redis_settings=RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=None
    ),
    on_startup=startup,
    on_shutdown=shutdown,
    handle_signals=True,
    cron_jobs=[
        # Обработка outbox каждую секунду
        {"coroutine": process_outbox_events, "second": "*"},
    ],
)
