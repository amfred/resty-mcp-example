"""
Pytest configuration and shared fixtures for FastAPI Pet Adoption API tests

This module provides common fixtures and configuration for all test modules.
"""

import pytest
import asyncio
import tempfile
import os
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import our FastAPI app and components
from main import app
from database import Base, get_db
from models import Pet


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine for the session."""
    # Use temporary file for SQLite
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    database_url = f"sqlite+aiosqlite:///{temp_db.name}"
    engine = create_async_engine(database_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine, temp_db.name
    
    # Cleanup
    await engine.dispose()
    try:
        os.unlink(temp_db.name)
    except:
        pass


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    engine, temp_db_path = test_engine
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Clear existing data
        await session.execute("DELETE FROM pet")
        await session.commit()
        yield session


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        return test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    def override_get_db():
        return test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pet_data():
    """Sample pet data for testing."""
    return {
        "name": "Buddy",
        "species": "Dog",
        "breed": "Golden Retriever",
        "age": 3,
        "description": "Friendly and energetic dog"
    }


@pytest.fixture
def sample_pets_data():
    """Sample multiple pets data for testing."""
    return [
        {
            "name": "Buddy",
            "species": "Dog",
            "breed": "Golden Retriever",
            "age": 3,
            "description": "Friendly dog"
        },
        {
            "name": "Whiskers",
            "species": "Cat",
            "breed": "Persian",
            "age": 2,
            "description": "Calm cat"
        },
        {
            "name": "Tweety",
            "species": "Bird",
            "breed": "Canary",
            "age": 1,
            "description": "Singing bird"
        }
    ]


@pytest.fixture
def mcp_request_template():
    """Template for MCP JSON-RPC requests."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request"
    }


@pytest.fixture
def mcp_initialize_request(mcp_request_template):
    """MCP initialize request for testing."""
    return {
        **mcp_request_template,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "Test Client",
                "version": "1.0.0"
            }
        }
    }


@pytest.fixture
def mcp_tools_list_request(mcp_request_template):
    """MCP tools/list request for testing."""
    return {
        **mcp_request_template,
        "method": "tools/list"
    }


@pytest.fixture
def mcp_tool_call_request(mcp_request_template):
    """MCP tools/call request template for testing."""
    return {
        **mcp_request_template,
        "method": "tools/call",
        "params": {
            "name": "get_pets_summary",
            "arguments": {}
        }
    }


# Pytest markers for test categorization
pytestmark = [
    pytest.mark.asyncio,
]
