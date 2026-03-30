from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime


# === Entity Schemas ===

class EntityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique entity name")
    description: Optional[str] = Field(None, max_length=500)
    schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for validation")


class EntityCreate(EntityBase):
    tenant_id: Optional[int] = None


class EntityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    schema: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EntityResponse(EntityBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tenant_id: Optional[int]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: Optional[datetime]


# === Record Schemas ===

class RecordBase(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)


class RecordCreate(RecordBase):
    entity_id: int
    tenant_id: Optional[int] = None


class RecordUpdate(BaseModel):
    data: Dict[str, Any]


class RecordResponse(RecordBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    entity_id: int
    tenant_id: Optional[int]
    created_by: Optional[int]
    updated_by: Optional[int]
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


class RecordListResponse(BaseModel):
    items: List[RecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# === Filter Schemas ===

class FilterCondition(BaseModel):
    """Условие фильтрации для Query Core"""
    field: str
    operator: str = Field(..., pattern="^(eq|ne|gt|gte|lt|lte|in|like|contains)$")
    value: Any


class RecordFilter(BaseModel):
    """Фильтр для записей"""
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort_by: Optional[str] = None
    sort_order: str = Field("asc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# === Workflow Schemas ===

class WorkflowStep(BaseModel):
    type: str = Field(..., pattern="^(http_request|send_email|delay|update_record|create_record|trigger_event)$")
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    trigger_event: str = Field(..., min_length=1)
    steps: List[WorkflowStep] = Field(default_factory=list)


class WorkflowCreate(WorkflowBase):
    tenant_id: Optional[int] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    is_active: Optional[bool] = None


class WorkflowResponse(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tenant_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


# === Event Outbox Schemas ===

class EventOutboxBase(BaseModel):
    event_type: str
    payload: Dict[str, Any]


class EventOutboxCreate(EventOutboxBase):
    idempotency_key: Optional[str] = None


class EventOutboxResponse(EventOutboxBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: str
    retry_count: int
    idempotency_key: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]


# === Health Check ===

class HealthResponse(BaseModel):
    status: str
    version: str
