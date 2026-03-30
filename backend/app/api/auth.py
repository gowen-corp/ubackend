"""
Auth endpoints для управления сессиями и токенами
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import (
    get_current_user,
    create_local_token,
    keycloak_client,
    settings
)
from app.schemas import TokenResponse, UserInfo, LoginRequest
from app.services.auth_service import UserService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Локальный логин (для сервисов и тестов)
    
    Для прода используйте Keycloak OIDC flow
    """
    # В реальной реализации здесь была бы проверка пароля
    # Для MVP создаём токен для существующего пользователя
    
    user_service = UserService(db)
    
    # Проверяем существование пользователя
    user = await user_service.get_user_by_external_id(request.username)
    
    if not user:
        # Создаём нового (для первого входа)
        user = await user_service.get_or_create_user(
            external_id=request.username,
            username=request.username
        )
    
    # Создаём JWT токен
    token = create_local_token(
        user_id=str(user["id"]),
        username=user["username"],
        roles=["user"],  # Default role
        email=user.get("email")
    )
    
    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о текущем пользователе
    """
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user.get("email"),
        "roles": current_user.get("roles", []),
        "is_authenticated": True
    }


@router.get("/keycloak-config")
async def get_keycloak_config():
    """
    Конфигурация Keycloak для frontend
    
    Используется для настройки Keycloak JS adapter
    """
    if not keycloak_client.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keycloak not configured"
        )
    
    return {
        "url": settings.KEYCLOAK_SERVER_URL,
        "realm": settings.KEYCLOAK_REALM,
        "clientId": settings.KEYCLOAK_CLIENT_ID,
        "enabled": True
    }


@router.post("/logout")
async def logout():
    """
    Логаут (на клиенте нужно удалить токен)
    
    Для Keycloak - редирект на Keycloak logout URL
    """
    if keycloak_client.is_enabled:
        return {
            "logout_url": f"{keycloak_client.realm_url}/protocol/openid-connect/logout"
        }
    
    return {"message": "Logged out locally"}
