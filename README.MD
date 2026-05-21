# Employee-Department API

A RESTful API for managing organizational structure — departments and employees. Built with FastAPI and SQLAlchemy 2.0, using PostgreSQL as the database and Alembic for schema migrations.

---

## Tech Stack

- **FastAPI** — web framework
- **SQLAlchemy 2.0** — ORM with async support
- **PostgreSQL** — database
- **asyncpg** — async PostgreSQL driver
- **Alembic** — database migrations
- **Pydantic v2** — data validation and serialization
- **Docker** — database container

---

## Project Structure

```
├── main.py                          # FastAPI app entry point
├── database.py                      # Database engine, session, base model
├── alembic.ini                      # Alembic configuration
├── migrations/                      # Alembic migrations folder
│   ├── env.py
│   └── versions/
│       └── 81048bacbb65_init.py     # Initial migration (departments + employees)
├── models/
│   └── departments_employees.py     # SQLAlchemy ORM models
├── schemas/
│   ├── departments.py               # Pydantic schemas for departments
│   └── employees.py                 # Pydantic schemas for employees
├── routers/
│   └── departments_employees.py     # API endpoints
└── tests/
    ├── conftest.py                   # Shared fixtures, models, app
    ├── test_departments.py           # Department endpoint tests
    └── test_employees.py             # Employee endpoint tests
```

---

## Features

- Create, read, and delete departments
- Self-referential parent-child department hierarchy (adjacency list)
- Recursive department tree with configurable depth
- Create employees and assign them to departments
- Delete department with cascade (removes all children and employees)
- Delete department with reassign (moves employees to another department before deleting)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy asyncpg alembic psycopg2-binary pydantic
```

### 3. Start PostgreSQL via Docker

```bash
docker run --name departments-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -e POSTGRES_DB=departments \
  -p 5432:5432 \
  -d postgres
```

### 4. Configure database URL

In `database.py`:
```python
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/departments"
```

In `alembic.ini`:
```ini
sqlalchemy.url = postgresql+psycopg2://user:pass@localhost:5432/departments
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the application

```bash
python main.py
```

API will be available at `http://127.0.0.1:8000`.
Interactive docs at `http://127.0.0.1:8000/docs`.

---

## API Endpoints

### Departments

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/departments/` | Create a new department |
| `GET` | `/departments/{id}` | Get department with employees and subdepartments |
| `PATCH` | `/departments/{id}` | Update department name or parent |
| `DELETE` | `/departments/{id}` | Delete department (cascade or reassign) |

#### GET `/departments/{id}` query parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_employees` | bool | `true` | Include employees in response |
| `depth` | int | `1` | Depth of subdepartment tree (1–5) |

#### DELETE `/departments/{id}` query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `mode` | `cascade` \| `reassign` | Delete mode |
| `reassign_to_department_id` | int | Required when mode is `reassign` |

### Employees

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/departments/employees/` | Create a new employee |

---

## Database Migrations

Migrations are managed by Alembic. Tables are **not** created automatically on app startup — always use Alembic.

```bash
# Apply all migrations
alembic upgrade head

# Roll back all migrations
alembic downgrade base

# Roll back one step
alembic downgrade -1

# View migration history
alembic history

# Check current migration
alembic current

# Generate a new migration after model changes
alembic revision --autogenerate -m "description"
```

---

## Running Tests

Tests use SQLite in-memory database — no PostgreSQL required.

```bash
pip install pytest pytest-asyncio httpx aiosqlite
pytest tests/ -v --asyncio-mode=auto
```

---

## Department Tree Example

A department can have a parent and multiple children, forming a hierarchy:

```
Company
├── Engineering
│   ├── Backend
│   └── Frontend
└── Marketing
    └── SEO
```

Each department stores its `parent_id` as a foreign key referencing the same table (adjacency list pattern).
