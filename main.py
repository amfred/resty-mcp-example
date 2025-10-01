"""
FastAPI main application for Pet Adoption API

This is the main entry point for the FastAPI application, replacing the Flask app.py.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application startup and shutdown.
    
    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    await init_db()
    print("Database initialized")
    
    yield
    
    # Shutdown  
    await close_db()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.description,
    version=settings.app_version,
    openapi_url=settings.openapi_url,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


# Include routers
from routers import pets_router, mcp_router

app.include_router(pets_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")


# Temporary root endpoint (will be moved to routers later)
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name}!",
        "version": settings.app_version,
        "docs": f"{settings.docs_url}",
        "redoc": f"{settings.redoc_url}",
        "api": {
            "pets": "/api/v1/pets",
            "mcp": "/api/v1/mcp"
        },
        "mcp": {
            "protocol_version": settings.mcp_protocol_version,
            "server_name": settings.mcp_server_name,
            "server_version": settings.mcp_server_version,
            "info_endpoint": "/api/v1/mcp/info"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
