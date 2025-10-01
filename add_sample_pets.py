#!/usr/bin/env python3
"""
Add sample pets to the database

This script adds 5 sample pets to the FastAPI Pet Adoption API database.
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import async_sessionmaker, engine
from models import Pet
from schemas import PetCreate


async def add_sample_pets():
    """Add 5 sample pets to the database."""
    
    # Sample pets data
    sample_pets = [
        {
            "name": "Buddy",
            "species": "Dog",
            "breed": "Golden Retriever",
            "age": 3,
            "description": "Friendly and energetic dog who loves to play fetch. Great with kids and other pets."
        },
        {
            "name": "Whiskers",
            "species": "Cat",
            "breed": "Persian",
            "age": 2,
            "description": "Calm and gentle cat who enjoys lounging in sunny spots. Perfect for a quiet home."
        },
        {
            "name": "Tweety",
            "species": "Bird",
            "breed": "Canary",
            "age": 1,
            "description": "Beautiful singing bird with bright yellow feathers. Brings joy with its melodious songs."
        },
        {
            "name": "Max",
            "species": "Dog",
            "breed": "Labrador",
            "age": 4,
            "description": "Loyal and intelligent dog. Great for families and loves outdoor activities."
        },
        {
            "name": "Luna",
            "species": "Cat",
            "breed": "Siamese",
            "age": 2,
            "description": "Elegant and social cat with striking blue eyes. Very affectionate and vocal."
        }
    ]
    
    print("🐾 Adding sample pets to the database...")
    print("=" * 50)
    
    async_session = async_sessionmaker(engine)
    async with async_session() as session:
        try:
            added_count = 0
            
            for pet_data in sample_pets:
                # Check if pet already exists
                existing_pet = await session.execute(
                    text("SELECT id FROM pet WHERE name = :name"),
                    {"name": pet_data["name"]}
                )
                
                if existing_pet.fetchone():
                    print(f"⚠️  Pet '{pet_data['name']}' already exists, skipping...")
                    continue
                
                # Create new pet
                pet = Pet(
                    name=pet_data["name"],
                    species=pet_data["species"],
                    breed=pet_data["breed"],
                    age=pet_data["age"],
                    description=pet_data["description"],
                    is_adopted=False
                )
                
                session.add(pet)
                added_count += 1
                print(f"✅ Added: {pet_data['name']} ({pet_data['species']}, {pet_data['breed']}, age {pet_data['age']})")
            
            # Commit all changes
            await session.commit()
            
            print("=" * 50)
            print(f"🎉 Successfully added {added_count} sample pets to the database!")
            
            # Display summary
            result = await session.execute(text("SELECT COUNT(*) FROM pet"))
            total_pets = result.scalar()
            print(f"📊 Total pets in database: {total_pets}")
            
            # Show all pets
            result = await session.execute(text("SELECT name, species, breed, age, is_adopted FROM pet ORDER BY created_at"))
            pets = result.fetchall()
            
            print("\n📋 All pets in database:")
            print("-" * 60)
            for pet in pets:
                status = "Adopted" if pet.is_adopted else "Available"
                print(f"• {pet.name} ({pet.species}, {pet.breed}, age {pet.age}) - {status}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error adding pets: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(add_sample_pets())
