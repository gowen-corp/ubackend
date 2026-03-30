# uBackend - Universal Low Code Backend

Платформа для быстрой разработки внутренних систем с использованием подхода JSONB-first.

## Архитектура

- **Backend**: FastAPI + SQLAlchemy Core + asyncpg
- **Database**: PostgreSQL 15 (JSONB для гибкой схемы данных)
- **Cache/Queue**: Redis + ARQ для фоновых задач
- **Frontend**: Next.js + TypeScript + Tailwind CSS

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/gowen-corp/ubackend.git
cd ubackend
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
# Отредактируйте .env, установив безопасные пароли
```

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

Сервисы будут доступны по адресам:
- API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 4. Проверка здоровья

```bash
curl http://localhost:8000/api/v1/health
```

## Структура проекта

```
ubackend/
├── backend/
│   ├── app/
│   │   ├── api/          # API роуты
│   │   ├── core/         # Конфигурация, БД
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── services/     # Бизнес-логика
│   │   └── workers/      # ARQ задачи
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js App Router
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## Разработка

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Ключевые возможности

- **JSONB-first**: Гибкая схема данных без миграций
- **Transactional Outbox**: Гарантированная доставка событий
- **Workflow Engine**: Визуальный конструктор бизнес-процессов
- **RBAC**: Ролевая модель доступа с фильтрацией на уровне строк

## License

MIT
