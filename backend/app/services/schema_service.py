"""
Сервис для управления схемами сущностей

Поддерживаемые типы полей:
- string
- number (integer/float)
- boolean
- date
- datetime
- json
- reference (ссылка на другую сущность)
- array
"""
from typing import Dict, Any, List, Optional, Literal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import entities
import structlog

logger = structlog.get_logger()

FieldType = Literal["string", "number", "integer", "boolean", "date", "datetime", "json", "reference", "array", "email", "text"]


class SchemaField:
    """Модель поля схемы"""
    
    def __init__(
        self,
        name: str,
        type: FieldType = "string",
        required: bool = False,
        description: Optional[str] = None,
        default: Any = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        pattern: Optional[str] = None,
        enum: Optional[List[Any]] = None,
        reference_entity_id: Optional[int] = None,  # Для типа reference
        items_type: Optional[FieldType] = None,  # Для типа array
    ):
        self.name = name
        self.type = type
        self.required = required
        self.description = description
        self.default = default
        self.min_length = min_length
        self.max_length = max_length
        self.minimum = minimum
        self.maximum = maximum
        self.pattern = pattern
        self.enum = enum
        self.reference_entity_id = reference_entity_id
        self.items_type = items_type
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Конвертация в JSON Schema формат"""
        schema: Dict[str, Any] = {
            "type": self.type,
        }
        
        if self.description:
            schema["description"] = self.description
        
        if self.default is not None:
            schema["default"] = self.default
        
        # Валидации для string
        if self.type in ["string", "text", "email"]:
            if self.min_length:
                schema["minLength"] = self.min_length
            if self.max_length:
                schema["maxLength"] = self.max_length
            if self.pattern:
                schema["pattern"] = self.pattern
            if self.type == "email":
                schema["format"] = "email"
        
        # Валидации для number/integer
        if self.type in ["number", "integer"]:
            if self.minimum is not None:
                schema["minimum"] = self.minimum
            if self.maximum is not None:
                schema["maximum"] = self.maximum
        
        # Enum
        if self.enum:
            schema["enum"] = self.enum
        
        # Reference
        if self.type == "reference" and self.reference_entity_id:
            schema["x-reference"] = self.reference_entity_id
        
        # Array items
        if self.type == "array" and self.items_type:
            schema["items"] = {"type": self.items_type}
        
        return schema


class EntitySchemaService:
    """Сервис для управления схемами сущностей"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_entity_schema(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Получение схемы сущности"""
        query = select(entities.c.schema).where(entities.c.id == entity_id)
        result = await self.db.execute(query)
        row = result.fetchone()
        
        if row:
            return row[0]
        return None
    
    async def update_entity_schema(
        self,
        entity_id: int,
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Обновление схемы сущности
        
        Schema формат:
        {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "...",
                    ...
                }
            },
            "required": ["field1", "field2"]
        }
        """
        # Проверка существования сущности
        check_query = select(entities).where(entities.c.id == entity_id)
        check_result = await self.db.execute(check_query)
        entity = check_result.fetchone()
        
        if not entity:
            return None
        
        # Валидация схемы
        if not self._validate_schema(schema):
            raise ValueError("Invalid schema format")
        
        # Обновление
        update_query = entities.update().where(
            entities.c.id == entity_id
        ).values(
            schema=schema,
            version=entities.c.version + 1
        )
        await self.db.execute(update_query)
        await self.db.flush()
        
        return schema
    
    async def add_field_to_schema(
        self,
        entity_id: int,
        field_name: str,
        field_type: FieldType = "string",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Добавление поля к схеме сущности"""
        schema = await self.get_entity_schema(entity_id)
        
        if not schema:
            schema = {"type": "object", "properties": {}, "required": []}
        
        if "properties" not in schema:
            schema["properties"] = {}
        
        if "required" not in schema:
            schema["required"] = []
        
        # Проверка дубликата
        if field_name in schema["properties"]:
            raise ValueError(f"Field '{field_name}' already exists")
        
        # Создание поля
        field = SchemaField(name=field_name, type=field_type, **kwargs)
        schema["properties"][field_name] = field.to_json_schema()
        
        if field.required:
            schema["required"].append(field_name)
        
        return await self.update_entity_schema(entity_id, schema)
    
    async def remove_field_from_schema(
        self,
        entity_id: int,
        field_name: str
    ) -> Optional[Dict[str, Any]]:
        """Удаление поля из схемы"""
        schema = await self.get_entity_schema(entity_id)
        
        if not schema or "properties" not in schema:
            return None
        
        if field_name not in schema["properties"]:
            raise ValueError(f"Field '{field_name}' not found")
        
        # Удаляем поле
        del schema["properties"][field_name]
        
        # Удаляем из required если есть
        if field_name in schema.get("required", []):
            schema["required"].remove(field_name)
        
        return await self.update_entity_schema(entity_id, schema)
    
    async def update_field_in_schema(
        self,
        entity_id: int,
        field_name: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """Обновление поля в схеме"""
        schema = await self.get_entity_schema(entity_id)
        
        if not schema or "properties" not in schema:
            return None
        
        if field_name not in schema["properties"]:
            raise ValueError(f"Field '{field_name}' not found")
        
        # Обновляем поле
        schema["properties"][field_name].update(updates)
        
        # Обновляем required
        is_required = updates.get("required", False)
        if is_required and field_name not in schema.get("required", []):
            schema["required"].append(field_name)
        elif not is_required and field_name in schema.get("required", []):
            schema["required"].remove(field_name)
        
        return await self.update_entity_schema(entity_id, schema)
    
    def _validate_schema(self, schema: Dict[str, Any]) -> bool:
        """Валидация структуры схемы"""
        if not isinstance(schema, dict):
            return False
        
        # Должен быть object
        if schema.get("type") != "object":
            return False
        
        # Properties должен быть dict
        if "properties" in schema and not isinstance(schema["properties"], dict):
            return False
        
        # Required должен быть list
        if "required" in schema and not isinstance(schema["required"], list):
            return False
        
        return True
    
    async def get_schema_fields(self, entity_id: int) -> List[Dict[str, Any]]:
        """Получение списка полей схемы"""
        schema = await self.get_entity_schema(entity_id)
        
        if not schema or "properties" not in schema:
            return []
        
        fields = []
        required_fields = schema.get("required", [])
        
        for name, props in schema["properties"].items():
            field = {
                "name": name,
                "type": props.get("type", "string"),
                "required": name in required_fields,
                "description": props.get("description"),
                "config": {k: v for k, v in props.items() if k not in ["type", "description"]}
            }
            fields.append(field)
        
        return fields
