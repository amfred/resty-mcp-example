"""
MCP (Model Context Protocol) tests for FastAPI Pet Adoption API

Comprehensive tests for MCP JSON-RPC 2.0 protocol implementation.
"""

import pytest
import json
from fastapi import status
from httpx import AsyncClient


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPProtocol:
    """Test suite for MCP protocol implementation."""

    @pytest.mark.asyncio
    async def test_mcp_server_info(self, async_client: AsyncClient):
        """Test MCP server info endpoint."""
        response = await async_client.get("/api/v1/mcp/info")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "server" in data
        assert "capabilities" in data
        assert data["server"]["name"] == "Pet Adoption API"
        assert data["server"]["version"] == "2.0.0"
        assert "tools" in data["capabilities"]
        assert "resources" in data["capabilities"]
        assert "prompts" in data["capabilities"]

    @pytest.mark.asyncio
    async def test_mcp_initialize(self, async_client: AsyncClient, mcp_initialize_request):
        """Test MCP initialize method."""
        response = await async_client.post("/api/v1/mcp/", json=mcp_initialize_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == mcp_initialize_request["id"]
        assert "result" in data
        
        result = data["result"]
        assert result["protocolVersion"] == "2025-06-18"
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "Pet Adoption API"

    @pytest.mark.asyncio
    async def test_mcp_initialized_notification(self, async_client: AsyncClient):
        """Test MCP initialized notification."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data

    @pytest.mark.asyncio
    async def test_mcp_tools_list(self, async_client: AsyncClient, mcp_tools_list_request):
        """Test MCP tools/list method."""
        response = await async_client.post("/api/v1/mcp/", json=mcp_tools_list_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == mcp_tools_list_request["id"]
        assert "result" in data
        
        result = data["result"]
        assert "tools" in result
        tools = result["tools"]
        assert len(tools) >= 10
        
        # Check for expected tools
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "get_pets_summary", "search_pets", "create_pet",
            "adopt_pet_by_name", "update_pet_info", "get_valid_species"
        ]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_mcp_tools_call_get_pets_summary(self, async_client: AsyncClient, sample_pets_data):
        """Test MCP tools/call with get_pets_summary."""
        # Create some test data first
        for pet_data in sample_pets_data:
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_pets_summary",
                "arguments": {}
            },
            "id": "test-summary"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-summary"
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert result["isError"] == False
        
        # Parse the content (should be JSON string)
        content = result["content"][0]["text"]
        summary_data = json.loads(content)
        assert "summary_by_species" in summary_data
        assert "overall_totals" in summary_data

    @pytest.mark.asyncio
    async def test_mcp_tools_call_create_pet(self, async_client: AsyncClient):
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
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-create"
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert result["isError"] == False
        
        # Parse the content
        content = result["content"][0]["text"]
        pet_data = json.loads(content)
        assert pet_data["name"] == "MCP Test Pet"
        assert pet_data["species"] == "Dog"
        assert pet_data["breed"] == "Labrador"
        assert pet_data["age"] == 2

    @pytest.mark.asyncio
    async def test_mcp_tools_call_search_pets(self, async_client: AsyncClient, sample_pets_data):
        """Test MCP tools/call with search_pets."""
        # Create test data
        for pet_data in sample_pets_data:
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_pets",
                "arguments": {
                    "species": "Dog"
                }
            },
            "id": "test-search"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-search"
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert result["isError"] == False
        
        # Parse the content
        content = result["content"][0]["text"]
        search_results = json.loads(content)
        assert isinstance(search_results, list)
        assert len(search_results) == 1
        assert search_results[0]["species"] == "Dog"

    @pytest.mark.asyncio
    async def test_mcp_tools_call_adopt_pet_by_name(self, async_client: AsyncClient, sample_pets_data):
        """Test MCP tools/call with adopt_pet_by_name."""
        # Create test data
        for pet_data in sample_pets_data:
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "adopt_pet_by_name",
                "arguments": {
                    "name": "Buddy"
                }
            },
            "id": "test-adopt"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-adopt"
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert result["isError"] == False
        
        # Parse the content
        content = result["content"][0]["text"]
        adoption_result = json.loads(content)
        assert "message" in adoption_result
        assert "pet" in adoption_result
        assert "successfully adopted" in adoption_result["message"]
        assert adoption_result["pet"]["is_adopted"] == True

    @pytest.mark.asyncio
    async def test_mcp_resources_list(self, async_client: AsyncClient):
        """Test MCP resources/list method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "id": "test-resources"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-resources"
        assert "result" in data
        
        result = data["result"]
        assert "resources" in result
        resources = result["resources"]
        assert len(resources) >= 4
        
        # Check for expected resources
        resource_names = [resource["name"] for resource in resources]
        expected_resources = [
            "Pet Adoption Application Form",
            "Pet Care Guidelines",
            "Adoption Process Documentation",
            "Pet Species Information"
        ]
        for expected_resource in expected_resources:
            assert expected_resource in resource_names

    @pytest.mark.asyncio
    async def test_mcp_resources_read(self, async_client: AsyncClient):
        """Test MCP resources/read method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {
                "uri": "file://adoption-form.pdf"
            },
            "id": "test-read"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-read"
        assert "result" in data
        
        result = data["result"]
        assert "contents" in result
        assert len(result["contents"]) == 1
        assert result["contents"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_mcp_prompts_list(self, async_client: AsyncClient):
        """Test MCP prompts/list method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "prompts/list",
            "id": "test-prompts"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-prompts"
        assert "result" in data
        
        result = data["result"]
        assert "prompts" in result
        prompts = result["prompts"]
        assert len(prompts) >= 3
        
        # Check for expected prompts
        prompt_names = [prompt["name"] for prompt in prompts]
        expected_prompts = [
            "adoption_assistant",
            "pet_care_advisor",
            "species_recommender"
        ]
        for expected_prompt in expected_prompts:
            assert expected_prompt in prompt_names

    @pytest.mark.asyncio
    async def test_mcp_prompts_get(self, async_client: AsyncClient):
        """Test MCP prompts/get method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {
                "name": "adoption_assistant",
                "arguments": {
                    "pet_type": "dog",
                    "experience_level": "beginner"
                }
            },
            "id": "test-prompt"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-prompt"
        assert "result" in data
        
        result = data["result"]
        assert "description" in result
        assert "messages" in result
        assert len(result["messages"]) >= 2

    @pytest.mark.asyncio
    async def test_mcp_logging_setLevel(self, async_client: AsyncClient):
        """Test MCP logging/setLevel method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "logging/setLevel",
            "params": {
                "level": "debug"
            },
            "id": "test-logging"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-logging"
        assert "result" in data
        
        result = data["result"]
        assert "message" in result
        assert "level" in result
        assert result["level"] == "debug"

    @pytest.mark.asyncio
    async def test_mcp_invalid_method(self, async_client: AsyncClient):
        """Test MCP with invalid method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "id": "test-invalid"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-invalid"
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_mcp_invalid_jsonrpc_version(self, async_client: AsyncClient):
        """Test MCP with invalid JSON-RPC version."""
        request_data = {
            "jsonrpc": "1.0",  # Invalid version
            "method": "tools/list",
            "id": "test-invalid-jsonrpc"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32600  # Invalid Request

    @pytest.mark.asyncio
    async def test_mcp_missing_method(self, async_client: AsyncClient):
        """Test MCP with missing method."""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-missing-method"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32600  # Invalid Request

    @pytest.mark.asyncio
    async def test_mcp_tool_error_handling(self, async_client: AsyncClient):
        """Test MCP tool error handling."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_pet",
                "arguments": {
                    "name": "Test Pet"
                    # Missing required species field
                }
            },
            "id": "test-error"
        }
        
        response = await async_client.post("/api/v1/mcp/", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-error"
        assert "result" in data
        
        result = data["result"]
        assert "content" in result
        assert result["isError"] == True
        assert "Error:" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_mcp_concurrent_requests(self, async_client: AsyncClient):
        """Test MCP with concurrent requests."""
        import asyncio
        
        # Create multiple concurrent MCP requests
        requests = [
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": f"concurrent-{i}"
            }
            for i in range(5)
        ]
        
        tasks = [
            async_client.post("/api/v1/mcp/", json=request)
            for request in requests
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert "result" in data
