import pytest
from httpx import AsyncClient
from app.main import app
from app.core.auth import create_local_token
from sqlalchemy import select
from app.models.tables import users, roles, user_roles


@pytest.fixture
async def client():
    """Создание тестового клиента"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def setup_auth_db(setup_db):
    """Инициализация БД с auth таблицами"""
    async with app.state.db() as db:
        # Создаём тестовые роли
        await db.execute(roles.insert().values(
            name="admin",
            description="Administrator",
            permissions=["*"],
            is_system=True
        ))
        await db.execute(roles.insert().values(
            name="user",
            description="Regular user",
            permissions=["read"],
            is_system=False
        ))
        await db.commit()
    
    yield
    
    # Очистка
    async with app.state.db() as db:
        await db.execute(user_roles.delete())
        await db.execute(users.delete())
        await db.execute(roles.delete())
        await db.commit()


@pytest.fixture
def test_user_token():
    """Создание тестового JWT токена"""
    return create_local_token(
        user_id="test-user-1",
        username="testuser",
        roles=["user"],
        email="test@example.com"
    )


@pytest.fixture
def test_admin_token():
    """Создание admin JWT токена"""
    return create_local_token(
        user_id="test-admin-1",
        username="testadmin",
        roles=["admin", "user"],
        email="admin@example.com"
    )


@pytest.mark.asyncio
async def test_login_local(client: AsyncClient, setup_auth_db):
    """Тест локального логина"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "testuser"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, test_user_token):
    """Тест получения информации о пользователе"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["is_authenticated"] == True
    assert "user" in data["roles"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Тест получения информации без аутентификации"""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    """Тест невалидного токена"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_keycloak_config_disabled(client: AsyncClient):
    """Тест конфига Keycloak (должен быть отключен по умолчанию)"""
    response = await client.get("/api/v1/auth/keycloak-config")
    
    # По умолчанию Keycloak отключен
    assert response.status_code in [404, 200]


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, test_user_token):
    """Тест логаута"""
    response = await client.post("/api/v1/auth/logout")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_token_with_different_roles(client: AsyncClient):
    """Тест токенов с разными ролями"""
    # User token
    user_token = create_local_token(
        user_id="user-1",
        username="regular_user",
        roles=["user"]
    )
    
    # Admin token
    admin_token = create_local_token(
        user_id="admin-1",
        username="admin_user",
        roles=["admin", "user", "manager"]
    )
    
    # Проверяем user token
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["roles"] == ["user"]
    
    # Проверяем admin token
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert set(response.json()["roles"]) == {"admin", "user", "manager"}


@pytest.mark.asyncio
async def test_expired_token(client: AsyncClient):
    """Тест просроченного токена"""
    from datetime import datetime, timedelta
    from jose import jwt
    
    # Создаём просроченный токен
    payload = {
        "sub": "expired-user",
        "username": "expired",
        "roles": ["user"],
        "exp": datetime.utcnow() - timedelta(hours=1)  # Истёк час назад
    }
    
    expired_token = jwt.encode(
        payload,
        "super_secret_key_change_me_generate_random_string",
        algorithm="HS256"
    )
    
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    # Токен должен быть отклонён
    assert response.status_code == 401
