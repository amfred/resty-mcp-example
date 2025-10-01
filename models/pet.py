"""
Pet SQLAlchemy model for Pet Adoption API

Async SQLAlchemy model definition with proper type hints following FastAPI best practices.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from models.database import Base


class Pet(Base):
    """
    Pet model representing animals available for adoption.
    
    This model stores information about pets including their basic details,
    adoption status, and timestamps.
    """
    __tablename__ = "pet"

    # Primary key
    id: int = Column(Integer, primary_key=True, index=True)
    
    # Required fields
    name: str = Column(String(100), nullable=False, index=True)
    species: str = Column(String(50), nullable=False, index=True)
    
    # Optional fields
    breed: Optional[str] = Column(String(100), nullable=True)
    age: Optional[int] = Column(Integer, nullable=True)
    description: Optional[str] = Column(Text, nullable=True)
    
    # Status fields
    is_adopted: bool = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamp fields
    created_at: datetime = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        """String representation of the Pet model."""
        return f"<Pet(id={self.id}, name='{self.name}', species='{self.species}', is_adopted={self.is_adopted})>"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "adopted" if self.is_adopted else "available"
        return f"{self.name} - {self.species} ({status})"
