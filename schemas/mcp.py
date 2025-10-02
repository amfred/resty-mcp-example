"""
MCP (Model Context Protocol) Pydantic schemas for Pet Adoption API

JSON-RPC 2.0 protocol schemas following MCP specification October 2025.
"""

from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class MCPErrorCode(int, Enum):
    """Standard JSON-RPC 2.0 error codes for MCP protocol."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


class MCPRequest(BaseModel):
    """
    Base MCP JSON-RPC 2.0 request schema.
    
    All MCP requests must follow this format according to the specification.
    """
    jsonrpc: str = Field(
        ..., 
        pattern="^2\\.0$",
        description="JSON-RPC version (must be '2.0')",
        examples=["2.0"]
    )
    method: str = Field(
        ...,
        min_length=1,
        description="MCP method name",
        examples=["initialize", "tools/list", "tools/call"]
    )
    params: Optional[Dict[str, Any]] = Field(
        None,
        description="Method parameters (optional)"
    )
    id: Optional[Union[str, int]] = Field(
        None,
        description="Request identifier for matching with response"
    )


class MCPResponse(BaseModel):
    """
    Base MCP JSON-RPC 2.0 response schema.
    
    All MCP responses must follow this format.
    """
    jsonrpc: str = Field(
        default="2.0",
        pattern="^2\\.0$",
        description="JSON-RPC version (always '2.0')"
    )
    id: Optional[Union[str, int]] = Field(
        None,
        description="Request identifier (matches request.id)"
    )
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Method result (present on success)"
    )
    error: Optional[Dict[str, Any]] = Field(
        None,
        description="Error information (present on failure)"
    )

    @validator('result', 'error')
    def validate_result_or_error(cls, v, values):
        """Ensure exactly one of result or error is present."""
        if 'result' in values and 'error' in values:
            if values.get('result') is not None and values.get('error') is not None:
                raise ValueError('Response cannot have both result and error')
            if values.get('result') is None and values.get('error') is None:
                raise ValueError('Response must have either result or error')
        return v


class MCPError(BaseModel):
    """MCP error object schema."""
    code: int = Field(
        ...,
        description="Error code (standard JSON-RPC codes)",
        examples=[-32700, -32600, -32601, -32602, -32603]
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    data: Optional[Any] = Field(
        None,
        description="Additional error data (optional)"
    )


# Initialize Method Schemas
class MCPClientInfo(BaseModel):
    """Client information for initialize request."""
    name: str = Field(..., description="Client name")
    version: str = Field(..., description="Client version")


class MCPServerCapabilities(BaseModel):
    """Server capabilities declaration."""
    tools: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tools capability")
    resources: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Resources capability")
    prompts: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Prompts capability")
    logging: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Logging capability")


class MCPInitializeParams(BaseModel):
    """Parameters for initialize method."""
    protocolVersion: str = Field(
        ...,
        description="MCP protocol version",
        examples=["2025-06-18"]
    )
    capabilities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Client capabilities"
    )
    clientInfo: MCPClientInfo = Field(
        ...,
        description="Client information"
    )


class MCPServerInfo(BaseModel):
    """Server information for initialize response."""
    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")
    description: Optional[str] = Field(None, description="Server description")


class MCPInitializeResult(BaseModel):
    """Result for initialize method."""
    protocolVersion: str = Field(
        ...,
        description="Supported MCP protocol version"
    )
    capabilities: MCPServerCapabilities = Field(
        ...,
        description="Server capabilities"
    )
    serverInfo: MCPServerInfo = Field(
        ...,
        description="Server information"
    )


# Tools Method Schemas
class MCPToolSchema(BaseModel):
    """Schema definition for MCP tool input/output."""
    type: str = Field(..., description="Schema type")
    properties: Optional[Dict[str, Any]] = Field(None, description="Schema properties")
    required: Optional[List[str]] = Field(None, description="Required properties")
    additionalProperties: Optional[bool] = Field(None, description="Allow additional properties")


class MCPTool(BaseModel):
    """MCP tool definition schema."""
    name: str = Field(
        ...,
        description="Tool name",
        examples=["get_pets_summary", "create_pet", "search_pets"]
    )
    title: Optional[str] = Field(None, description="Tool title")
    description: str = Field(
        ...,
        description="Tool description"
    )
    inputSchema: Optional[MCPToolSchema] = Field(
        None,
        description="Input parameter schema"
    )
    outputSchema: Optional[MCPToolSchema] = Field(
        None,
        description="Output result schema"
    )
    annotations: Optional[Dict[str, Any]] = Field(
        None,
        description="Tool behavior annotations for trust & safety"
    )


class MCPToolsListResult(BaseModel):
    """Result for tools/list method."""
    tools: List[MCPTool] = Field(
        ...,
        description="Array of available tools"
    )


class MCPToolCallParams(BaseModel):
    """Parameters for tools/call method."""
    name: str = Field(
        ...,
        description="Tool name to execute"
    )
    arguments: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Tool arguments"
    )


class MCPContent(BaseModel):
    """MCP structured content item."""
    type: str = Field(
        ...,
        description="Content type",
        examples=["text", "image", "resource"]
    )
    text: Optional[str] = Field(None, description="Text content")
    data: Optional[str] = Field(None, description="Base64 encoded data")
    mimeType: Optional[str] = Field(None, description="MIME type")
    annotations: Optional[Dict[str, Any]] = Field(
        None,
        description="Content annotations for metadata"
    )


class MCPToolCallResult(BaseModel):
    """Result for tools/call method."""
    content: List[MCPContent] = Field(
        ...,
        description="Structured tool output content"
    )
    structuredContent: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured content for programmatic access"
    )
    isError: bool = Field(
        default=False,
        description="Whether the tool execution resulted in an error"
    )


# Resources Method Schemas
class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str = Field(
        ...,
        description="Resource URI",
        examples=["file://adoption-form.pdf", "file://pet-care-guide.md"]
    )
    name: str = Field(
        ...,
        description="Resource name"
    )
    description: Optional[str] = Field(
        None,
        description="Resource description"
    )
    mimeType: Optional[str] = Field(
        None,
        description="Resource MIME type"
    )


class MCPResourcesListResult(BaseModel):
    """Result for resources/list method."""
    resources: List[MCPResource] = Field(
        ...,
        description="Array of available resources"
    )


class MCPResourceReadParams(BaseModel):
    """Parameters for resources/read method."""
    uri: str = Field(
        ...,
        description="Resource URI to read"
    )


class MCPResourceReadResult(BaseModel):
    """Result for resources/read method."""
    contents: List[MCPContent] = Field(
        ...,
        description="Resource content"
    )


# Prompts Method Schemas
class MCPPromptArgument(BaseModel):
    """MCP prompt argument definition."""
    name: str = Field(..., description="Argument name")
    description: str = Field(..., description="Argument description")
    required: bool = Field(default=False, description="Whether argument is required")


class MCPPrompt(BaseModel):
    """MCP prompt template definition."""
    name: str = Field(
        ...,
        description="Prompt name",
        examples=["adoption_assistant", "pet_care_advisor"]
    )
    description: str = Field(
        ...,
        description="Prompt description"
    )
    arguments: Optional[List[MCPPromptArgument]] = Field(
        None,
        description="Prompt arguments"
    )


class MCPPromptsListResult(BaseModel):
    """Result for prompts/list method."""
    prompts: List[MCPPrompt] = Field(
        ...,
        description="Array of available prompts"
    )


class MCPPromptGetParams(BaseModel):
    """Parameters for prompts/get method."""
    name: str = Field(
        ...,
        description="Prompt name"
    )
    arguments: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Prompt arguments"
    )


class MCPMessage(BaseModel):
    """MCP message for prompt templates."""
    role: str = Field(
        ...,
        description="Message role",
        examples=["system", "user", "assistant"]
    )
    content: MCPContent = Field(
        ...,
        description="Message content"
    )


class MCPPromptGetResult(BaseModel):
    """Result for prompts/get method."""
    description: str = Field(
        ...,
        description="Prompt description"
    )
    messages: List[MCPMessage] = Field(
        ...,
        description="Prompt message sequence"
    )


# Logging Method Schemas
class MCPLoggingSetLevelParams(BaseModel):
    """Parameters for logging/setLevel method."""
    level: str = Field(
        ...,
        description="Logging level",
        examples=["debug", "info", "warning", "error"]
    )

    @validator('level')
    def validate_level(cls, v):
        """Validate logging level."""
        valid_levels = ['debug', 'info', 'notice', 'warning', 'error', 'critical', 'alert', 'emergency']
        if v.lower() not in valid_levels:
            raise ValueError(f'Invalid logging level: {v}. Valid levels: {valid_levels}')
        return v.lower()


# Convenience type unions for method routing
MCPMethodParams = Union[
    MCPInitializeParams,
    MCPToolCallParams,
    MCPResourceReadParams,
    MCPPromptGetParams,
    MCPLoggingSetLevelParams,
    Dict[str, Any]  # For methods with no specific params schema
]

MCPMethodResult = Union[
    MCPInitializeResult,
    MCPToolsListResult,
    MCPToolCallResult,
    MCPResourcesListResult,
    MCPResourceReadResult,
    MCPPromptsListResult,
    MCPPromptGetResult,
    Dict[str, Any]  # For simple result objects
]
