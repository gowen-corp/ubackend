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


# === Auth Schemas ===

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    email: Optional[str] = Field(None, description="Email")
    full_name: Optional[str] = Field(None, description="Full name")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    is_authenticated: bool = True


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_system: bool
    created_at: datetime


class UserRoleAssign(BaseModel):
    role_id: int
    expires_at: Optional[datetime] = None


class EntityPermissionAssign(BaseModel):
    role_id: int
    can_read: bool = True
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False
    row_filter: Optional[Dict[str, Any]] = None


# === Schema Builder Schemas ===

class EntitySchemaField(BaseModel):
    name: str
    type: str = Field(..., pattern="^(string|number|integer|boolean|date|datetime|json|reference|array|email|text)$")
    required: bool = False
    description: Optional[str] = None
    default: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    pattern: Optional[str] = None
    enum: Optional[List[Any]] = None
    reference_entity_id: Optional[int] = None
    items_type: Optional[str] = None


class FieldCreate(EntitySchemaField):
    pass


class FieldUpdate(BaseModel):
    type: Optional[str] = None
    required: Optional[bool] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    pattern: Optional[str] = None
    enum: Optional[List[Any]] = None
    reference_entity_id: Optional[int] = None
    items_type: Optional[str] = None


class EntitySchemaUpdate(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


# === Workflow Schemas ===

class WorkflowStepConfig(BaseModel):
    """Конфигурация шага workflow"""
    # Для http_request
    url: Optional[str] = None
    method: Optional[str] = "POST"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    
    # Для send_email
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    
    # Для delay
    seconds: Optional[int] = None
    
    # Для update_record/create_record
    entity_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    
    # Для trigger_event
    event_type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class WorkflowStep(BaseModel):
    type: str = Field(..., pattern="^(http_request|send_email|delay|update_record|create_record|trigger_event)$")
    name: Optional[str] = None
    config: WorkflowStepConfig = Field(default_factory=WorkflowStepConfig)


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    trigger_event: str = Field(..., min_length=1, description="Событие для запуска (например, 'entity.created')")
    description: Optional[str] = None
    steps: List[WorkflowStep] = Field(default_factory=list)


class WorkflowCreate(WorkflowBase):
    tenant_id: Optional[int] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    is_active: Optional[bool] = None


class WorkflowResponse(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tenant_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: int
    status: str  # running, completed, failed
    context: Dict[str, Any]
    current_step: int
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]


# === Health Check ===

class HealthResponse(BaseModel):
    status: str
    version: str
