"""
Configuration settings for Pet Adoption API with FastAPI

Environment-based configuration following FastAPI best practices.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Pet Adoption API"
    app_version: str = "2.0.0"
    description: str = "A REST API for pet adoption with MCP tool integration"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 5001
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./resty.db"
    database_echo: bool = False
    
    # CORS settings
    cors_origins: list[str] = ["*"]
    
    # Security settings
    secret_key: str = "dev-secret-key-change-in-production"
    
    # MCP Protocol settings
    mcp_protocol_version: str = "2025-06-18"
    mcp_server_name: str = "Pet Adoption API"
    mcp_server_version: str = "2.0.0"
    mcp_server_description: str = "A REST API for pet adoption with MCP tool integration"
    
    # API settings
    api_v1_str: str = "/api/v1"
    openapi_url: str = "/api/v1/openapi.json"
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
