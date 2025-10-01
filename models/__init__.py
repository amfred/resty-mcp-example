"""
Models package for Pet Adoption API

This package contains SQLAlchemy model definitions for the FastAPI application.
"""

from .database import Base
from .pet import Pet

__all__ = ["Base", "Pet"]
