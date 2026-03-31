"""
Local Authentication Service для разработки/тестирования

Предоставляет простую аутентификацию по паролю без Keycloak:
- Регистрация пользователя с паролем
- Логин с проверкой пароля
- Хранение хешей паролей в БД
- JWT токены с ролями

Используется только когда KEYCLOAK_ENABLED=false
"""
import bcrypt
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import users, roles, user_roles
from app.core.auth import create_local_token
from app.config import settings
import structlog

logger = structlog.get_logger()


class LocalAuthService:
    """Сервис локальной аутентификации"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Регистрация нового пользователя
        
        Args:
            username: Уникальное имя пользователя
            password: Пароль (будет захеширован)
            email: Email (опционально)
            full_name: Полное имя (опционально)
        
        Returns:
            Данные пользователя
        
        Raises:
            ValueError: Если пользователь с таким именем уже существует
        """
        # Проверка существования
        check_query = select(users).where(users.c.username == username)
        check_result = await self.db.execute(check_query)
        if check_result.fetchone():
            raise ValueError(f"User '{username}' already exists")
        
        # Хеширование пароля
        password_hash = self._hash_password(password)
        
        # Создание пользователя
        insert_query = users.insert().values(
            external_id=f"local:{username}",  # Префикс для локальных пользователей
            username=username,
            email=email,
            full_name=full_name,
            metadata={"password_hash": password_hash},
            is_active=True
        )
        result = await self.db.execute(insert_query)
        await self.db.flush()
        
        user_id = result.inserted_primary_key[0]
        
        # Назначаем роль "user" по умолчанию
        default_role = await self._get_role_by_name("user")
        if default_role:
            await self.db.execute(user_roles.insert().values(
                user_id=user_id,
                role_id=default_role["id"]
            ))
        
        # Получаем созданного пользователя
        get_query = select(users).where(users.c.id == user_id)
        get_result = await self.db.execute(get_query)
        user = dict(get_result.fetchone())
        
        # Удаляем хеш из ответа
        user["metadata"].pop("password_hash", None)
        
        return user
    
    async def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Аутентификация пользователя по паролю
        
        Returns:
            Данные пользователя с токеном или None если неверные credentials
        """
        # Поиск пользователя
        query = select(users).where(
            users.c.username == username,
            users.c.is_active == True
        )
        result = await self.db.execute(query)
        user = result.fetchone()
        
        if not user:
            logger.warning(f"User '{username}' not found")
            return None
        
        user_dict = dict(user)
        
        # Проверка пароля
        password_hash = user_dict["metadata"].get("password_hash")
        if not password_hash:
            logger.warning(f"User '{username}' has no password hash")
            return None
        
        if not self._verify_password(password, password_hash):
            logger.warning(f"Invalid password for user '{username}'")
            return None
        
        # Обновление last_login
        await self.db.execute(
            users.update().where(users.c.id == user_dict["id"]).values(
                last_login_at=datetime.utcnow()
            )
        )
        
        # Получение ролей
        roles_query = (
            select(roles.c.name)
            .select_from(user_roles.join(roles, user_roles.c.role_id == roles.c.id))
            .where(user_roles.c.user_id == user_dict["id"])
        )
        roles_result = await self.db.execute(roles_query)
        user_roles_list = [row[0] for row in roles_result.fetchall()]
        
        # Создание токена
        token = create_local_token(
            user_id=str(user_dict["id"]),
            username=user_dict["username"],
            roles=user_roles_list,
            email=user_dict.get("email")
        )
        
        # Возвращаем данные без хеша
        user_dict["metadata"].pop("password_hash", None)
        
        return {
            "user": user_dict,
            "token": token,
            "token_type": "bearer"
        }
    
    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Смена пароля пользователя
        
        Returns:
            True если успешно, False если старый пароль неверный
        """
        query = select(users).where(users.c.id == user_id)
        result = await self.db.execute(query)
        user = result.fetchone()
        
        if not user:
            return False
        
        user_dict = dict(user)
        password_hash = user_dict["metadata"].get("password_hash")
        
        # Проверка старого пароля
        if not password_hash or not self._verify_password(old_password, password_hash):
            return False
        
        # Обновление пароля
        new_hash = self._hash_password(new_password)
        metadata = user_dict["metadata"].copy()
        metadata["password_hash"] = new_hash
        
        await self.db.execute(
            users.update().where(users.c.id == user_id).values(
                metadata=metadata
            )
        )
        
        return True
    
    def _hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Проверка пароля"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    async def _get_role_by_name(self, name: str) -> Optional[Dict]:
        """Получение роли по имени"""
        query = select(roles).where(roles.c.name == name)
        result = await self.db.execute(query)
        row = result.fetchone()
        return dict(row) if row else None
    
    async def get_or_create_default_roles(self) -> List[Dict]:
        """
        Создание ролей по умолчанию если их нет
        
        Вызывать при старте приложения
        """
        default_roles = [
            {"name": "admin", "description": "Administrator", "permissions": ["*"], "is_system": True},
            {"name": "user", "description": "Regular user", "permissions": ["read"], "is_system": False},
            {"name": "manager", "description": "Manager", "permissions": ["read", "create", "update"], "is_system": False},
        ]
        
        created_roles = []
        
        for role_data in default_roles:
            existing = await self._get_role_by_name(role_data["name"])

            if not existing:
                # Создаём роль
                insert_query = roles.insert().values(**role_data)
                result = await self.db.execute(insert_query)
                await self.db.flush()

                role_id = result.inserted_primary_key[0]
                get_query = select(roles).where(roles.c.id == role_id)
                get_result = await self.db.execute(get_query)
                row = get_result.fetchone()
                if row:
                    created_roles.append({
                        "id": row.id,
                        "name": row.name,
                        "description": row.description,
                        "permissions": row.permissions,
                        "is_system": row.is_system,
                        "created_at": row.created_at,
                    })
            else:
                created_roles.append(existing)

        return created_roles
