# 🚀 Quick Start Guide

## Запуск через Docker Compose (рекомендуется)

### 1. Клонирование репозитория

```bash
git clone https://github.com/gowen-corp/ubackend.git
cd ubackend
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```bash
# Database
DB_USER=ubackend
DB_PASSWORD=change_me_to_secure_password
DB_NAME=ubackend_db

# Security
SECRET_KEY=generate_random_string_here_32_chars

# Keycloak (опционально, для начала false)
KEYCLOAK_ENABLED=false
```

### 3. Запуск

```bash
docker-compose up -d
```

Сервисы будут доступны:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/api/v1/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Первый вход

1. Откройте http://localhost:3000
2. Нажмите "Sign Up"
3. Зарегистрируйтесь (например, admin / admin123)
4. После входа увидите Dashboard

### 5. Проверка здоровья

```bash
curl http://localhost:8000/api/v1/health
```

Ответ:
```json
{
  "status": "healthy",
  "uptime_seconds": 123.45,
  "total_requests": 10,
  "total_errors": 0,
  "error_rate": 0.0
}
```

---

## Локальная разработка (без Docker)

### Backend

```bash
cd backend

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend доступен на http://localhost:8000

### Frontend

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск
npm run dev
```

Frontend доступен на http://localhost:3000

---

## Первые шаги после запуска

### 1. Создание сущности

1. Перейдите в **Entities** → **Create Entity**
2. Введите имя (например, `products`)
3. Нажмите **Create**
4. Перейдите в **Schema Builder**
5. Добавьте поля:
   - `name` (string, required)
   - `price` (number)
   - `quantity` (integer)
   - `active` (boolean)

### 2. Создание записей

1. Перейдите в **Records**
2. Выберите сущность `products`
3. Нажмите **Create Record**
4. Заполните поля

### 3. Создание workflow

1. Перейдите в **Workflows** → **Create Workflow**
2. Name: `Notify on new product`
3. Trigger: `record.created`
4. Добавьте шаг:
   - Type: `Send Email`
   - To: `admin@example.com`
   - Subject: `New product created`
5. Нажмите **Create Workflow**

### 4. Управление ролями

1. Перейдите в **Admin** → **Roles**
2. Создайте роль `manager`
3. Назначьте роль пользователю в **Admin** → **Users**

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/login` - Логин
- `GET /api/v1/auth/me` - Информация о пользователе

### Entities
- `GET /api/v1/entities` - Список сущностей
- `POST /api/v1/entities` - Создание
- `GET /api/v1/entities/{id}` - Получение
- `PUT /api/v1/entities/{id}` - Обновление
- `DELETE /api/v1/entities/{id}` - Удаление
- `GET /api/v1/entities/{id}/schema` - Схема
- `POST /api/v1/entities/{id}/schema/fields` - Добавить поле

### Records
- `GET /api/v1/records?entity_id={id}` - Список записей
- `POST /api/v1/records` - Создание
- `GET /api/v1/records/{id}` - Получение
- `PUT /api/v1/records/{id}` - Обновление
- `DELETE /api/v1/records/{id}` - Удаление

### Workflows
- `GET /api/v1/workflows` - Список workflow
- `POST /api/v1/workflows` - Создание
- `POST /api/v1/workflows/{id}/trigger` - Ручной запуск
- `POST /api/v1/workflows/{id}/toggle` - Включить/выключить

### RBAC
- `GET /api/v1/rbac/roles` - Список ролей
- `POST /api/v1/rbac/roles` - Создание роли
- `GET /api/v1/rbac/users` - Список пользователей
- `POST /api/v1/rbac/users/{id}/roles` - Назначить роль

---

## Troubleshooting

### Ошибка "Connection refused" к БД

Убедитесь, что PostgreSQL запущен:
```bash
docker-compose ps
```

Перезапустите:
```bash
docker-compose down
docker-compose up -d db
# Подождите 10 секунд
docker-compose up -d
```

### Ошибка миграций

```bash
cd backend
alembic upgrade head
```

### Сброс данных

```bash
docker-compose down -v  # Удаляет volumes
docker-compose up -d
```

---

## Production Deployment

### Переменные окружения для прода

```bash
# Обязательно смените!
SECRET_KEY=use_secure_random_string_64_chars
DB_PASSWORD=use_secure_password

# Keycloak (если используется)
KEYCLOAK_ENABLED=true
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=ubackend
KEYCLOAK_CLIENT_ID=ubackend-backend

# Rate limiting (опционально)
RATE_LIMIT_DEFAULT=1000
RATE_LIMIT_AUTH=20
```

### Docker Compose для прода

1. Замените `localhost` порты на нужные
2. Добавьте reverse proxy (nginx/traefik)
3. Настройте SSL сертификаты
4. Включите Keycloak

---

## Поддержка

- GitHub Issues: https://github.com/gowen-corp/ubackend/issues
- Документация: https://github.com/gowen-corp/ubackend/wiki
