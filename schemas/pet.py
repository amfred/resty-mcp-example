"""
Pet Pydantic schemas for Pet Adoption API

Request/response validation schemas following FastAPI best practices.
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from datetime import datetime
from typing import Optional
from enum import Enum


class PetSpecies(str, Enum):
    """Enumeration of valid pet species."""
    DOG = "Dog"
    CAT = "Cat"
    BIRD = "Bird"
    RABBIT = "Rabbit"
    HAMSTER = "Hamster"
    GUINEA_PIG = "Guinea Pig"
    FISH = "Fish"
    REPTILE = "Reptile"


class PetBase(BaseModel):
    """
    Base Pet schema with common fields for input validation.
    
    This schema contains the core fields that are common across
    create and update operations.
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Pet's name (1-100 characters)",
        examples=["Buddy", "Whiskers", "Tweety"]
    )
    species: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Pet's species (e.g., Dog, Cat, Bird)",
        examples=["Dog", "Cat", "Bird"]
    )
    breed: Optional[str] = Field(
        None, 
        max_length=100,
        description="Pet's breed (optional)",
        examples=["Golden Retriever", "Persian", "Canary"]
    )
    age: Optional[int] = Field(
        None, 
        ge=0, 
        le=50,
        description="Pet's age in years (0-50)",
        examples=[2, 5, 1]
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Description of the pet (optional)",
        examples=["Friendly and energetic", "Calm and cuddly", "Sings beautifully"]
    )

    @validator('species')
    def validate_species(cls, v):
        """Validate that species is one of the common pet types."""
        if v:
            # Convert to title case for consistency
            v = v.strip().title()
            
            # Check against common species (allow custom ones too)
            common_species = [species.value for species in PetSpecies]
            if v not in common_species:
                # Allow custom species but warn in logs (could be implemented later)
                pass
                
        return v

    @validator('name')
    def validate_name(cls, v):
        """Validate pet name format."""
        if v:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or whitespace only')
        return v

    @validator('breed')
    def validate_breed(cls, v):
        """Validate breed format."""
        if v:
            v = v.strip().title()
            if not v:
                return None  # Convert empty string to None
        return v


class PetCreate(PetBase):
    """
    Pet creation schema.
    
    Inherits all validation from PetBase and is used for POST /pets requests.
    All required fields must be provided.
    """
    pass


class PetUpdate(BaseModel):
    """
    Pet update schema for partial updates.
    
    All fields are optional to allow partial updates via PATCH/PUT operations.
    """
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        description="Pet's name (optional for updates)"
    )
    species: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="Pet's species (optional for updates)"
    )
    breed: Optional[str] = Field(
        None, 
        max_length=100,
        description="Pet's breed (optional for updates)"
    )
    age: Optional[int] = Field(
        None, 
        ge=0, 
        le=50,
        description="Pet's age in years (optional for updates)"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Description of the pet (optional for updates)"
    )

    # Apply the same validators as PetBase
    @validator('species')
    def validate_species(cls, v):
        if v:
            v = v.strip().title()
        return v

    @validator('name')
    def validate_name(cls, v):
        if v:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or whitespace only')
        return v

    @validator('breed')
    def validate_breed(cls, v):
        if v:
            v = v.strip().title()
            if not v:
                return None
        return v


class Pet(PetBase):
    """
    Complete Pet schema for responses.
    
    Includes all fields from PetBase plus auto-generated fields like id and timestamps.
    Used for API responses and includes the model configuration for SQLAlchemy integration.
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Auto-generated fields
    id: int = Field(
        ...,
        description="Unique pet identifier",
        examples=[1, 42, 123]
    )
    is_adopted: bool = Field(
        default=False,
        description="Whether the pet has been adopted",
        examples=[False, True]
    )
    created_at: datetime = Field(
        ...,
        description="When the pet was added to the system",
        examples=["2025-01-01T10:30:00Z"]
    )
    updated_at: datetime = Field(
        ...,
        description="When the pet information was last updated",
        examples=["2025-01-01T15:45:00Z"]
    )


class PetSearchParams(BaseModel):
    """
    Schema for pet search query parameters.
    
    Used to validate search/filter parameters in GET /pets/search requests.
    """
    species: Optional[str] = Field(
        None,
        description="Filter by species (case-insensitive, supports partial matching)"
    )
    breed: Optional[str] = Field(
        None,
        description="Filter by breed (case-insensitive, supports partial matching)"
    )
    available_only: bool = Field(
        default=False,
        description="If true, only return pets that are not yet adopted"
    )
    min_age: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum age filter"
    )
    max_age: Optional[int] = Field(
        None,
        le=50,
        description="Maximum age filter"
    )


class PetSummary(BaseModel):
    """
    Schema for pet statistics summary responses.
    
    Used in GET /pets/summary endpoint responses.
    """
    species_stats: dict[str, dict[str, int]] = Field(
        ...,
        description="Statistics grouped by pet species",
        examples=[{
            "Dog": {"available": 5, "adopted": 3, "total": 8},
            "Cat": {"available": 2, "adopted": 1, "total": 3}
        }]
    )
    overall_totals: dict[str, int] = Field(
        ...,
        description="Overall statistics across all species",
        examples=[{
            "total_pets": 11,
            "available_pets": 7,
            "adopted_pets": 4
        }]
    )


class AdoptionResponse(BaseModel):
    """
    Schema for pet adoption responses.
    
    Used when a pet is successfully adopted.
    """
    message: str = Field(
        ...,
        description="Success message",
        examples=["Buddy has been successfully adopted!"]
    )
    pet: Pet = Field(
        ...,
        description="The adopted pet details"
    )


class BatchPetCreate(BaseModel):
    """
    Schema for batch pet creation requests.
    
    Used in POST /pets/batch endpoint.
    """
    pets: list[PetCreate] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="Array of pets to create (1-50 pets maximum)"
    )


class BatchPetCreateResponse(BaseModel):
    """
    Schema for batch pet creation responses.
    """
    message: str = Field(
        ...,
        description="Success message",
        examples=["Successfully created 3 pets"]
    )
    created_pets: list[Pet] = Field(
        ...,
        description="Array of successfully created pets"
    )
    errors: Optional[list[str]] = Field(
        None,
        description="Array of error messages for failed pet creations"
    )
