import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import async_session_maker, init_db
from sqlalchemy import select
from app.models.tables import entities


@pytest.fixture
async def client():
    """Создание тестового клиента"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def setup_db():
    """Инициализация БД перед тестами"""
    await init_db()
    yield
    # Очистка после тестов
    async with async_session_maker() as db:
        from app.models.tables import records, event_outbox, workflows, workflow_runs
        
        # Удаляем в обратном порядке из-за FK
        await db.execute(records.delete())
        await db.execute(event_outbox.delete())
        await db.execute(workflow_runs.delete())
        await db.execute(workflows.delete())
        await db.execute(entities.delete())
        await db.commit()


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Тест health check endpoint"""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Тест корневого endpoint"""
    response = await client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]


@pytest.mark.asyncio
async def test_create_entity(client: AsyncClient, setup_db):
    """Тест создания сущности"""
    entity_data = {
        "name": "test_entity",
        "description": "Test entity for testing",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
    }
    
    response = await client.post("/api/v1/entities", json=entity_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "test_entity"
    assert data["description"] == "Test entity for testing"
    assert "id" in data
    
    return data


@pytest.mark.asyncio
async def test_get_entity(client: AsyncClient, setup_db):
    """Тест получения сущности"""
    # Создаём сущность
    entity_data = {"name": "get_test", "schema": {}}
    create_response = await client.post("/api/v1/entities", json=entity_data)
    entity_id = create_response.json()["id"]
    
    # Получаем сущность
    response = await client.get(f"/api/v1/entities/{entity_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == entity_id
    assert data["name"] == "get_test"


@pytest.mark.asyncio
async def test_list_entities(client: AsyncClient, setup_db):
    """Тест списка сущностей"""
    # Создаём несколько сущностей
    for i in range(3):
        await client.post("/api/v1/entities", json={
            "name": f"entity_{i}",
            "schema": {}
        })
    
    response = await client.get("/api/v1/entities")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_update_entity(client: AsyncClient, setup_db):
    """Тест обновления сущности"""
    # Создаём сущность
    entity_data = {"name": "update_test", "schema": {}}
    create_response = await client.post("/api/v1/entities", json=entity_data)
    entity_id = create_response.json()["id"]
    
    # Обновляем
    update_data = {"description": "Updated description"}
    response = await client.put(f"/api/v1/entities/{entity_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_entity(client: AsyncClient, setup_db):
    """Тест удаления сущности"""
    # Создаём сущность
    entity_data = {"name": "delete_test", "schema": {}}
    create_response = await client.post("/api/v1/entities", json=entity_data)
    entity_id = create_response.json()["id"]
    
    # Удаляем
    response = await client.delete(f"/api/v1/entities/{entity_id}")
    assert response.status_code == 204
    
    # Проверяем, что сущность неактивна
    response = await client.get(f"/api/v1/entities/{entity_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False


@pytest.mark.asyncio
async def test_duplicate_entity_name(client: AsyncClient, setup_db):
    """Тест уникальности имени сущности"""
    entity_data = {"name": "unique_test", "schema": {}}
    
    # Создаём первую сущность
    response1 = await client.post("/api/v1/entities", json=entity_data)
    assert response1.status_code == 201
    
    # Пытаемся создать с таким же именем
    response2 = await client.post("/api/v1/entities", json=entity_data)
    assert response2.status_code == 400


@pytest.mark.asyncio
async def test_create_record(client: AsyncClient, setup_db):
    """Тест создания записи"""
    # Создаём сущность
    entity_response = await client.post("/api/v1/entities", json={
        "name": "records_test",
        "schema": {}
    })
    entity_id = entity_response.json()["id"]
    
    # Создаём запись
    record_data = {
        "entity_id": entity_id,
        "data": {"name": "John", "age": 30}
    }
    
    response = await client.post("/api/v1/records", json=record_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["data"]["name"] == "John"
    assert data["entity_id"] == entity_id


@pytest.mark.asyncio
async def test_list_records_with_filters(client: AsyncClient, setup_db):
    """Тест фильтрации записей"""
    import json
    
    # Создаём сущность
    entity_response = await client.post("/api/v1/entities", json={
        "name": "filter_test",
        "schema": {}
    })
    entity_id = entity_response.json()["id"]
    
    # Создаём записи
    for i in range(5):
        await client.post("/api/v1/records", json={
            "entity_id": entity_id,
            "data": {"status": "active" if i % 2 == 0 else "inactive", "value": i * 10}
        })
    
    # Фильтруем по статусу
    filters = json.dumps({"status": {"eq": "active"}})
    response = await client.get(
        f"/api/v1/records?entity_id={entity_id}&filters={filters}"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 3  # 0, 2, 4 - активные


@pytest.mark.asyncio
async def test_record_not_found(client: AsyncClient, setup_db):
    """Тест получения несуществующей записи"""
    response = await client.get("/api/v1/records/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_record_invalid_entity(client: AsyncClient, setup_db):
    """Тест создания записи с несуществующей сущностью"""
    record_data = {
        "entity_id": 999999,
        "data": {"test": "data"}
    }
    
    response = await client.post("/api/v1/records", json=record_data)
    assert response.status_code == 400
