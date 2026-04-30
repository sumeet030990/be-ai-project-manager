# Project Manager — Backend API

A production-ready REST API built with **FastAPI**, following an **n-tier architecture** (Routes → Controllers → Services → Repositories) backed by **PostgreSQL** via async SQLAlchemy.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.136.1 |
| Server | Uvicorn 0.46.0 |
| Validation | Pydantic 2.13.3 |
| ORM | SQLAlchemy 2.0.49 (async) |
| Migrations | Alembic 1.18.4 |
| Database Driver | asyncpg 0.31.0 |
| Config | pydantic-settings 2.14.0 |

---

## Project Structure

```
be-project-manager/
├── main.py                          # Uvicorn entrypoint
├── requirements.txt
├── .env.example
├── alembic.ini
├── alembic/
│   ├── env.py                       # Async Alembic configuration
│   ├── script.py.mako               # Migration template
│   └── versions/                    # Auto-generated migration files
└── app/
    ├── main.py                      # FastAPI app factory (CORS, middleware, exception handlers)
    ├── core/
    │   ├── config.py                # Pydantic Settings — reads from .env
    │   ├── database.py              # Async engine, session factory, Base
    │   ├── dependencies.py          # Annotated DBSession injectable type
    │   └── exceptions.py            # AppException hierarchy + global handler
    ├── middleware/
    │   └── logging.py               # Request logging + X-Request-Id header
    ├── models/
    │   ├── base.py                  # BaseModel (UUID primary key + timestamps)
    │   └── project.py               # Project SQLAlchemy model
    ├── schemas/
    │   ├── common.py                # PaginatedResponse[T] generic schema
    │   └── project.py               # ProjectCreate / ProjectUpdate / ProjectResponse
    ├── repositories/
    │   ├── base.py                  # Generic BaseRepository[T] — CRUD operations
    │   └── project_repository.py   # Project-specific queries
    ├── services/
    │   └── project_service.py      # Business logic, raises domain exceptions
    ├── controllers/
    │   └── project_controller.py   # HTTP plumbing — calls service, returns response
    └── routes/
        ├── __init__.py              # api_router aggregator
        ├── health.py                # GET /health
        └── project.py              # CRUD /projects endpoints
```

---

## Architecture

```
HTTP Request
     │
     ▼
 [ Routes ]          → defines endpoints, parses path/query params
     │
     ▼
 [ Controllers ]     → handles HTTP in/out, delegates to service
     │
     ▼
 [ Services ]        → business logic, validation, raises domain exceptions
     │
     ▼
 [ Repositories ]    → data access only, no business logic
     │
     ▼
 [ Database ]        → PostgreSQL via async SQLAlchemy
```

**Rule of thumb:**
- Routes know nothing about business rules.
- Controllers know nothing about SQL.
- Services know nothing about HTTP status codes.
- Repositories know nothing about business logic.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+

### 1. Clone and set up a virtual environment

```bash
git clone <repo-url>
cd be-project-manager

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
APP_NAME="Project Manager"
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/project_manager_db

ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. Run database migrations

```bash
# Generate migration from current models
alembic revision --autogenerate -m "init"

# Apply migrations
alembic upgrade head
```

### 5. Seed the database

```bash
python -m database.seeders.runner
```

### 6. Start the server

```bash
python main.py
```

Or directly with Uvicorn:

```bash
uvicorn app.main:app --reload
```

API is now available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `APP_NAME` | No | `Project Manager` | Application name shown in docs |
| `APP_ENV` | No | `development` | `development` or `production` |
| `APP_DEBUG` | No | `true` | Enables SQL echo and debug logging |
| `APP_HOST` | No | `0.0.0.0` | Bind host |
| `APP_PORT` | No | `8000` | Bind port |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS origins |

> In `production` mode, `/docs` and `/redoc` are automatically disabled.

---

## API Reference

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns service status |

### Projects

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects` | List all projects (paginated) |
| `GET` | `/projects/{id}` | Get a project by ID |
| `POST` | `/projects` | Create a new project |
| `PATCH` | `/projects/{id}` | Partially update a project |
| `DELETE` | `/projects/{id}` | Delete a project |

#### Query Parameters — `GET /projects`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | `int` | `1` | Page number (≥ 1) |
| `size` | `int` | `20` | Items per page (1–100) |

#### Project Status Values

| Value | Description |
|---|---|
| `active` | Project is active |
| `inactive` | Project is inactive |
| `archived` | Project is archived |

#### Example Payloads

**Create project** — `POST /projects`
```json
{
  "name": "My Project",
  "description": "Optional description",
  "status": "active"
}
```

**Update project** — `PATCH /projects/{id}`
```json
{
  "status": "archived"
}
```

**Paginated response**
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

---

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "describe your change"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade <revision_id>

# Show current revision
alembic current

# Show migration history
alembic history
```

> All models must be imported in `alembic/env.py` for Alembic to detect schema changes.

---

## Adding a New Domain

Follow this checklist to add a new resource (e.g. `Task`):

1. **Model** — `app/models/task.py` — extend `BaseModel`
2. **Schema** — `app/schemas/task.py` — `TaskCreate`, `TaskUpdate`, `TaskResponse`
3. **Repository** — `app/repositories/task_repository.py` — extend `BaseRepository[Task]`
4. **Service** — `app/services/task_service.py` — business logic
5. **Controller** — `app/controllers/task_controller.py` — calls service
6. **Route** — `app/routes/task.py` — define endpoints
7. **Register route** — add `include_router(task_router)` in `app/routes/__init__.py`
8. **Register model** — import model in `alembic/env.py`
9. **Migrate** — `alembic revision --autogenerate -m "add tasks table"`

---

## Error Responses

All errors follow a consistent shape:

```json
{
  "error_code": "NOT_FOUND",
  "detail": "Project with identifier 'abc' not found."
}
```

| HTTP Status | Error Code | Trigger |
|---|---|---|
| 400 | `BAD_REQUEST` | Invalid business input |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Duplicate / constraint violation |
| 422 | `UNPROCESSABLE_ENTITY` | Pydantic validation failure (FastAPI default) |
