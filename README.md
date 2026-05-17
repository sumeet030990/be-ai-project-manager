# AI Project Manager — Backend API

A production-ready REST API built with **FastAPI**, following an **n-tier architecture** (Routes → Controllers → Services → Repositories) backed by **PostgreSQL** via async SQLAlchemy. Integrates with **JIRA** for bidirectional work-item sync and supports **multiple AI providers** (Claude, OpenAI, Groq, DeepSeek) configured per project.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.136.1 |
| Server | Uvicorn 0.46.0 |
| Validation | Pydantic 2.13.3 |
| ORM | SQLAlchemy 2.0.49 (async) |
| Migrations | Alembic 1.18.4 |
| Database Driver | asyncpg (PostgreSQL) |
| Config | pydantic-settings 2.14.0 |
| AI — Groq | groq SDK |
| AI — Anthropic | anthropic SDK |
| AI — OpenAI / DeepSeek | openai SDK |
| Encryption | cryptography (Fernet/AES) |
| HTTP Client | httpx |

---

## Project Structure

```
be-ai-project-manager/
├── main.py                              # Uvicorn entrypoint
├── requirements.txt
├── .env / .env.example
├── alembic.ini
├── alembic/
│   ├── env.py                           # Async Alembic configuration
│   └── versions/                        # Migration history
├── app/
│   ├── main.py                          # FastAPI app factory (CORS, middleware, exception handlers)
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings — reads from .env
│   │   ├── database.py                  # Async engine + session factory
│   │   ├── dependencies.py              # Annotated DBSession injectable type
│   │   ├── exceptions.py                # AppException hierarchy + global handler
│   │   ├── security.py                  # bcrypt password hashing
│   │   ├── encryption.py                # Fernet AES encrypt / decrypt / mask for API keys
│   │   ├── ai_client.py                 # get_project_ai_client() — resolves provider from DB
│   │   └── ai/
│   │       ├── base.py                  # BaseAIClient ABC + ToolCallResult dataclass
│   │       ├── factory.py               # get_ai_client_for_provider(provider, key, model)
│   │       ├── groq_client.py           # Groq / Llama (with XML fallback handling)
│   │       ├── claude_client.py         # Anthropic Claude (OpenAI tool format → Anthropic format)
│   │       ├── openai_client.py         # OpenAI
│   │       └── deepseek_client.py       # DeepSeek (OpenAI-compatible)
│   ├── controllers/                     # HTTP plumbing — calls service, returns response
│   ├── services/                        # Business logic, AI calls, JIRA integration
│   │   ├── story_service.py             # Story CRUD + AI generate/refine + JIRA sync
│   │   ├── test_case_service.py         # Test case CRUD + AI generation
│   │   ├── jira_service.py              # JIRA REST API client (ADF format, epic/story/user sync)
│   │   └── project_ai_config_service.py # AI provider config management
│   ├── repositories/                    # Data access only, no business logic
│   └── schemas/                         # Pydantic request / response models
├── routes/
│   ├── __init__.py                      # api_router aggregator
│   ├── company.py
│   ├── user.py
│   ├── role.py
│   ├── project.py
│   ├── project_tech_stack.py
│   ├── project_plugin.py
│   ├── project_ai_config.py             # AI provider config CRUD
│   ├── module.py
│   ├── story.py                         # Story CRUD + AI + JIRA
│   ├── test_case.py                     # Test case CRUD + AI
│   ├── prompt.py
│   └── jira.py                          # JIRA user sync + issue type lookup
└── database/
    ├── models/                          # SQLAlchemy ORM models
    └── seeders/                         # Seed data (roles, companies, users, projects, stacks)
```

---

## Architecture

```
HTTP Request
     │
     ▼
 [ Routes ]           → endpoints, path/query params
     │
     ▼
 [ Controllers ]      → HTTP in/out, delegates to service
     │
     ▼
 [ Services ]         → business logic, AI calls, JIRA calls
     │
     ▼
 [ Repositories ]     → SQL queries only
     │
     ▼
 [ Database ]         → PostgreSQL (async SQLAlchemy)
```

**Multi-AI Provider Flow:**

```
Service calls get_project_ai_client(project_id, session)
     │
     ├── ProjectAIConfig found (is_default=True)?
     │     └── decrypt API key → get_ai_client_for_provider(provider, key, model)
     │           ├── "claude"    → ClaudeAIClient
     │           ├── "openai"    → OpenAIAIClient
     │           ├── "groq"      → GroqAIClient
     │           └── "deepseek"  → DeepSeekAIClient
     │
     └── No config set → fallback to env GROQ_API_KEY
```

All providers share the `BaseAIClient` interface: `chat_with_tools(messages, tools, tool_choice) → ToolCallResult(tool_name, arguments)`. Tool definitions use OpenAI format; the Claude client converts internally.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+

### 1. Clone and set up a virtual environment

```bash
git clone <repo-url>
cd be-ai-project-manager

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

Edit `.env` and fill in your values (see [Environment Variables](#environment-variables) below).

#### Generate the encryption key

AI provider API keys are stored AES-encrypted in the database. You must generate a Fernet key once and add it to `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output into `.env` as:

```env
ENCRYPTION_KEY=<paste output here>
```

> Keep this key safe. If it changes, all stored AI config API keys become unreadable.

### 4. Run database migrations

```bash
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

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs` (disabled in production)

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | `postgresql+asyncpg://user:pass@host:5432/db` |
| `ENCRYPTION_KEY` | Yes | — | Fernet key for encrypting AI provider API keys |
| `GROQ_API_KEY` | No | — | Fallback AI key when no project-level config is set |
| `JIRA_BASE_URL` | No | — | e.g. `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | No | — | Atlassian account email |
| `JIRA_API_KEY` | No | — | Atlassian API token |
| `JIRA_ISSUE_TYPE` | No | `Story` | Issue type for created stories |
| `JIRA_STORY_POINTS_FIELD` | No | `customfield_10016` | Custom field ID for story points |
| `APP_NAME` | No | `Project Manager` | Shown in API docs |
| `APP_ENV` | No | `development` | `development` or `production` |
| `APP_DEBUG` | No | `true` | Enables SQL echo |
| `APP_HOST` | No | `0.0.0.0` | Bind host |
| `APP_PORT` | No | `8000` | Bind port |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS origins |

> In `production` mode, `/docs` and `/redoc` are automatically disabled.

---

## AI Provider Configuration

AI providers are configured **per project** via the `project_ai_configs` table. This allows each project to use a different provider, model, and API key.

### Setting up an AI provider for a project

```http
POST /projects/{project_id}/ai-configs
Content-Type: application/json

{
  "provider": "claude",
  "api_key": "sk-ant-...",
  "model_name": "claude-sonnet-4-6",
  "is_default": true
}
```

- `provider`: `claude` | `openai` | `groq` | `deepseek` | `other`
- `api_key`: plaintext — encrypted with Fernet before storage
- `is_default`: only one config per project can be default; setting this automatically unsets the previous default
- API responses always show `api_key_masked` (`****last8chars`) — the plaintext key is never returned

### Provider default models

| Provider | Suggested model |
|---|---|
| `claude` | `claude-sonnet-4-6` |
| `openai` | `gpt-4o` |
| `groq` | `llama-3.3-70b-versatile` |
| `deepseek` | `deepseek-chat` |

### Fallback behaviour

If no AI config with `is_default=true` exists for a project, the system falls back to the server-level `GROQ_API_KEY` environment variable with `llama-3.3-70b-versatile`.

---

## API Reference

All list endpoints return a paginated envelope:

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### Roles

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/roles` | List all roles |
| `GET` | `/roles/{id}` | Get a role |

### Companies

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/companies` | List companies |
| `GET` | `/companies/{id}` | Get a company |
| `POST` | `/companies` | Create company |
| `PATCH` | `/companies/{id}` | Update company |
| `DELETE` | `/companies/{id}` | Delete company |

### Users

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users` | List users |
| `GET` | `/users/{id}` | Get a user |
| `POST` | `/users` | Create user |
| `PATCH` | `/users/{id}` | Update user |
| `DELETE` | `/users/{id}` | Delete user |
| `GET` | `/users/{id}/projects` | List user's projects |

### Projects

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects` | List projects (filter: `company_id`) |
| `GET` | `/projects/{id}` | Get a project |
| `POST` | `/projects` | Create project |
| `PATCH` | `/projects/{id}` | Update project |
| `DELETE` | `/projects/{id}` | Delete project |
| `GET` | `/projects/{id}/users` | List project team members |
| `POST` | `/projects/{id}/users` | Add users to project |
| `DELETE` | `/projects/{id}/users/{uid}` | Remove user from project |

### Project AI Configs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects/{id}/ai-configs` | List AI configs for project |
| `GET` | `/projects/{id}/ai-configs/{cid}` | Get an AI config |
| `POST` | `/projects/{id}/ai-configs` | Add AI provider config |
| `PATCH` | `/projects/{id}/ai-configs/{cid}` | Update config (rotate key, change model, set default) |
| `DELETE` | `/projects/{id}/ai-configs/{cid}` | Delete config |

### Tech Stacks & Plugins

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects/{id}/tech-stacks` | List tech stacks |
| `POST` | `/projects/{id}/tech-stacks` | Add tech stack |
| `GET` | `/projects/{id}/tech-stacks/{sid}` | Get tech stack |
| `PATCH` | `/projects/{id}/tech-stacks/{sid}` | Update tech stack |
| `DELETE` | `/projects/{id}/tech-stacks/{sid}` | Delete tech stack |
| `GET` | `/projects/{id}/tech-stacks/{sid}/plugins` | List plugins for a stack |
| `POST` | `/projects/{id}/plugins` | Add plugin (body: `tech_stack_id`) |
| `GET` | `/projects/{id}/plugins/{pid}` | Get plugin |
| `PATCH` | `/projects/{id}/plugins/{pid}` | Update plugin |
| `DELETE` | `/projects/{id}/plugins/{pid}` | Delete plugin |

### Modules

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects/{pid}/modules` | List modules |
| `GET` | `/projects/{pid}/modules/{mid}` | Get module |
| `POST` | `/projects/{pid}/modules` | Create module |
| `PATCH` | `/projects/{pid}/modules/{mid}` | Update module |
| `DELETE` | `/projects/{pid}/modules/{mid}` | Delete module |

### Stories

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/modules/{mid}/stories` | List stories |
| `GET` | `/modules/{mid}/stories/{sid}` | Get story |
| `POST` | `/modules/{mid}/stories` | Create story |
| `PATCH` | `/modules/{mid}/stories/{sid}` | Update story |
| `DELETE` | `/modules/{mid}/stories/{sid}` | Delete story |
| `POST` | `/projects/{pid}/modules/{mid}/generate-stories` | **AI** — generate stories from module description |
| `POST` | `/modules/{mid}/stories/{sid}/refine` | **AI** — enrich story with business rules, ACs, file refs |

### Story JIRA Sync

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/modules/{mid}/stories/jira/sync` | Pull all JIRA issues into module as stories |
| `POST` | `/modules/{mid}/stories/{sid}/jira` | Push story to JIRA (creates Epic if needed) |
| `PUT` | `/modules/{mid}/stories/{sid}/jira` | Update existing JIRA issue |
| `POST` | `/modules/{mid}/stories/{sid}/jira/pull` | Pull latest from JIRA into story |
| `DELETE` | `/modules/{mid}/stories/{sid}/jira` | Delete from JIRA and unlink |

### Test Cases

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/modules/{mid}/stories/{sid}/test-cases` | List test cases |
| `GET` | `/modules/{mid}/stories/{sid}/test-cases/{tcid}` | Get test case |
| `POST` | `/modules/{mid}/stories/{sid}/test-cases` | Create test case |
| `PATCH` | `/modules/{mid}/stories/{sid}/test-cases/{tcid}` | Update test case |
| `DELETE` | `/modules/{mid}/stories/{sid}/test-cases/{tcid}` | Delete test case |
| `POST` | `/modules/{mid}/stories/{sid}/test-cases/generate` | **AI** — generate positive + negative test cases |

### Prompts

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/modules/{mid}/stories/{sid}/prompts` | List saved prompts |
| `POST` | `/modules/{mid}/stories/{sid}/prompts` | Save a prompt |

### JIRA Utilities

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/jira/users/preview` | Preview JIRA users with local match status |
| `POST` | `/jira/users/sync` | Link JIRA accounts to local users |
| `GET` | `/jira/issue-types` | List available JIRA issue types |

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade <revision_id>

# Create a new migration from model changes
alembic revision --autogenerate -m "describe your change"

# Show current revision
alembic current

# Show full migration history
alembic history
```

### Migration history

| Revision | Description |
|---|---|
| `0503944248d7` | Initial schema (companies, roles, users, projects, project_users) |
| `a2b3c4d5e6f7` | Add `jira_issue_key` to stories |
| `c4d5e6f7g8h9` | Add `test_cases` table |
| `e6f7g8h9i0j1` | Add `prompts` table |
| `f7g8h9i0j1k2` | Add `jira_project_key` to projects |
| `g8h9i0j1k2l3` | Add `priority` to modules and stories |
| `h9i0j1k2l3m4` | Add `jira_account_id` to users |
| `i0j1k2l3m4n5` | Add `assignee_id` to stories |
| `j1k2l3m4n5o6` | Add `parent_id` to stories (later removed) |
| `k2l3m4n5o6p7` | Add `jira_epic_key` to modules, drop `parent_id` from stories |
| `l3m4n5o6p7q8` | Add `project_ai_configs` table |

---

## Data Model Overview

```
Company
  └── Projects
        ├── ProjectUsers       (team members)
        ├── ProjectTechStacks  (React, FastAPI, …)
        │     └── ProjectPlugins (npm/pip packages)
        ├── ProjectAIConfigs   (per-project AI provider: provider, encrypted key, model)
        └── Modules            (≈ Jira Epic — jira_epic_key)
              └── Stories      (≈ Jira Story — jira_issue_key, is_ai_generated)
                    ├── TestCases  (positive / negative — is_ai_generated)
                    └── Prompts    (saved AI prompts for code generation)
```

---

## Error Responses

All errors follow a consistent shape:

```json
{
  "error_code": "NOT_FOUND",
  "detail": "Story with identifier 'abc' not found."
}
```

| HTTP Status | Error Code | Trigger |
|---|---|---|
| 400 | `BAD_REQUEST` | Invalid business input |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Duplicate or constraint violation |
| 422 | `UNPROCESSABLE_ENTITY` | Pydantic validation failure |
| 503 | `SERVICE_UNAVAILABLE` | AI provider or JIRA unreachable |

---

## Adding a New Domain

Follow this checklist to add a new resource:

1. **Model** — `database/models/resource.py` — extend `BaseModel`
2. **Register model** — import in `database/models/__init__.py`
3. **Schema** — `app/schemas/resource.py` — `ResourceCreate`, `ResourceUpdate`, `ResourceResponse`
4. **Repository** — `app/repositories/resource_repository.py` — extend `BaseRepository[Resource]`
5. **Service** — `app/services/resource_service.py` — business logic
6. **Controller** — `app/controllers/resource_controller.py` — HTTP plumbing
7. **Route** — `routes/resource.py` — define endpoints
8. **Register route** — add `include_router(resource_router)` in `routes/__init__.py`
9. **Migrate** — `alembic revision --autogenerate -m "add resource table" && alembic upgrade head`
