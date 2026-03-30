from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import metadata

# Таблица сущностей (метаданные)
entities = Table(
    "entities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False, unique=True),
    Column("description", String(500)),
    Column("schema", JSONB, nullable=False, default=dict),
    Column("tenant_id", Integer, nullable=True),
    Column("is_active", Boolean, default=True),
    Column("version", Integer, default=1),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)

# Таблица записей (данные пользователей)
records = Table(
    "records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("tenant_id", Integer, nullable=True),
    Column("data", JSONB, nullable=False, default=dict),
    Column("created_by", Integer, nullable=True),
    Column("updated_by", Integer, nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)

# Outbox для событий (Transactional Outbox pattern)
event_outbox = Table(
    "event_outbox",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", String(255), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("status", String(50), default="pending"),  # pending, processed, failed
    Column("retry_count", Integer, default=0),
    Column("next_retry_at", DateTime(timezone=True), nullable=True),
    Column("idempotency_key", String(255), unique=True, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("processed_at", DateTime(timezone=True), nullable=True),
)

# Workflow определения
workflows = Table(
    "workflows",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("trigger_event", String(255), nullable=False),
    Column("steps", JSONB, nullable=False, default=list),
    Column("is_active", Boolean, default=True),
    Column("tenant_id", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)

# История выполнения workflow
workflow_runs = Table(
    "workflow_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("workflow_id", Integer, ForeignKey("workflows.id"), nullable=False),
    Column("status", String(50), default="running"),  # running, completed, failed
    Column("context", JSONB, nullable=False, default=dict),
    Column("current_step", Integer, default=0),
    Column("error_message", String(1000), nullable=True),
    Column("started_at", DateTime(timezone=True), server_default=func.now()),
    Column("completed_at", DateTime(timezone=True), nullable=True),
)
