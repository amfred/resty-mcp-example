"""
Schemas package for Pet Adoption API

This package contains Pydantic model schemas for request/response validation.
"""

# Pet schemas
from .pet import (
    PetBase,
    PetCreate,
    PetUpdate,
    Pet,
    PetSearchParams,
    PetSummary,
    AdoptionResponse,
    BatchPetCreate,
    BatchPetCreateResponse,
    PetSpecies
)

# MCP schemas
from .mcp import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPInitializeParams,
    MCPInitializeResult,
    MCPToolsListResult,
    MCPToolCallParams,
    MCPToolCallResult,
    MCPResourcesListResult,
    MCPResourceReadParams,
    MCPResourceReadResult,
    MCPPromptsListResult,
    MCPPromptGetParams,
    MCPPromptGetResult,
    MCPLoggingSetLevelParams,
    MCPTool,
    MCPResource,
    MCPPrompt,
    MCPContent
)

__all__ = [
    # Pet schemas
    "PetBase",
    "PetCreate", 
    "PetUpdate",
    "Pet",
    "PetSearchParams",
    "PetSummary",
    "AdoptionResponse",
    "BatchPetCreate",
    "BatchPetCreateResponse",
    "PetSpecies",
    
    # MCP schemas
    "MCPRequest",
    "MCPResponse",
    "MCPError",
    "MCPInitializeParams",
    "MCPInitializeResult",
    "MCPToolsListResult",
    "MCPToolCallParams",
    "MCPToolCallResult",
    "MCPResourcesListResult",
    "MCPResourceReadParams",
    "MCPResourceReadResult",
    "MCPPromptsListResult",
    "MCPPromptGetParams",
    "MCPPromptGetResult",
    "MCPLoggingSetLevelParams",
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "MCPContent"
]
