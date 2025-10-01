"""
Database dependency injection for Pet Adoption API

Provides database session dependencies for FastAPI route handlers.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

# Type alias for database dependency
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
