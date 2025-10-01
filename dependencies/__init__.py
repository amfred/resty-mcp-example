"""
Dependencies package for Pet Adoption API

This package contains FastAPI dependency injection functions for shared resources.
"""

# Database dependencies
from .database import DatabaseDep

__all__ = ["DatabaseDep"]
