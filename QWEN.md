# uBackend — Low-Code Platform Context

## Project Overview

**uBackend** — универсальная low-code платформа для быстрой разработки внутренних систем с использованием подхода **JSONB-first**. Платформа позволяет создавать бэкенд-приложения декларативно через веб-интерфейс без написания кода.

### Key Technologies

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI + SQLAlchemy Core + asyncpg |
| **Database** | PostgreSQL 15 (JSONB для гибкой схемы) |
| **Cache/Queue** | Redis + ARQ для фоновых задач |
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS |
| **Auth** | python-jose (JWT) / Keycloak (опционально) |
| **Logging** | Structlog (JSON-логи) |

### Architecture Highlights

- **JSONB-first**: Гибкая схема данных без миграций — все пользовательские данные хранятся в JSONB-полях
- **Transactional Outbox**: Гарантированная доставка событий через таблицу `event_outbox`
- **Workflow Engine**: Визуальный конструктор бизнес-процессов (триггеры → условия → действия)
- **RBAC**: Ролевая модель доступа с фильтрацией на уровне строк (Row-Level Security)
- **Multi-tenancy**: Изоляция данных по `tenant_id`

---

## Building and Running

### Quick Start (Docker Compose)

```bash
# 1. Клонирование
git clone https://github.com/gowen-corp/ubackend.git
cd ubackend

# 2. Настройка окружения
cp .env.example .env
# Отредактируйте .env: SECRET_KEY, DB_PASSWORD

# 3. Запуск
docker-compose up -d

# 4. Проверка
curl http://localhost:8000/api/v1/health
```

**Сервисы:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/api/v1/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Testing

```bash
cd backend
pytest  # или pytest -v для подробного вывода
```

---

## Project Structure

```
ubackend/
├── backend/
│   ├── app/
│   │   ├── api/              # API роуты
│   │   │   ├── auth.py       # Аутентификация (JWT)
│   │   │   ├── entities.py   # CRUD сущностей
│   │   │   ├── records.py    # CRUD записей (динамический)
│   │   │   ├── workflow.py   # Workflow management
│   │   │   ├── rbac.py       # Роли и разрешения
│   │   │   └── router.py     # Основной роутер
│   │   ├── core/             # Ядро системы
│   │   │   ├── database.py   # DB connection pool
│   │   │   ├── logging.py    # Structlog настройка
│   │   │   ├── rate_limiter.py
│   │   │   └── security.py   # JWT, hashing
│   │   ├── models/
│   │   │   └── tables.py     # SQLAlchemy Core таблицы
│   │   ├── services/         # Бизнес-логика
│   │   │   ├── auth_service.py
│   │   │   ├── entity_service.py
│   │   │   ├── record_service.py
│   │   │   └── workflow_service.py
│   │   ├── workers/          # ARQ воркеры
│   │   │   └── workflow_worker.py
│   │   ├── config.py         # Pydantic settings
│   │   ├── main.py           # FastAPI app entry point
│   │   └── schemas.py        # Pydantic схемы
│   ├── alembic/              # DB миграции
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/
│   ├── lib/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Database Schema

### System Tables (Metadata)

| Table | Description |
|-------|-------------|
| `entities` | Определения сущностей (slug, schema_definition, version) |
| `roles` | Роли с permissions (JSONB) |
| `users` | Пользователи (синхронизация с Keycloak) |
| `user_roles` | Many-to-many связь пользователей и ролей |
| `entity_permissions` | Разрешения на сущности + row_filter |

### Data Tables

| Table | Description |
|-------|-------------|
| `records` | **Единая таблица для всех записей** (data JSONB) |
| `event_outbox` | Очередь событий для workflow (pending/processed/failed) |
| `workflows` | Определения workflow (trigger_event, steps JSONB) |
| `workflow_runs` | История выполнений workflow |

**Ключевой паттерн:** Все пользовательские данные хранятся в `records.data` (JSONB) с GIN-индексом для быстрой фильтрации.

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` — Регистрация
- `POST /api/v1/auth/login` — Логин (JWT)
- `GET /api/v1/auth/me` — Текущий пользователь

### Entities (Metadata)
- `GET/POST/PUT/DELETE /api/v1/entities` — CRUD сущностей
- `POST /api/v1/entities/{id}/schema/fields` — Добавить поле

### Records (Dynamic CRUD)
- `GET /api/v1/records?entity_id={id}` — Список с фильтрами
- `POST /api/v1/records` — Создание записи
- `PUT/PATCH/DELETE /api/v1/records/{id}` — Операции с записью

### Workflows
- `GET/POST /api/v1/workflows` — Управление workflow
- `POST /api/v1/workflows/{id}/trigger` — Ручной запуск
- `POST /api/v1/workflows/{id}/toggle` — Вкл/Выкл

### RBAC
- `GET/POST /api/v1/rbac/roles` — Роли
- `POST /api/v1/rbac/users/{id}/roles` — Назначить роль

---

## Development Conventions

### Code Style
- **Python**: Type hints обязательны, Pydantic для валидации
- **Frontend**: TypeScript, React Hook Form + Zod для форм
- **Logging**: Structlog с JSON-выводом (поля: `timestamp`, `level`, `event`, `request_id`, `user_id`)

### Testing Practices
- **Unit tests**: `pytest` + `pytest-asyncio` для async тестов
- **Integration tests**: Тестирование API через `httpx.AsyncClient`
- **Test fixtures**: Фикстуры для БД (создание тестовых сущностей/записей)

### Security
- JWT токены с expiration (30 мин access)
- Password hashing через bcrypt (passlib)
- Rate limiting на middleware уровне
- Row-Level Security через `row_filter` в `entity_permissions`

### Key Patterns
1. **Dynamic Model Validation**: Валидация данных через Pydantic модели, генерируемые на лету из схемы сущности
2. **Outbox Pattern**: Запись события в `event_outbox` в той же транзакции, что и изменение данных
3. **Cache Invalidation**: Кэширование схем в Redis с инвалидацией при изменении метаданных
4. **Middleware Order**: CORS → Rate Limit → Logging → Auth

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | PostgreSQL пользователь | `ubackend` |
| `DB_PASSWORD` | PostgreSQL пароль | _required_ |
| `DB_NAME` | Имя БД | `ubackend_db` |
| `SECRET_KEY` | JWT secret key | _required_ |
| `KEYCLOAK_ENABLED` | Включить OIDC | `false` |
| `REDIS_HOST` | Redis хост | `redis` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

---

## Troubleshooting

### DB Connection Error
```bash
docker-compose ps  # Проверить статус контейнеров
docker-compose down && docker-compose up -d db
# Подождать 10 сек, затем:
docker-compose up -d
```

### Migration Issues
```bash
cd backend
alembic upgrade head
```

### Reset All Data
```bash
docker-compose down -v  # Удаляет volumes
docker-compose up -d
```

---

## Documentation Files

- `README.md` — Общий обзор проекта
- `QUICKSTART.md` — Подробное руководство по запуску и первым шагам
- `TECHNICAL_SPECIFICATION_BACKEND.md` — Детальное ТЗ backend
- `TECHNICAL_SPECIFICATION_FRONTEND.md` — Спецификация frontend
- `architecture_description.md` — Описание архитектуры по слоям
- `lowcode_backend_description.md` — Описание концепции low-code платформы
