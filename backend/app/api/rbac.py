"""
API endpoints для управления ролями и доступом
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.core.database import get_db
from app.models.tables import roles, users, user_roles, entities, entity_permissions
from app.schemas import RoleCreate, RoleUpdate, RoleResponse, UserRoleAssign, EntityPermissionAssign

router = APIRouter()


# === Users ===

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка пользователей"""
    query = select(users).offset(skip).limit(limit).order_by(users.c.username)
    result = await db.execute(query)
    
    users_list = []
    for row in result.fetchall():
        user_dict = dict(row)
        
        # Получаем роли пользователя
        roles_query = (
            select(roles.c.name)
            .select_from(user_roles.join(roles, user_roles.c.role_id == roles.c.id))
            .where(user_roles.c.user_id == user_dict["id"])
        )
        roles_result = await db.execute(roles_query)
        user_dict["roles"] = [row[0] for row in roles_result.fetchall()]
        
        # Удаляем хеш пароля
        user_dict["metadata"].pop("password_hash", None)
        
        users_list.append(user_dict)
    
    return users_list


# === Roles CRUD ===

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка ролей"""
    query = select(roles).offset(skip).limit(limit).order_by(roles.c.name)
    result = await db.execute(query)
    return [dict(row) for row in result.fetchall()]


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    """Получение роли по ID"""
    query = select(roles).where(roles.c.id == role_id)
    result = await db.execute(query)
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return dict(row)


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание новой роли"""
    # Проверка уникальности
    check_query = select(roles).where(roles.c.name == role.name)
    check_result = await db.execute(check_query)
    if check_result.fetchone():
        raise HTTPException(status_code=400, detail="Role already exists")
    
    query = roles.insert().values(
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        is_system=False
    )
    result = await db.execute(query)
    await db.flush()
    
    role_id = result.inserted_primary_key[0]
    
    get_query = select(roles).where(roles.c.id == role_id)
    get_result = await db.execute(get_query)
    return dict(get_result.fetchone())


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role: RoleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление роли"""
    # Проверка существования
    check_query = select(roles).where(roles.c.id == role_id)
    check_result = await db.execute(check_query)
    existing = check_result.fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Нельзя изменять системные роли
    if existing.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system role")
    
    update_data = {k: v for k, v in role.model_dump().items() if v is not None}
    
    query = roles.update().where(roles.c.id == role_id).values(**update_data)
    await db.execute(query)
    await db.flush()
    
    get_query = select(roles).where(roles.c.id == role_id)
    get_result = await db.execute(get_query)
    return dict(get_result.fetchone())


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление роли"""
    # Проверка существования
    check_query = select(roles).where(roles.c.id == role_id)
    check_result = await db.execute(check_query)
    existing = check_result.fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Нельзя удалять системные роли
    if existing.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system role")
    
    # Удаляем связь с пользователями
    await db.execute(user_roles.delete().where(user_roles.c.role_id == role_id))
    
    # Удаляем роль
    query = roles.delete().where(roles.c.id == role_id)
    await db.execute(query)
    await db.flush()
    
    return None


# === User-Role Management ===

@router.get("/roles/{role_id}/users")
async def get_role_users(
    role_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение пользователей с данной ролью"""
    query = (
        select(users)
        .select_from(user_roles.join(users, user_roles.c.user_id == users.c.id))
        .where(user_roles.c.role_id == role_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return [dict(row) for row in result.fetchall()]


@router.post("/users/{user_id}/roles", status_code=201)
async def assign_role_to_user(
    user_id: int,
    role_assign: UserRoleAssign,
    db: AsyncSession = Depends(get_db)
):
    """Назначение роли пользователю"""
    # Проверка существования
    user_check = select(users).where(users.c.id == user_id)
    user_result = await db.execute(user_check)
    if not user_result.fetchone():
        raise HTTPException(status_code=404, detail="User not found")
    
    role_check = select(roles).where(roles.c.id == role_assign.role_id)
    role_result = await db.execute(role_check)
    if not role_result.fetchone():
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Проверка дубликата
    dup_check = select(user_roles).where(
        (user_roles.c.user_id == user_id) &
        (user_roles.c.role_id == role_assign.role_id)
    )
    dup_result = await db.execute(dup_check)
    if dup_result.fetchone():
        raise HTTPException(status_code=400, detail="Role already assigned")
    
    # Назначаем роль
    query = user_roles.insert().values(
        user_id=user_id,
        role_id=role_assign.role_id,
        expires_at=role_assign.expires_at
    )
    await db.execute(query)
    await db.flush()
    
    return {"message": "Role assigned successfully"}


@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удаление роли у пользователя"""
    query = user_roles.delete().where(
        (user_roles.c.user_id == user_id) &
        (user_roles.c.role_id == role_id)
    )
    result = await db.execute(query)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    
    await db.flush()
    return None


# === Entity Permissions ===

@router.get("/entities/{entity_id}/permissions")
async def get_entity_permissions(
    entity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение разрешений для сущности"""
    query = (
        select(entity_permissions, roles.c.name)
        .join(roles, entity_permissions.c.role_id == roles.c.id)
        .where(entity_permissions.c.entity_id == entity_id)
    )
    result = await db.execute(query)
    
    permissions = []
    for row in result.fetchall():
        perm_dict = dict(row)
        permissions.append({
            "id": perm_dict["id"],
            "role_id": perm_dict["role_id"],
            "role_name": perm_dict["name"],
            "can_read": perm_dict["can_read"],
            "can_create": perm_dict["can_create"],
            "can_update": perm_dict["can_update"],
            "can_delete": perm_dict["can_delete"],
            "row_filter": perm_dict["row_filter"],
        })
    
    return permissions


@router.post("/entities/{entity_id}/permissions", status_code=201)
async def set_entity_permission(
    entity_id: int,
    permission: EntityPermissionAssign,
    db: AsyncSession = Depends(get_db)
):
    """Установка разрешения для роли на сущность"""
    # Проверка существования
    entity_check = select(entities).where(entities.c.id == entity_id)
    entity_result = await db.execute(entity_check)
    if not entity_result.fetchone():
        raise HTTPException(status_code=404, detail="Entity not found")
    
    role_check = select(roles).where(roles.c.id == permission.role_id)
    role_result = await db.execute(role_check)
    if not role_result.fetchone():
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Проверка на дубликат
    dup_check = select(entity_permissions).where(
        (entity_permissions.c.entity_id == entity_id) &
        (entity_permissions.c.role_id == permission.role_id)
    )
    dup_result = await db.execute(dup_check)
    existing = dup_result.fetchone()
    
    if existing:
        # Обновляем
        update_query = entity_permissions.update().where(
            entity_permissions.c.id == existing.id
        ).values(
            can_read=permission.can_read,
            can_create=permission.can_create,
            can_update=permission.can_update,
            can_delete=permission.can_delete,
            row_filter=permission.row_filter
        )
        await db.execute(update_query)
        perm_id = existing.id
    else:
        # Создаём
        insert_query = entity_permissions.insert().values(
            entity_id=entity_id,
            role_id=permission.role_id,
            can_read=permission.can_read,
            can_create=permission.can_create,
            can_update=permission.can_update,
            can_delete=permission.can_delete,
            row_filter=permission.row_filter
        )
        result = await db.execute(insert_query)
        await db.flush()
        perm_id = result.inserted_primary_key[0]
    
    get_query = select(entity_permissions).where(entity_permissions.c.id == perm_id)
    get_result = await db.execute(get_query)
    return dict(get_result.fetchone())


@router.delete("/entities/{entity_id}/permissions/{permission_id}", status_code=204)
async def delete_entity_permission(
    entity_id: int,
    permission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удаление разрешения"""
    query = entity_permissions.delete().where(
        (entity_permissions.c.id == permission_id) &
        (entity_permissions.c.entity_id == entity_id)
    )
    result = await db.execute(query)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    await db.flush()
    return None
