"""
Pet management router for Pet Adoption API

FastAPI router implementing all pet-related endpoints with async operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from dependencies import DatabaseDep
from schemas import (
    Pet, PetCreate, PetUpdate, PetSearchParams, PetSummary, 
    AdoptionResponse, BatchPetCreate, BatchPetCreateResponse
)
from services import PetService, StatsService

# Create router with prefix and tags
router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("/", response_model=List[Pet])
async def get_pets(db: DatabaseDep):
    """
    Get all pets in the database.
    
    Returns a list of all pets with their complete information.
    """
    pets = await PetService.get_all_pets(db)
    return pets


@router.post("/", response_model=Pet, status_code=status.HTTP_201_CREATED)
async def create_pet(pet_data: PetCreate, db: DatabaseDep):
    """
    Create a new pet in the adoption system.
    
    Adds a new pet with the provided information. Name and species are required.
    """
    try:
        pet = await PetService.create_pet(db, pet_data)
        return pet
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create pet: {str(e)}"
        )


@router.get("/summary", response_model=PetSummary)
async def get_pets_summary(db: DatabaseDep):
    """
    Get comprehensive pet statistics by species and adoption status.
    
    Returns detailed statistics including counts by species and overall totals.
    """
    summary = await StatsService.get_pets_summary(db)
    return PetSummary(**summary)


@router.get("/{pet_id}", response_model=Pet)
async def get_pet(pet_id: int, db: DatabaseDep):
    """
    Get a specific pet by ID.
    
    Returns detailed information about the pet with the given ID.
    """
    pet = await PetService.get_pet_by_id(db, pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID {pet_id} not found"
        )
    return pet


@router.put("/{pet_id}", response_model=Pet)
async def update_pet_info(pet_id: int, pet_update: PetUpdate, db: DatabaseDep):
    """
    Update pet information (excluding adoption status).
    
    Updates the pet's details like name, species, breed, age, or description.
    """
    pet = await PetService.update_pet(db, pet_id, pet_update)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID {pet_id} not found"
        )
    return pet


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet(pet_id: int, db: DatabaseDep):
    """
    Delete a pet from the database.
    
    Permanently removes the pet record from the system.
    """
    success = await PetService.delete_pet(db, pet_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID {pet_id} not found"
        )


@router.put("/{pet_id}/adopt", response_model=AdoptionResponse)
async def adopt_pet(pet_id: int, db: DatabaseDep):
    """
    Mark a pet as adopted by ID.
    
    Updates the pet's adoption status to true.
    """
    try:
        pet = await PetService.adopt_pet(db, pet_id)
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {pet_id} not found"
            )
        
        return AdoptionResponse(
            message=f"{pet.name} has been successfully adopted!",
            pet=pet
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/adopt", response_model=AdoptionResponse)
async def adopt_pet_by_name(
    name: str = Query(..., description="Pet name to search for"),
    db: DatabaseDep = None
):
    """
    Mark a pet as adopted by searching for its name.
    
    Finds a pet by name (case-insensitive) and marks it as adopted.
    """
    pet = await PetService.find_pet_by_name(db, name)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'No pet found with name containing "{name}"'
        )
    
    try:
        adopted_pet = await PetService.adopt_pet(db, pet.id)
        return AdoptionResponse(
            message=f"{adopted_pet.name} has been successfully adopted!",
            pet=adopted_pet
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/search", response_model=List[Pet])
async def search_pets(
    species: Optional[str] = Query(None, description="Filter by species"),
    breed: Optional[str] = Query(None, description="Filter by breed"),
    available_only: bool = Query(False, description="Only available pets"),
    min_age: Optional[int] = Query(None, ge=0, description="Minimum age"),
    max_age: Optional[int] = Query(None, le=50, description="Maximum age"),
    db: DatabaseDep = None
):
    """
    Search pets with various filters.
    
    Supports filtering by species, breed, availability, and age range.
    """
    pets = await PetService.search_pets(
        db, 
        species=species,
        breed=breed, 
        available_only=available_only,
        min_age=min_age,
        max_age=max_age
    )
    return pets


@router.get("/available", response_model=List[Pet])
async def get_available_pets(db: DatabaseDep):
    """
    Get all pets that are currently available for adoption.
    
    Returns only pets that have not yet been adopted.
    """
    pets = await PetService.get_available_pets(db)
    return pets


@router.post("/batch", response_model=BatchPetCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_multiple_pets(batch_data: BatchPetCreate, db: DatabaseDep):
    """
    Add multiple pets in a single operation.
    
    Creates multiple pets in one transaction. Maximum 50 pets per batch.
    """
    created_pets, errors = await PetService.create_pets_batch(db, batch_data.pets)
    
    if errors:
        # If there were errors, return a 207 Multi-Status response
        return JSONResponse(
            status_code=status.HTTP_207_MULTI_STATUS,
            content={
                "message": f"Batch operation completed with {len(errors)} errors",
                "created_pets": [
                    {
                        "id": pet.id,
                        "name": pet.name,
                        "species": pet.species,
                        "breed": pet.breed,
                        "age": pet.age,
                        "description": pet.description,
                        "is_adopted": pet.is_adopted,
                        "created_at": pet.created_at.isoformat() if pet.created_at else None,
                        "updated_at": pet.updated_at.isoformat() if pet.updated_at else None
                    }
                    for pet in created_pets
                ],
                "errors": errors
            }
        )
    
    return BatchPetCreateResponse(
        message=f"Successfully created {len(created_pets)} pets",
        created_pets=created_pets,
        errors=None
    )


@router.get("/species", response_model=dict)
async def get_valid_species(db: DatabaseDep):
    """
    Get list of valid/common pet species.
    
    Returns both existing species in the database and common pet species options.
    """
    from services import MCPService
    result = await MCPService._execute_get_valid_species(db)
    return result
