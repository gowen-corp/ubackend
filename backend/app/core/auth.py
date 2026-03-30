"""
Модуль аутентификации с поддержкой Keycloak OIDC и локального JWT

Приоритет проверки токенов:
1. Keycloak (если включён)
2. Локальный JWT (fallback для сервисов и тестов)
"""
import httpx
import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from jose import jwt, JWTError, jwk
from jose.constants import ALGORITHMS
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

logger = structlog.get_logger()

# Security схема
security = HTTPBearer(auto_error=False)


class KeycloakClient:
    """Клиент для взаимодействия с Keycloak"""
    
    def __init__(self):
        self.server_url = settings.KEYCLOAK_SERVER_URL
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self._public_keys: Dict[str, Any] = {}
        self._keys_loaded_at: Optional[datetime] = None
    
    @property
    def is_enabled(self) -> bool:
        return settings.KEYCLOAK_ENABLED and all([
            self.server_url,
            self.realm,
            self.client_id
        ])
    
    @property
    def realm_url(self) -> str:
        return f"{self.server_url}/realms/{self.realm}"
    
    async def get_public_keys(self) -> Dict[str, Any]:
        """Получение публичных ключей Keycloak"""
        # Кэшируем ключи на 1 час
        if (
            self._keys_loaded_at and 
            datetime.utcnow() - self._keys_loaded_at < timedelta(hours=1)
        ):
            return self._public_keys
        
        jwks_url = f"{self.realm_url}/protocol/openid-connect/certs"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            self._public_keys = response.json()
            self._keys_loaded_at = datetime.utcnow()
        
        return self._public_keys
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Верификация токена через Keycloak
        
        Возвращает payload токена или None если невалиден
        """
        if not self.is_enabled:
            return None
        
        try:
            # Получаем заголовок токена для определения kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                logger.warning("Token missing kid")
                return None
            
            # Получаем публичные ключи
            keys = await self.get_public_keys()
            
            # Находим нужный ключ
            for key in keys.get("keys", []):
                if key.get("kid") == kid:
                    public_key = jwk.construct(key, algorithm=ALGORITHMS.RS256)
                    
                    try:
                        payload = jwt.decode(
                            token,
                            public_key,
                            algorithms=[ALGORITHMS.RS256],
                            audience=self.client_id,
                            issuer=f"{self.realm_url}"
                        )
                        return payload
                    except JWTError as e:
                        logger.warning(f"Token decode error: {e}")
                        return None
            
            logger.warning(f"Key {kid} not found in JWKS")
            return None
            
        except Exception as e:
            logger.error(f"Keycloak verification error: {e}")
            return None
    
    async def introspect_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Интроспекция токена через Keycloak API
        
        Альтернативный метод проверки через /token/introspect
        """
        if not self.is_enabled:
            return None
        
        introspect_url = f"{self.realm_url}/protocol/openid-connect/token/introspect"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                introspect_url,
                data={
                    "token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return data if data.get("active") else None


class LocalJWTVerifier:
    """Верификатор для локальных JWT токенов (fallback)"""
    
    def __init__(self):
        self.secret = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Верификация локального JWT токена"""
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Local JWT verify error: {e}")
            return None
    
    def create_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Создание локального JWT токена"""
        to_encode = data.copy()
        
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)


# Глобальные инстансы
keycloak_client = KeycloakClient()
local_verifier = LocalJWTVerifier()


async def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Верификация токена доступа
    
    Приоритет:
    1. Keycloak (если включён)
    2. Локальный JWT
    
    Raises:
        HTTPException: Если токен невалиден
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = None
    
    # Пробуем Keycloak
    if keycloak_client.is_enabled:
        payload = await keycloak_client.verify_token(token)
        
        # Fallback на интроспекцию
        if not payload:
            payload = await keycloak_client.introspect_token(token)
    
    # Fallback на локальный JWT
    if not payload:
        payload = local_verifier.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user(
    payload: Dict[str, Any] = Depends(verify_access_token)
) -> Dict[str, Any]:
    """
    Получение текущего пользователя из токена
    
    Поддерживаемые форматы:
    - Keycloak: sub, preferred_username, realm_access.roles
    - Local: sub, username, roles
    """
    # Нормализация полей
    user_id = payload.get("sub") or payload.get("user_id")
    username = (
        payload.get("preferred_username") or 
        payload.get("username") or 
        payload.get("email") or
        user_id
    )
    
    # Извлечение ролей
    roles = []
    
    # Keycloak формат
    realm_access = payload.get("realm_access", {})
    if realm_access:
        roles.extend(realm_access.get("roles", []))
    
    # Resource access (client-specific roles)
    resource_access = payload.get("resource_access", {})
    if resource_access:
        client_roles = resource_access.get(
            settings.KEYCLOAK_CLIENT_ID or "realm", 
            {}
        ).get("roles", [])
        roles.extend(client_roles)
    
    # Local формат
    if payload.get("roles"):
        roles.extend(payload["roles"])
    
    return {
        "id": user_id,
        "username": username,
        "email": payload.get("email"),
        "roles": list(set(roles)),  # Убираем дубликаты
        "raw": payload
    }


def require_roles(*required_roles: str):
    """
    Декоратор для проверки наличия ролей
    
    Использование:
        @router.get("/admin", dependencies=[Depends(require_roles("admin"))])
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        user_roles = set(current_user.get("roles", []))
        required = set(required_roles)
        
        if not required.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {required_roles}",
            )
        
        return current_user
    
    return role_checker


def create_local_token(
    user_id: str,
    username: str,
    roles: List[str],
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создание локального JWT токена (для сервисов и тестов)
    """
    return local_verifier.create_token(
        data={
            "sub": user_id,
            "username": username,
            "email": email,
            "roles": roles
        },
        expires_delta=expires_delta
    )
