"""
Pets API endpoint tests for FastAPI Pet Adoption API

Comprehensive tests for all pets-related REST API endpoints.
"""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.pets
class TestPetsAPI:
    """Test suite for pets REST API endpoints."""

    @pytest.mark.asyncio
    async def test_get_pets_empty(self, async_client: AsyncClient):
        """Test getting pets when database is empty."""
        response = await async_client.get("/api/v1/pets/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_pet(self, async_client: AsyncClient, sample_pet_data):
        """Test creating a new pet."""
        response = await async_client.post("/api/v1/pets/", json=sample_pet_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == sample_pet_data["name"]
        assert data["species"] == sample_pet_data["species"]
        assert data["breed"] == sample_pet_data["breed"]
        assert data["age"] == sample_pet_data["age"]
        assert data["is_adopted"] == False
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_pet_validation_error(self, async_client: AsyncClient):
        """Test pet creation with validation errors."""
        # Missing required fields
        pet_data = {"name": "Buddy"}  # Missing species
        
        response = await async_client.post("/api/v1/pets/", json=pet_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_pet_by_id(self, async_client: AsyncClient, sample_pet_data):
        """Test getting a pet by ID."""
        # First create a pet
        create_response = await async_client.post("/api/v1/pets/", json=sample_pet_data)
        pet_id = create_response.json()["id"]
        
        # Then get it by ID
        response = await async_client.get(f"/api/v1/pets/{pet_id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == sample_pet_data["name"]
        assert data["species"] == sample_pet_data["species"]
        assert data["id"] == pet_id

    @pytest.mark.asyncio
    async def test_get_pet_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent pet."""
        response = await async_client.get("/api/v1/pets/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_pet(self, async_client: AsyncClient, sample_pet_data):
        """Test updating a pet."""
        # Create a pet
        create_response = await async_client.post("/api/v1/pets/", json=sample_pet_data)
        pet_id = create_response.json()["id"]
        
        # Update the pet
        update_data = {"age": 4, "description": "Updated description"}
        response = await async_client.put(f"/api/v1/pets/{pet_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["age"] == 4
        assert data["description"] == "Updated description"
        assert data["name"] == sample_pet_data["name"]  # Unchanged

    @pytest.mark.asyncio
    async def test_delete_pet(self, async_client: AsyncClient, sample_pet_data):
        """Test deleting a pet."""
        # Create a pet
        create_response = await async_client.post("/api/v1/pets/", json=sample_pet_data)
        pet_id = create_response.json()["id"]
        
        # Delete the pet
        response = await async_client.delete(f"/api/v1/pets/{pet_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        get_response = await async_client.get(f"/api/v1/pets/{pet_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_adopt_pet_by_id(self, async_client: AsyncClient, sample_pet_data):
        """Test adopting a pet by ID."""
        # Create a pet
        create_response = await async_client.post("/api/v1/pets/", json=sample_pet_data)
        pet_id = create_response.json()["id"]
        
        # Adopt the pet
        response = await async_client.put(f"/api/v1/pets/{pet_id}/adopt")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "successfully adopted" in data["message"]
        assert data["pet"]["is_adopted"] == True

    @pytest.mark.asyncio
    async def test_adopt_pet_by_name(self, async_client: AsyncClient, sample_pet_data):
        """Test adopting a pet by name."""
        # Create a pet
        await async_client.post("/api/v1/pets/", json=sample_pet_data)
        
        # Adopt the pet by name
        response = await async_client.put("/api/v1/pets/adopt?name=Buddy")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "successfully adopted" in data["message"]
        assert data["pet"]["is_adopted"] == True

    @pytest.mark.asyncio
    async def test_search_pets(self, async_client: AsyncClient, sample_pets_data):
        """Test searching pets with filters."""
        # Create test pets
        for pet_data in sample_pets_data:
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Search by species
        response = await async_client.get("/api/v1/pets/search?species=Dog")
        assert response.status_code == status.HTTP_200_OK
        dogs = response.json()
        assert len(dogs) == 1
        assert dogs[0]["species"] == "Dog"
        
        # Search by breed
        response = await async_client.get("/api/v1/pets/search?breed=Persian")
        assert response.status_code == status.HTTP_200_OK
        persians = response.json()
        assert len(persians) == 1
        assert persians[0]["breed"] == "Persian"

    @pytest.mark.asyncio
    async def test_search_pets_available_only(self, async_client: AsyncClient, sample_pets_data):
        """Test searching for available pets only."""
        # Create test pets
        for pet_data in sample_pets_data:
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Adopt one pet
        pets = await async_client.get("/api/v1/pets/")
        pet_id = pets.json()[0]["id"]
        await async_client.put(f"/api/v1/pets/{pet_id}/adopt")
        
        # Search for available pets only
        response = await async_client.get("/api/v1/pets/search?available_only=true")
        assert response.status_code == status.HTTP_200_OK
        available_pets = response.json()
        assert len(available_pets) == 2  # 3 total - 1 adopted
        assert all(pet["is_adopted"] == False for pet in available_pets)

    @pytest.mark.asyncio
    async def test_get_pets_summary(self, async_client: AsyncClient, sample_pets_data):
        """Test getting pets summary statistics."""
        # Create test pets
        for pet_data in sample_pets_data:
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Adopt one pet
        pets = await async_client.get("/api/v1/pets/")
        pet_id = pets.json()[0]["id"]
        await async_client.put(f"/api/v1/pets/{pet_id}/adopt")
        
        # Get summary
        response = await async_client.get("/api/v1/pets/summary")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "species_stats" in data
        assert "overall_totals" in data
        assert data["overall_totals"]["total_pets"] == 3
        assert data["overall_totals"]["adopted_pets"] == 1
        assert data["overall_totals"]["available_pets"] == 2

    @pytest.mark.asyncio
    async def test_get_available_pets(self, async_client: AsyncClient, sample_pets_data):
        """Test getting available pets only."""
        # Create test pets
        for pet_data in sample_pets_data:
            await async_client.post("/api/v1/pets/", json=pet_data)
        
        # Adopt one pet
        pets = await async_client.get("/api/v1/pets/")
        pet_id = pets.json()[0]["id"]
        await async_client.put(f"/api/v1/pets/{pet_id}/adopt")
        
        # Get available pets
        response = await async_client.get("/api/v1/pets/available")
        assert response.status_code == status.HTTP_200_OK
        
        available_pets = response.json()
        assert len(available_pets) == 2  # 3 total - 1 adopted
        assert all(pet["is_adopted"] == False for pet in available_pets)

    @pytest.mark.asyncio
    async def test_create_multiple_pets(self, async_client: AsyncClient, sample_pets_data):
        """Test creating multiple pets in batch."""
        batch_data = {"pets": sample_pets_data}
        
        response = await async_client.post("/api/v1/pets/batch", json=batch_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["message"] == "Successfully created 3 pets"
        assert len(data["created_pets"]) == 3
        assert data["errors"] is None

    @pytest.mark.asyncio
    async def test_get_valid_species(self, async_client: AsyncClient):
        """Test getting valid pet species."""
        response = await async_client.get("/api/v1/pets/species")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "species" in data
        assert "existing_in_database" in data
        assert "common_options" in data
        assert isinstance(data["species"], list)
        assert len(data["species"]) > 0

    @pytest.mark.asyncio
    async def test_pet_validation_edge_cases(self, async_client: AsyncClient):
        """Test pet validation with edge cases."""
        # Test empty name
        pet_data = {"name": "", "species": "Dog"}
        response = await async_client.post("/api/v1/pets/", json=pet_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test negative age
        pet_data = {"name": "Test", "species": "Dog", "age": -1}
        response = await async_client.post("/api/v1/pets/", json=pet_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test very old age
        pet_data = {"name": "Test", "species": "Dog", "age": 100}
        response = await async_client.post("/api/v1/pets/", json=pet_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_concurrent_pet_operations(self, async_client: AsyncClient, sample_pets_data):
        """Test concurrent pet operations."""
        import asyncio
        
        # Create multiple pets concurrently
        tasks = [
            async_client.post("/api/v1/pets/", json=pet_data)
            for pet_data in sample_pets_data
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_201_CREATED
        
        # Verify all pets were created
        response = await async_client.get("/api/v1/pets/")
        assert response.status_code == status.HTTP_200_OK
        pets = response.json()
        assert len(pets) == 3
