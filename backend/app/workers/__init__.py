from arq import WorkerSettings
from app.config import settings
from app.workers.tasks import process_event, send_notification, execute_workflow_step


class RedisSettings:
    host = settings.REDIS_HOST
    port = settings.REDIS_PORT
    password = None


async def startup(ctx):
    ctx["redis"] = None  # Будет инициализировано arq


async def shutdown(ctx):
    pass


class WorkerSettings:
    functions = [process_event, send_notification, execute_workflow_step]
    redis_settings = RedisSettings
    on_startup = startup
    on_shutdown = shutdown
    handle_signals = True
