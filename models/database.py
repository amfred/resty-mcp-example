"""
Database models base configuration for Pet Adoption API

This module provides the base class for all SQLAlchemy models.
"""

from sqlalchemy.orm import declarative_base

# Create the declarative base for all models
Base = declarative_base()
