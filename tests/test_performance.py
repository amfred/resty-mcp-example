"""
Performance and load tests for FastAPI Pet Adoption API

Tests for performance, concurrency, and scalability.
"""

import pytest
import asyncio
import time
from typing import List
from httpx import AsyncClient


@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Performance and load test suite."""

    @pytest.mark.asyncio
    async def test_concurrent_pet_creation(self, async_client: AsyncClient):
        """Test concurrent pet creation performance."""
        pet_data = {
            "name": "Performance Test Pet",
            "species": "Dog",
            "breed": "Test Breed",
            "age": 1,
            "description": "Performance test"
        }
        
        # Create 10 pets concurrently
        start_time = time.time()
        
        tasks = [
            async_client.post("/api/v1/pets/", json=pet_data)
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All should succeed
        for response in responses:
            assert response.status_code == 201
        
        # Performance check: should complete in reasonable time
        duration = end_time - start_time
        assert duration < 5.0, f"Concurrent creation took {duration:.2f}s, expected < 5s"
        
        # Verify all pets were created
        response = await async_client.get("/api/v1/pets/")
        pets = response.json()
        assert len(pets) == 10

    @pytest.mark.asyncio
    async def test_concurrent_search_operations(self, async_client: AsyncClient):
        """Test concurrent search operations performance."""
        # Create test data
        pet_data = {
            "name": "Search Test Pet",
            "species": "Cat",
            "breed": "Test Breed",
            "age": 2
        }
        
        # Create 5 pets
        for i in range(5):
            pet_data["name"] = f"Search Test Pet {i}"
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Perform 20 concurrent searches
        start_time = time.time()
        
        tasks = [
            async_client.get("/api/v1/pets/search?species=Cat")
            for _ in range(20)
        ]
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            pets = response.json()
            assert len(pets) == 5
        
        # Performance check
        duration = end_time - start_time
        assert duration < 3.0, f"Concurrent searches took {duration:.2f}s, expected < 3s"

    @pytest.mark.asyncio
    async def test_mcp_concurrent_tool_calls(self, async_client: AsyncClient):
        """Test concurrent MCP tool calls performance."""
        # Create test data
        pet_data = {
            "name": "MCP Test Pet",
            "species": "Dog",
            "breed": "Test Breed"
        }
        await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Perform 15 concurrent MCP tool calls
        start_time = time.time()
        
        tasks = [
            async_client.post("/api/v1/mcp/", json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get_pets_summary",
                    "arguments": {}
                },
                "id": f"perf-test-{i}"
            })
            for i in range(15)
        ]
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert "result" in data
        
        # Performance check
        duration = end_time - start_time
        assert duration < 4.0, f"Concurrent MCP calls took {duration:.2f}s, expected < 4s"

    @pytest.mark.asyncio
    async def test_batch_operations_performance(self, async_client: AsyncClient):
        """Test batch operations performance."""
        # Create batch data with 20 pets
        pets_data = [
            {
                "name": f"Batch Pet {i}",
                "species": "Dog" if i % 2 == 0 else "Cat",
                "breed": f"Breed {i}",
                "age": i % 10 + 1
            }
            for i in range(20)
        ]
        
        batch_data = {"pets": pets_data}
        
        start_time = time.time()
        response = await async_client.post("/api/v1/pets/batch", json=batch_data)
        end_time = time.time()
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["created_pets"]) == 20
        
        # Performance check: batch should be faster than individual creates
        duration = end_time - start_time
        assert duration < 2.0, f"Batch creation took {duration:.2f}s, expected < 2s"

    @pytest.mark.asyncio
    async def test_database_query_performance(self, async_client: AsyncClient):
        """Test database query performance with larger datasets."""
        # Create 50 pets
        for i in range(50):
            pet_data = {
                "name": f"Perf Pet {i}",
                "species": "Dog" if i % 3 == 0 else "Cat" if i % 3 == 1 else "Bird",
                "breed": f"Breed {i % 10}",
                "age": i % 15 + 1
            }
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Test various query operations
        operations = [
            ("/api/v1/pets/", "Get all pets"),
            ("/api/v1/pets/summary", "Get summary"),
            ("/api/v1/pets/search?species=Dog", "Search by species"),
            ("/api/v1/pets/available", "Get available pets"),
            ("/api/v1/pets/species", "Get species list")
        ]
        
        for endpoint, description in operations:
            start_time = time.time()
            response = await async_client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200, f"{description} failed"
            
            duration = end_time - start_time
            assert duration < 1.0, f"{description} took {duration:.2f}s, expected < 1s"

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, async_client: AsyncClient):
        """Test memory usage stability under load."""
        # Create and delete pets in cycles to test memory stability
        for cycle in range(5):
            # Create 10 pets
            pet_ids = []
            for i in range(10):
                pet_data = {
                    "name": f"Memory Test Pet {cycle}-{i}",
                    "species": "Dog",
                    "breed": "Test Breed"
                }
                response = await async_client.post("/api/v1/pets/", json=pet_data)
                pet_ids.append(response.json()["id"])
            
            # Perform various operations
            await async_client.get("/api/v1/pets/")
            await async_client.get("/api/v1/pets/summary")
            await async_client.get("/api/v1/pets/search?species=Dog")
            
            # Delete all pets
            for pet_id in pet_ids:
                await async_client.delete(f"/api/v1/pets/{pet_id}")
            
            # Verify cleanup
            response = await async_client.get("/api/v1/pets/")
            assert len(response.json()) == 0, f"Memory test cycle {cycle}: pets not cleaned up"

    @pytest.mark.asyncio
    async def test_error_handling_performance(self, async_client: AsyncClient):
        """Test error handling doesn't impact performance."""
        # Test with various error conditions
        error_tests = [
            ("/api/v1/pets/999", "Non-existent pet"),
            ("/api/v1/pets/search?species=NonExistentSpecies", "Invalid search"),
            ("/api/v1/mcp/", {"jsonrpc": "2.0", "method": "invalid_method", "id": "test"})
        ]
        
        start_time = time.time()
        
        for endpoint, description in error_tests:
            if isinstance(endpoint, str):
                response = await async_client.get(endpoint)
                assert response.status_code in [404, 200], f"{description} error handling failed"
            else:
                response = await async_client.post("/api/v1/mcp/", json=endpoint)
                assert response.status_code in [404, 200], f"{description} error handling failed"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Error handling should be fast
        assert duration < 1.0, f"Error handling took {duration:.2f}s, expected < 1s"

    @pytest.mark.asyncio
    async def test_mixed_workload_performance(self, async_client: AsyncClient):
        """Test performance with mixed workload."""
        # Create initial data
        for i in range(10):
            pet_data = {
                "name": f"Mixed Pet {i}",
                "species": "Dog" if i % 2 == 0 else "Cat",
                "breed": f"Breed {i}",
                "age": i % 5 + 1
            }
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Mixed operations
        start_time = time.time()
        
        tasks = [
            # Read operations
            async_client.get("/api/v1/pets/"),
            async_client.get("/api/v1/pets/summary"),
            async_client.get("/api/v1/pets/search?species=Dog"),
            async_client.get("/api/v1/pets/available"),
            
            # MCP operations
            async_client.post("/api/v1/mcp/", json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": "mixed-test"
            }),
            async_client.post("/api/v1/mcp/", json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "get_pets_summary", "arguments": {}},
                "id": "mixed-test-2"
            }),
            
            # Write operations
            async_client.post("/api/v1/pets/", json={
                "name": "Mixed Workload Pet",
                "species": "Bird",
                "breed": "Canary"
            }),
            
            # Update operations
            async_client.put("/api/v1/pets/1", json={"age": 5}) if True else None,
        ]
        
        # Filter out None values
        tasks = [task for task in tasks if task is not None]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Most should succeed (some might fail due to non-existent pets)
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code < 400)
        assert success_count >= len(tasks) * 0.8, f"Only {success_count}/{len(tasks)} operations succeeded"
        
        # Performance check
        duration = end_time - start_time
        assert duration < 3.0, f"Mixed workload took {duration:.2f}s, expected < 3s"


@pytest.mark.performance
@pytest.mark.load
class TestLoadTesting:
    """Load testing for high-traffic scenarios."""

    @pytest.mark.asyncio
    async def test_high_concurrent_reads(self, async_client: AsyncClient):
        """Test high concurrent read operations."""
        # Create test data
        for i in range(20):
            pet_data = {
                "name": f"Load Test Pet {i}",
                "species": "Dog" if i % 2 == 0 else "Cat",
                "breed": f"Breed {i % 5}",
                "age": i % 10 + 1
            }
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # 50 concurrent read operations
        start_time = time.time()
        
        tasks = [
            async_client.get("/api/v1/pets/")
            for _ in range(50)
        ]
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            pets = response.json()
            assert len(pets) == 20
        
        duration = end_time - start_time
        assert duration < 5.0, f"High concurrent reads took {duration:.2f}s, expected < 5s"

    @pytest.mark.asyncio
    async def test_sustained_load(self, async_client: AsyncClient):
        """Test sustained load over time."""
        # Run operations for 30 seconds
        start_time = time.time()
        operation_count = 0
        
        while time.time() - start_time < 10:  # Reduced to 10 seconds for test speed
            # Mix of operations
            tasks = [
                async_client.get("/api/v1/pets/"),
                async_client.get("/api/v1/pets/summary"),
                async_client.post("/api/v1/pets/", json={
                    "name": f"Sustained Pet {operation_count}",
                    "species": "Dog",
                    "breed": "Test Breed"
                })
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            operation_count += len(tasks)
            
            # Brief pause to prevent overwhelming
            await asyncio.sleep(0.1)
        
        # Should have completed many operations
        assert operation_count > 50, f"Only completed {operation_count} operations in sustained load test"
        
        # Verify system is still responsive
        response = await async_client.get("/api/v1/pets/")
        assert response.status_code == 200
