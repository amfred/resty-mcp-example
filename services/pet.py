"""
Pet database service for Pet Adoption API

Async database operations and business logic for pet management following FastAPI patterns.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Pet
from schemas import PetCreate, PetUpdate, Pet as PetSchema


class PetService:
    """
    Async service for pet database operations and business logic.
    
    This service handles all pet-related database operations with proper
    async/await patterns and comprehensive error handling.
    """

    @staticmethod
    async def get_all_pets(db: AsyncSession) -> List[Pet]:
        """
        Get all pets from the database.
        
        Args:
            db: Async database session
            
        Returns:
            List of all Pet models
        """
        result = await db.execute(
            select(Pet).order_by(Pet.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_pet_by_id(db: AsyncSession, pet_id: int) -> Optional[Pet]:
        """
        Get a pet by its ID.
        
        Args:
            db: Async database session
            pet_id: Pet ID to retrieve
            
        Returns:
            Pet model or None if not found
        """
        result = await db.execute(
            select(Pet).where(Pet.id == pet_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_pet(db: AsyncSession, pet_data: PetCreate) -> Pet:
        """
        Create a new pet in the database.
        
        Args:
            db: Async database session
            pet_data: Validated pet creation data
            
        Returns:
            Created Pet model
        """
        # Convert Pydantic model to dict and create Pet instance
        pet_dict = pet_data.model_dump()
        new_pet = Pet(**pet_dict)
        
        db.add(new_pet)
        await db.commit()
        await db.refresh(new_pet)
        
        return new_pet

    @staticmethod
    async def update_pet(
        db: AsyncSession, 
        pet_id: int, 
        pet_update: PetUpdate
    ) -> Optional[Pet]:
        """
        Update a pet's information.
        
        Args:
            db: Async database session
            pet_id: Pet ID to update
            pet_update: Validated pet update data
            
        Returns:
            Updated Pet model or None if not found
        """
        # Get the pet first
        pet = await PetService.get_pet_by_id(db, pet_id)
        if not pet:
            return None
            
        # Update only provided fields
        update_data = pet_update.model_dump(exclude_unset=True)
        
        if update_data:
            await db.execute(
                update(Pet)
                .where(Pet.id == pet_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(pet)
        
        return pet

    @staticmethod
    async def delete_pet(db: AsyncSession, pet_id: int) -> bool:
        """
        Delete a pet from the database.
        
        Args:
            db: Async database session
            pet_id: Pet ID to delete
            
        Returns:
            True if pet was deleted, False if not found
        """
        result = await db.execute(
            delete(Pet).where(Pet.id == pet_id)
        )
        await db.commit()
        
        return result.rowcount > 0

    @staticmethod
    async def adopt_pet(db: AsyncSession, pet_id: int) -> Optional[Pet]:
        """
        Mark a pet as adopted.
        
        Args:
            db: Async database session
            pet_id: Pet ID to adopt
            
        Returns:
            Updated Pet model or None if not found
            
        Raises:
            ValueError: If pet is already adopted
        """
        pet = await PetService.get_pet_by_id(db, pet_id)
        if not pet:
            return None
            
        if pet.is_adopted:
            raise ValueError("Pet is already adopted")
        
        # Update adoption status
        await db.execute(
            update(Pet)
            .where(Pet.id == pet_id)
            .values(is_adopted=True)
        )
        await db.commit()
        await db.refresh(pet)
        
        return pet

    @staticmethod
    async def get_available_pets(db: AsyncSession) -> List[Pet]:
        """
        Get all pets that are available for adoption.
        
        Args:
            db: Async database session
            
        Returns:
            List of available Pet models
        """
        result = await db.execute(
            select(Pet)
            .where(Pet.is_adopted == False)
            .order_by(Pet.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def search_pets(
        db: AsyncSession,
        species: Optional[str] = None,
        breed: Optional[str] = None,
        available_only: bool = False,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None
    ) -> List[Pet]:
        """
        Search pets with various filters.
        
        Args:
            db: Async database session
            species: Filter by species (case-insensitive)
            breed: Filter by breed (case-insensitive)
            available_only: Only return non-adopted pets
            min_age: Minimum age filter
            max_age: Maximum age filter
            
        Returns:
            List of Pet models matching the criteria
        """
        query = select(Pet)
        conditions = []
        
        # Add filters based on provided parameters
        if species:
            conditions.append(Pet.species.ilike(f'%{species}%'))
            
        if breed:
            conditions.append(Pet.breed.ilike(f'%{breed}%'))
            
        if available_only:
            conditions.append(Pet.is_adopted == False)
            
        if min_age is not None:
            conditions.append(Pet.age >= min_age)
            
        if max_age is not None:
            conditions.append(Pet.age <= max_age)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.order_by(Pet.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def find_pet_by_name(db: AsyncSession, name: str) -> Optional[Pet]:
        """
        Find a pet by name (case-insensitive partial matching).
        
        Args:
            db: Async database session
            name: Pet name to search for
            
        Returns:
            First Pet model matching the name or None
        """
        result = await db.execute(
            select(Pet)
            .where(Pet.name.ilike(f'%{name}%'))
            .order_by(Pet.created_at.desc())
        )
        return result.scalars().first()

    @staticmethod
    async def get_pets_by_species(db: AsyncSession, species: str) -> List[Pet]:
        """
        Get all pets of a specific species.
        
        Args:
            db: Async database session
            species: Pet species to filter by
            
        Returns:
            List of Pet models of the specified species
        """
        result = await db.execute(
            select(Pet)
            .where(Pet.species.ilike(species))
            .order_by(Pet.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def create_pets_batch(
        db: AsyncSession, 
        pets_data: List[PetCreate]
    ) -> Tuple[List[Pet], List[str]]:
        """
        Create multiple pets in a single transaction.
        
        Args:
            db: Async database session
            pets_data: List of validated pet creation data
            
        Returns:
            Tuple of (created_pets, error_messages)
        """
        created_pets = []
        errors = []
        
        try:
            for i, pet_data in enumerate(pets_data):
                try:
                    pet_dict = pet_data.model_dump()
                    new_pet = Pet(**pet_dict)
                    db.add(new_pet)
                    created_pets.append(new_pet)
                except Exception as e:
                    errors.append(f"Pet {i+1}: {str(e)}")
            
            if not errors:  # Only commit if no errors
                await db.commit()
                
                # Refresh all created pets to get IDs and timestamps
                for pet in created_pets:
                    await db.refresh(pet)
            else:
                await db.rollback()
                created_pets = []
                
        except Exception as e:
            await db.rollback()
            errors.append(f"Transaction failed: {str(e)}")
            created_pets = []
        
        return created_pets, errors

    @staticmethod
    async def get_pet_count(db: AsyncSession) -> int:
        """
        Get total count of pets in the database.
        
        Args:
            db: Async database session
            
        Returns:
            Total number of pets
        """
        result = await db.execute(select(func.count(Pet.id)))
        return result.scalar() or 0

    @staticmethod
    async def get_available_pet_count(db: AsyncSession) -> int:
        """
        Get count of pets available for adoption.
        
        Args:
            db: Async database session
            
        Returns:
            Number of available pets
        """
        result = await db.execute(
            select(func.count(Pet.id))
            .where(Pet.is_adopted == False)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_adopted_pet_count(db: AsyncSession) -> int:
        """
        Get count of adopted pets.
        
        Args:
            db: Async database session
            
        Returns:
            Number of adopted pets
        """
        result = await db.execute(
            select(func.count(Pet.id))
            .where(Pet.is_adopted == True)
        )
        return result.scalar() or 0

    @staticmethod
    async def pet_exists(db: AsyncSession, pet_id: int) -> bool:
        """
        Check if a pet exists by ID.
        
        Args:
            db: Async database session
            pet_id: Pet ID to check
            
        Returns:
            True if pet exists, False otherwise
        """
        result = await db.execute(
            select(func.count(Pet.id))
            .where(Pet.id == pet_id)
        )
        count = result.scalar() or 0
        return count > 0
