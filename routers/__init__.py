"""
Routers package for Pet Adoption API

This package contains FastAPI router definitions organized by feature area.
"""

# Import routers for easy access
from .pets import router as pets_router
from .mcp import router as mcp_router

__all__ = ["pets_router", "mcp_router"]
