"""
Сервис для управления пользователями и ролями
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import users, roles, user_roles, entity_permissions
from datetime import datetime


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_user(
        self,
        external_id: str,
        username: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Получение или создание пользователя
        
        Используется при первом входе через Keycloak
        """
        # Пробуем найти существующего
        query = select(users).where(users.c.external_id == external_id)
        result = await self.db.execute(query)
        user = result.fetchone()
        
        if user:
            # Обновляем last_login
            await self.db.execute(
                users.update().where(users.c.id == user.id).values(
                    last_login_at=datetime.utcnow()
                )
            )
            return dict(user)
        
        # Создаём нового
        insert_query = users.insert().values(
            external_id=external_id,
            username=username,
            email=email,
            full_name=full_name,
            metadata=metadata or {}
        )
        result = await self.db.execute(insert_query)
        await self.db.flush()
        
        user_id = result.inserted_primary_key[0]
        
        # Получаем созданного пользователя
        get_query = select(users).where(users.c.id == user_id)
        get_result = await self.db.execute(get_query)
        return dict(get_result.fetchone())
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя по ID"""
        query = select(users).where(users.c.id == user_id)
        result = await self.db.execute(query)
        row = result.fetchone()
        return dict(row) if row else None
    
    async def get_user_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Получение пользователя по external_id (Keycloak sub)"""
        query = select(users).where(users.c.external_id == external_id)
        result = await self.db.execute(query)
        row = result.fetchone()
        return dict(row) if row else None
    
    async def assign_role_to_user(
        self,
        user_id: int,
        role_id: int,
        assigned_by: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Назначение роли пользователю"""
        # Проверка дубликата
        check_query = select(user_roles).where(
            and_(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id
            )
        )
        check_result = await self.db.execute(check_query)
        if check_result.fetchone():
            return False
        
        # Назначаем роль
        insert_query = user_roles.insert().values(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        await self.db.execute(insert_query)
        return True
    
    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Удаление роли у пользователя"""
        delete_query = user_roles.delete().where(
            and_(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id
            )
        )
        result = await self.db.execute(delete_query)
        return result.rowcount > 0
    
    async def get_user_roles(self, user_id: int) -> List[Dict]:
        """Получение ролей пользователя"""
        query = (
            select(roles)
            .select_from(
                user_roles.join(roles, user_roles.c.role_id == roles.c.id)
            )
            .where(
                and_(
                    user_roles.c.user_id == user_id,
                    (user_roles.c.expires_at.is_(None) | (user_roles.c.expires_at > datetime.utcnow()))
                )
            )
        )
        result = await self.db.execute(query)
        return [dict(row) for row in result.fetchall()]
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """
        Получение всех разрешений пользователя
        
        Собирает permissions из всех ролей
        """
        roles_list = await self.get_user_roles(user_id)
        
        permissions = set()
        for role in roles_list:
            role_permissions = role.get("permissions", [])
            permissions.update(role_permissions)
        
        # Если суперпользователь - добавляем все разрешения
        user = await self.get_user_by_id(user_id)
        if user and user.get("is_superuser"):
            permissions.add("*")
        
        return list(permissions)


class RoleService:
    """Сервис для работы с ролями"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        is_system: bool = False
    ) -> Dict:
        """Создание роли"""
        # Проверка уникальности
        check_query = select(roles).where(roles.c.name == name)
        check_result = await self.db.execute(check_query)
        if check_result.fetchone():
            raise ValueError(f"Role '{name}' already exists")
        
        insert_query = roles.insert().values(
            name=name,
            description=description,
            permissions=permissions or [],
            is_system=is_system
        )
        result = await self.db.execute(insert_query)
        await self.db.flush()
        
        role_id = result.inserted_primary_key[0]
        
        get_query = select(roles).where(roles.c.id == role_id)
        get_result = await self.db.execute(get_query)
        return dict(get_result.fetchone())
    
    async def get_role_by_name(self, name: str) -> Optional[Dict]:
        """Получение роли по имени"""
        query = select(roles).where(roles.c.name == name)
        result = await self.db.execute(query)
        row = result.fetchone()
        return dict(row) if row else None
    
    async def list_roles(self) -> List[Dict]:
        """Список всех ролей"""
        query = select(roles).order_by(roles.c.name)
        result = await self.db.execute(query)
        return [dict(row) for row in result.fetchall()]
    
    async def update_role_permissions(
        self,
        role_id: int,
        permissions: List[str]
    ) -> Optional[Dict]:
        """Обновление разрешений роли"""
        # Проверка is_system
        check_query = select(roles.c.is_system).where(roles.c.id == role_id)
        check_result = await self.db.execute(check_query)
        row = check_result.fetchone()
        
        if row and row.is_system:
            raise ValueError("Cannot modify system role")
        
        update_query = roles.update().where(
            roles.c.id == role_id
        ).values(permissions=permissions)
        await self.db.execute(update_query)
        
        get_query = select(roles).where(roles.c.id == role_id)
        get_result = await self.db.execute(get_query)
        return dict(get_result.fetchone())


class EntityPermissionService:
    """Сервис для управления разрешениями сущностей"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def set_entity_permission(
        self,
        entity_id: int,
        role_id: int,
        can_read: bool = True,
        can_create: bool = False,
        can_update: bool = False,
        can_delete: bool = False,
        row_filter: Optional[Dict] = None
    ) -> Dict:
        """Установка разрешений для роли на сущность"""
        # Проверка на дубликат
        check_query = select(entity_permissions).where(
            and_(
                entity_permissions.c.entity_id == entity_id,
                entity_permissions.c.role_id == role_id
            )
        )
        check_result = await self.db.execute(check_query)
        existing = check_result.fetchone()
        
        if existing:
            # Обновляем
            update_query = entity_permissions.update().where(
                entity_permissions.c.id == existing.id
            ).values(
                can_read=can_read,
                can_create=can_create,
                can_update=can_update,
                can_delete=can_delete,
                row_filter=row_filter
            )
            await self.db.execute(update_query)
            perm_id = existing.id
        else:
            # Создаём
            insert_query = entity_permissions.insert().values(
                entity_id=entity_id,
                role_id=role_id,
                can_read=can_read,
                can_create=can_create,
                can_update=can_update,
                can_delete=can_delete,
                row_filter=row_filter
            )
            result = await self.db.execute(insert_query)
            await self.db.flush()
            perm_id = result.inserted_primary_key[0]
        
        get_query = select(entity_permissions).where(entity_permissions.c.id == perm_id)
        get_result = await self.db.execute(get_query)
        return dict(get_result.fetchone())
    
    async def get_entity_permissions(
        self,
        entity_id: int,
        role_ids: List[int]
    ) -> Optional[Dict]:
        """
        Получение эффективных разрешений для сущности
        
        Агрегирует разрешения из всех ролей пользователя
        """
        query = select(entity_permissions).where(
            and_(
                entity_permissions.c.entity_id == entity_id,
                entity_permissions.c.role_id.in_(role_ids)
            )
        )
        result = await self.db.execute(query)
        perms = result.fetchall()
        
        if not perms:
            return None
        
        # Агрегируем разрешения (OR логика)
        aggregated = {
            "can_read": False,
            "can_create": False,
            "can_update": False,
            "can_delete": False,
            "row_filters": []
        }
        
        for perm in perms:
            aggregated["can_read"] = aggregated["can_read"] or perm.can_read
            aggregated["can_create"] = aggregated["can_create"] or perm.can_create
            aggregated["can_update"] = aggregated["can_update"] or perm.can_update
            aggregated["can_delete"] = aggregated["can_delete"] or perm.can_delete
            
            if perm.row_filter:
                aggregated["row_filters"].append(perm.row_filter)
        
        # Объединяем row фильтры через OR
        if aggregated["row_filters"]:
            aggregated["row_filter"] = {"$or": aggregated["row_filters"]}
        else:
            aggregated["row_filter"] = None
        
        return aggregated
