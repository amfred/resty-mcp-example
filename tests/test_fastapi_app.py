"""
Comprehensive FastAPI application tests

Integration tests for the complete FastAPI application including
pets endpoints, MCP protocol, and database operations.
"""

import pytest
import asyncio
import tempfile
import os
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import our FastAPI app and components
from main import app
from database import Base, get_db
from models import Pet
from schemas import PetCreate, PetUpdate


# Test database setup
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    # Use temporary file for SQLite
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    database_url = f"sqlite+aiosqlite:///{temp_db.name}"
    engine = create_async_engine(database_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()
    try:
        os.unlink(temp_db.name)
    except:
        pass


@pytest.fixture(scope="session")
async def test_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def test_db(test_session):
    """Create a fresh database session for each test."""
    # Clear existing data
    await test_session.execute("DELETE FROM pet")
    await test_session.commit()
    yield test_session


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database dependency override."""
    def override_get_db():
        return test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(test_db):
    """Create an async test client."""
    def override_get_db():
        return test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


class TestHealthAndInfo:
    """Test health check and info endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint with API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "api" in data
        assert "mcp" in data
        assert data["api"]["pets"] == "/api/v1/pets"
        assert data["api"]["mcp"] == "/api/v1/mcp"


class TestPetsEndpoints:
    """Test pets REST API endpoints."""
    
    def test_get_pets_empty(self, client):
        """Test getting pets when database is empty."""
        response = client.get("/api/v1/pets/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_pet(self, client):
        """Test creating a new pet."""
        pet_data = {
            "name": "Buddy",
            "species": "Dog",
            "breed": "Golden Retriever",
            "age": 3,
            "description": "Friendly dog"
        }
        
        response = client.post("/api/v1/pets/", json=pet_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Buddy"
        assert data["species"] == "Dog"
        assert data["breed"] == "Golden Retriever"
        assert data["age"] == 3
        assert data["is_adopted"] == False
        assert "id" in data
        assert "created_at" in data
    
    def test_create_pet_validation_error(self, client):
        """Test pet creation with validation errors."""
        # Missing required fields
        pet_data = {"name": "Buddy"}  # Missing species
        
        response = client.post("/api/v1/pets/", json=pet_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_pet_by_id(self, client):
        """Test getting a pet by ID."""
        # First create a pet
        pet_data = {"name": "Whiskers", "species": "Cat"}
        create_response = client.post("/api/v1/pets/", json=pet_data)
        pet_id = create_response.json()["id"]
        
        # Then get it by ID
        response = client.get(f"/api/v1/pets/{pet_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Whiskers"
        assert data["species"] == "Cat"
        assert data["id"] == pet_id
    
    def test_get_pet_not_found(self, client):
        """Test getting a non-existent pet."""
        response = client.get("/api/v1/pets/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_pet(self, client):
        """Test updating a pet."""
        # Create a pet
        pet_data = {"name": "Rex", "species": "Dog", "age": 2}
        create_response = client.post("/api/v1/pets/", json=pet_data)
        pet_id = create_response.json()["id"]
        
        # Update the pet
        update_data = {"age": 3, "description": "Updated description"}
        response = client.put(f"/api/v1/pets/{pet_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["age"] == 3
        assert data["description"] == "Updated description"
        assert data["name"] == "Rex"  # Unchanged
    
    def test_delete_pet(self, client):
        """Test deleting a pet."""
        # Create a pet
        pet_data = {"name": "Fluffy", "species": "Cat"}
        create_response = client.post("/api/v1/pets/", json=pet_data)
        pet_id = create_response.json()["id"]
        
        # Delete the pet
        response = client.delete(f"/api/v1/pets/{pet_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/pets/{pet_id}")
        assert get_response.status_code == 404
    
    def test_adopt_pet_by_id(self, client):
        """Test adopting a pet by ID."""
        # Create a pet
        pet_data = {"name": "Max", "species": "Dog"}
        create_response = client.post("/api/v1/pets/", json=pet_data)
        pet_id = create_response.json()["id"]
        
        # Adopt the pet
        response = client.put(f"/api/v1/pets/{pet_id}/adopt")
        assert response.status_code == 200
        
        data = response.json()
        assert "successfully adopted" in data["message"]
        assert data["pet"]["is_adopted"] == True
    
    def test_search_pets(self, client):
        """Test searching pets with filters."""
        # Create test pets
        pets_data = [
            {"name": "Dog1", "species": "Dog", "breed": "Labrador", "age": 2},
            {"name": "Cat1", "species": "Cat", "breed": "Persian", "age": 1},
            {"name": "Dog2", "species": "Dog", "breed": "Golden Retriever", "age": 5}
        ]
        
        for pet_data in pets_data:
            client.post("/api/v1/pets/", json=pet_data)
        
        # Search by species
        response = client.get("/api/v1/pets/search?species=Dog")
        assert response.status_code == 200
        dogs = response.json()
        assert len(dogs) == 2
        assert all(pet["species"] == "Dog" for pet in dogs)
        
        # Search by breed
        response = client.get("/api/v1/pets/search?breed=Persian")
        assert response.status_code == 200
        persians = response.json()
        assert len(persians) == 1
        assert persians[0]["breed"] == "Persian"
    
    def test_get_pets_summary(self, client):
        """Test getting pets summary statistics."""
        # Create test pets
        pets_data = [
            {"name": "Dog1", "species": "Dog"},
            {"name": "Cat1", "species": "Cat"},
            {"name": "Dog2", "species": "Dog"}
        ]
        
        for pet_data in pets_data:
            client.post("/api/v1/pets/", json=pet_data)
        
        # Adopt one pet
        pets = client.get("/api/v1/pets/").json()
        client.put(f"/api/v1/pets/{pets[0]['id']}/adopt")
        
        # Get summary
        response = client.get("/api/v1/pets/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "species_stats" in data
        assert "overall_totals" in data
        assert data["overall_totals"]["total_pets"] == 3
        assert data["overall_totals"]["adopted_pets"] == 1
        assert data["overall_totals"]["available_pets"] == 2


class TestMCPEndpoints:
    """Test MCP (Model Context Protocol) endpoints."""
    
    def test_mcp_server_info(self, client):
        """Test MCP server info endpoint."""
        response = client.get("/api/v1/mcp/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "server" in data
        assert "capabilities" in data
        assert data["server"]["name"] == "Pet Adoption API"
        assert "tools" in data["capabilities"]
        assert "resources" in data["capabilities"]
        assert "prompts" in data["capabilities"]
    
    def test_mcp_initialize(self, client):
        """Test MCP initialize method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "Test Client",
                    "version": "1.0.0"
                }
            },
            "id": "test-123"
        }
        
        response = client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-123"
        assert "result" in data
        
        result = data["result"]
        assert result["protocolVersion"] == "2025-06-18"
        assert "capabilities" in result
        assert "serverInfo" in result
    
    def test_mcp_tools_list(self, client):
        """Test MCP tools/list method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "test-456"
        }
        
        response = client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-456"
        assert "result" in data
        
        result = data["result"]
        assert "tools" in result
        tools = result["tools"]
        assert len(tools) > 0
        
        # Check for expected tools
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["get_pets_summary", "search_pets", "create_pet"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_mcp_tools_call_get_pets_summary(self, client):
        """Test MCP tools/call with get_pets_summary."""
        # Create some test data first
        pets_data = [
            {"name": "Dog1", "species": "Dog"},
            {"name": "Cat1", "species": "Cat"}
        ]
        for pet_data in pets_data:
            client.post("/api/v1/pets/", json=pet_data)
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_pets_summary",
                "arguments": {}
            },
            "id": "test-789"
        }
        
        response = client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-789"
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert result["isError"] == False
        
        # Parse the content (should be JSON string)
        content = result["content"][0]["text"]
        import json
        summary_data = json.loads(content)
        assert "summary_by_species" in summary_data
        assert "overall_totals" in summary_data
    
    def test_mcp_tools_call_create_pet(self, client):
        """Test MCP tools/call with create_pet."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_pet",
                "arguments": {
                    "name": "MCP Test Pet",
                    "species": "Dog",
                    "breed": "Labrador",
                    "age": 2
                }
            },
            "id": "test-create"
        }
        
        response = client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-create"
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert result["isError"] == False
        
        # Parse the content
        content = result["content"][0]["text"]
        import json
        pet_data = json.loads(content)
        assert pet_data["name"] == "MCP Test Pet"
        assert pet_data["species"] == "Dog"
        assert pet_data["breed"] == "Labrador"
        assert pet_data["age"] == 2
    
    def test_mcp_invalid_method(self, client):
        """Test MCP with invalid method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "id": "test-invalid"
        }
        
        response = client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == 404
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-invalid"
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found
    
    def test_mcp_invalid_jsonrpc(self, client):
        """Test MCP with invalid JSON-RPC version."""
        request_data = {
            "jsonrpc": "1.0",  # Invalid version
            "method": "tools/list",
            "id": "test-invalid-jsonrpc"
        }
        
        response = client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32600  # Invalid Request


class TestAsyncOperations:
    """Test async operations and performance."""
    
    @pytest.mark.asyncio
    async def test_async_pet_operations(self, async_client):
        """Test async pet operations."""
        # Create a pet
        pet_data = {"name": "Async Pet", "species": "Cat"}
        response = await async_client.post("/api/v1/pets/", json=pet_data)
        assert response.status_code == 201
        
        pet_id = response.json()["id"]
        
        # Get the pet
        response = await async_client.get(f"/api/v1/pets/{pet_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Async Pet"
        
        # Update the pet
        update_data = {"age": 3}
        response = await async_client.put(f"/api/v1/pets/{pet_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["age"] == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        """Test handling concurrent requests."""
        # Create multiple pets concurrently
        pet_data_list = [
            {"name": f"Pet {i}", "species": "Dog"}
            for i in range(5)
        ]
        
        tasks = [
            async_client.post("/api/v1/pets/", json=pet_data)
            for pet_data in pet_data_list
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 201
        
        # Verify all pets were created
        response = await async_client.get("/api/v1/pets/")
        assert response.status_code == 200
        pets = response.json()
        assert len(pets) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
