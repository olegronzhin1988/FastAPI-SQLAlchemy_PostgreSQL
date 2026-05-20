"""
Common fixtures for all tests.
Sets up the test database and HTTP client.
"""

import pytest
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from sqlite3 import Connection as SQLite3Connection

from main import app
from database import Model, get_db


# Test database - SQLite in-memory (fast and clean)
# No PostgreSQL installation required
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# Test session factory
TestingSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
    class_=AsyncSession
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture for a clean database before each test.
    Creates tables → yields session → drops tables after test.
    """
    # Enable foreign key support for SQLite
    @event.listens_for(test_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Create all tables based on models
    async with test_engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

    # Create session and pass to test
    async with TestingSessionLocal() as session:
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client fixture with test database.
    Overrides the get_db dependency to use the test session.
    """

    # Override the dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create client with ASGI transport for FastAPI testing
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up the override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_department_data() -> Dict[str, Any]:
    """Test data for creating a department"""
    return {"name": "Sales Department", "parent_id": None}


@pytest.fixture
def sample_department_child_data() -> Dict[str, Any]:
    """Test data for creating a child department"""
    return {"name": "IT Department"}


@pytest.fixture
def sample_employee_data() -> Dict[str, Any]:
    """Test data for creating an employee"""
    return {
        "full_name": "John Doe",
        "position": "Manager",
        "hired_at": None
    }


@pytest.fixture
async def create_test_department(
    client: AsyncClient,
    sample_department_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates a test department and returns its data.
    Used as a dependency in other tests.
    """
    response = await client.post("/departments/", json=sample_department_data)
    return response.json()


@pytest.fixture
async def create_test_department_with_child(
    client: AsyncClient,
    create_test_department: Dict[str, Any],
    sample_department_child_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates a test department with a child department.
    """
    child_data = {
        **sample_department_child_data,
        "parent_id": create_test_department["id"]
    }
    child_response = await client.post("/departments/", json=child_data)

    return {
        "parent": create_test_department,
        "child": child_response.json()
    }


@pytest.fixture
async def create_test_employee(
    client: AsyncClient,
    create_test_department: Dict[str, Any],
    sample_employee_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates a test employee and returns its data.
    """
    employee_data = {
        **sample_employee_data,
        "department_id": create_test_department["id"]
    }
    response = await client.post("/departments/employees/", json=employee_data)
    return response.json()