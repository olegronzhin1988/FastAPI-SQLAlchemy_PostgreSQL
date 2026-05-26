# Employee-Department API

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest-brightgreen?logo=pytest)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A REST API for managing an organizational structure: departments with unlimited nesting depth and employees. Demonstrates recursive data structures, async ORM, and database schema migrations.

---

## Features

- Unlimited department hierarchy depth (adjacency list pattern)
- Recursive subtree retrieval with configurable depth
- Cascade delete: removes all child departments and their employees
- Reassign delete: moves employees to another department before deletion
- Fully async stack (asyncpg + SQLAlchemy async)
- Schema migrations via Alembic (tables are never created at app startup)
- Tests run on SQLite in-memory — no PostgreSQL needed for testing

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 15+ |
| Async driver | asyncpg |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Tests | pytest + pytest-asyncio + httpx |
| DB container | Docker |

---

## Project Structure

```
├── main.py                          # FastAPI app entry point
├── database.py                      # Engine, session, base model
├── alembic.ini                      # Alembic configuration
├── compose.yaml                     # Docker Compose for PostgreSQL
├── pytest.ini                       # pytest configuration
├── requirements.txt
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 81048bacbb65_init.py     # Initial migration
├── models/
│   └── departments_employees.py     # SQLAlchemy ORM models
├── schemas/
│   ├── departments.py               # Pydantic schemas for departments
│   └── employees.py                 # Pydantic schemas for employees
├── routers/
│   └── departments_employees.py     # API endpoints
└── tests/
    ├── conftest.py                  # Fixtures, test app setup
    ├── test_departments.py
    └── test_employees.py
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker

### 1. Clone the repository

```bash
git clone https://github.com/olegronzhin1988/FastAPI-SQLAlchemy_PostgreSQL.git
cd FastAPI-SQLAlchemy_PostgreSQL
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Create the environment file

Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

`.env.example`:
```env
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=departments
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 4. Start PostgreSQL via Docker Compose

```bash
docker compose up -d
```

### 5. Apply migrations

```bash
alembic upgrade head
```

### 6. Run the application

```bash
python main.py
```

API available at `http://127.0.0.1:8000`  
Interactive docs: `http://127.0.0.1:8000/docs`

---

## API

### Departments

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/departments/` | Create a department |
| `GET` | `/departments/{id}` | Get department with employees and subtree |
| `PATCH` | `/departments/{id}` | Update name or parent |
| `DELETE` | `/departments/{id}` | Delete department (cascade or reassign) |

#### Query parameters — GET `/departments/{id}`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `include_employees` | bool | `true` | Include employees in the response |
| `depth` | int | `1` | Subtree depth (1–5) |

#### Query parameters — DELETE `/departments/{id}`

| Parameter | Type | Description |
|---|---|---|
| `mode` | `cascade` \| `reassign` | Deletion mode |
| `reassign_to_department_id` | int | Required when `mode=reassign` |

### Employees

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/departments/employees/` | Create an employee |

---

## Request Examples

**Create a root department:**
```bash
curl -X POST http://127.0.0.1:8000/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering"}'
```
```json
{"id": 1, "name": "Engineering", "parent_id": null}
```

**Create a child department:**
```bash
curl -X POST http://127.0.0.1:8000/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Backend", "parent_id": 1}'
```

**Get department tree with depth 3:**
```bash
curl "http://127.0.0.1:8000/departments/1?depth=3&include_employees=true"
```
```json
{
  "id": 1,
  "name": "Engineering",
  "parent_id": null,
  "employees": [{"id": 5, "name": "Alice", "position": "CTO"}],
  "subdepartments": [
    {
      "id": 2,
      "name": "Backend",
      "employees": [...],
      "subdepartments": [...]
    }
  ]
}
```

**Delete a department and reassign its employees:**
```bash
curl -X DELETE "http://127.0.0.1:8000/departments/2?mode=reassign&reassign_to_department_id=1"
```

---

## Department Hierarchy

Each department stores a `parent_id` foreign key pointing back to the same table (adjacency list). Example structure:

```
Company
├── Engineering
│   ├── Backend
│   └── Frontend
└── Marketing
    └── SEO
```

---

## Migrations

Tables are created **only via Alembic**, never at application startup.

```bash
# Apply all migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back all migrations
alembic downgrade base

# Generate a new migration after changing models
alembic revision --autogenerate -m "add salary column"

# Show migration history
alembic history

# Show current revision
alembic current
```

---

## Tests

Tests use an SQLite in-memory database — no PostgreSQL required.

```bash
pip install pytest pytest-asyncio httpx aiosqlite

# Run tests
pytest tests/ -v --asyncio-mode=auto

# With coverage report
pytest tests/ -v --asyncio-mode=auto --cov=. --cov-report=term-missing
```

Coverage includes: creating and deleting departments, cascade delete, employee reassignment, and edge cases (non-existent department, invalid `parent_id`).

---

## Known Limitations / TODO

- [ ] Authentication and authorization (JWT)
- [ ] Pagination for employee lists
- [ ] Endpoints for updating and deleting employees
- [ ] GitHub Actions CI (auto-run tests on every PR)
- [ ] Load settings via `pydantic-settings` instead of hardcoding in `database.py`
