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
    settings,
)
from app.schemas import TokenResponse, UserInfo, LoginRequest, RegisterRequest
from app.services.auth_service import UserService
from app.services.local_auth_service import LocalAuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Локальный логин с паролем (для разработки)
    
    Если KEYCLOAK_ENABLED=true — будет использоваться Keycloak
    """
    local_auth = LocalAuthService(db)
    
    # Пробуем локальную аутентификацию
    result = await local_auth.authenticate(request.username, request.password or "")
    
    if result:
        return result
    
    # Если не нашли локального пользователя и Keycloak включён — пробуем Keycloak
    if keycloak_client.is_enabled and request.password:
        # Здесь могла бы быть интеграция с Keycloak Resource Owner Password Credentials
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )


@router.post("/register", response_model=UserInfo)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя (только для локальной аутентификации)
    
    Не работает с Keycloak — там регистрация через Admin Console
    """
    if keycloak_client.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration disabled when Keycloak is enabled"
        )
    
    local_auth = LocalAuthService(db)
    
    try:
        user = await local_auth.register_user(
            username=request.username,
            password=request.password,
            email=request.email,
            full_name=request.full_name
        )
        
        return {
            "id": str(user["id"]),
            "username": user["username"],
            "email": user.get("email"),
            "roles": ["user"],  # Default role
            "is_authenticated": True
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


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


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Смена пароля текущего пользователя
    """
    local_auth = LocalAuthService(db)
    
    success = await local_auth.change_password(
        user_id=int(current_user["id"]),
        old_password=old_password,
        new_password=new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    return {"message": "Password changed successfully"}
