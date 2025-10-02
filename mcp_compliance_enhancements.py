"""
MCP Compliance Enhancements

This file contains enhancements to make our MCP server fully compliant
with the MCP Tools specification 2025-06-18.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Enhanced tool result formatting with full MCP compliance
def format_tool_result_enhanced(
    result: Any, 
    is_error: bool = False,
    content_type: str = "text",
    annotations: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Format tool execution result into fully MCP-compliant content format.
    
    Args:
        result: Tool execution result
        is_error: Whether the result represents an error
        content_type: Type of content (text, image, audio, resource_link, resource)
        annotations: Optional annotations for the content
        
    Returns:
        List of MCP-compliant content objects
    """
    base_annotations = {
        "audience": ["user", "assistant"],
        "priority": 0.8,
        "lastModified": datetime.utcnow().isoformat() + "Z"
    }
    
    if annotations:
        base_annotations.update(annotations)
    
    if is_error:
        return [{
            "type": "text",
            "text": f"Error: {str(result)}",
            "annotations": base_annotations
        }]
    
    if content_type == "text":
        # For structured data, return both text and structured content
        if isinstance(result, (dict, list)):
            return [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, ensure_ascii=False),
                    "annotations": base_annotations
                }
            ]
        else:
            return [{
                "type": "text",
                "text": str(result),
                "annotations": base_annotations
            }]
    
    elif content_type == "image":
        # Example for image content (would need actual image data)
        return [{
            "type": "image",
            "data": "base64-encoded-image-data",  # Would be actual base64 data
            "mimeType": "image/png",
            "annotations": base_annotations
        }]
    
    elif content_type == "resource_link":
        # Example for resource links
        return [{
            "type": "resource_link",
            "uri": "file:///path/to/resource",
            "name": "Resource Name",
            "description": "Resource description",
            "mimeType": "application/json",
            "annotations": base_annotations
        }]
    
    elif content_type == "resource":
        # Example for embedded resources
        return [{
            "type": "resource",
            "resource": {
                "uri": "file:///path/to/resource",
                "title": "Resource Title",
                "mimeType": "application/json",
                "text": json.dumps(result, indent=2),
                "annotations": base_annotations
            }
        }]
    
    else:
        # Default to text
        return [{
            "type": "text",
            "text": str(result),
            "annotations": base_annotations
        }]

# Enhanced tool definitions with full MCP compliance
def get_enhanced_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get enhanced tool definitions with full MCP compliance.
    
    Returns:
        List of fully compliant MCP tool definitions
    """
    return [
        {
            "name": "get_pets_summary",
            "title": "Get Pets Summary",
            "description": "Get comprehensive pet statistics by species and adoption status",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "summary_by_species": {
                        "type": "object",
                        "description": "Statistics grouped by pet species",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "integer"},
                                "adopted": {"type": "integer"},
                                "available": {"type": "integer"}
                            }
                        }
                    },
                    "overall_totals": {
                        "type": "object",
                        "description": "Overall adoption statistics",
                        "properties": {
                            "total_pets": {"type": "integer"},
                            "adopted_pets": {"type": "integer"},
                            "available_pets": {"type": "integer"},
                            "adoption_rate": {"type": "number"}
                        }
                    }
                },
                "required": ["summary_by_species", "overall_totals"],
                "additionalProperties": False
            },
            "annotations": {
                "audience": ["user", "assistant"],
                "priority": 0.9,
                "category": "analytics",
                "requiresConfirmation": False
            }
        },
        {
            "name": "search_pets",
            "title": "Search Pets",
            "description": "Search pets with optional filters for species, breed, availability, and age",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "species": {
                        "type": "string",
                        "description": "Filter by species",
                        "examples": ["Dog", "Cat", "Bird"]
                    },
                    "breed": {
                        "type": "string",
                        "description": "Filter by breed"
                    },
                    "available_only": {
                        "type": "boolean",
                        "description": "Only available pets",
                        "default": False
                    },
                    "min_age": {
                        "type": "integer",
                        "description": "Minimum age",
                        "minimum": 0
                    },
                    "max_age": {
                        "type": "integer",
                        "description": "Maximum age",
                        "minimum": 0
                    }
                },
                "required": [],
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "species": {"type": "string"},
                        "breed": {"type": "string"},
                        "age": {"type": "integer"},
                        "description": {"type": "string"},
                        "is_adopted": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "name", "species", "is_adopted"]
                }
            },
            "annotations": {
                "audience": ["user", "assistant"],
                "priority": 0.8,
                "category": "search",
                "requiresConfirmation": False
            }
        },
        {
            "name": "create_pet",
            "title": "Create Pet",
            "description": "Add a new pet to the adoption system",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Pet name",
                        "minLength": 1,
                        "maxLength": 100
                    },
                    "species": {
                        "type": "string",
                        "description": "Pet species",
                        "enum": ["Dog", "Cat", "Bird", "Rabbit", "Hamster", "Guinea Pig", "Fish", "Reptile"]
                    },
                    "breed": {
                        "type": "string",
                        "description": "Pet breed (optional)",
                        "maxLength": 100
                    },
                    "age": {
                        "type": "integer",
                        "description": "Pet age (optional)",
                        "minimum": 0,
                        "maximum": 30
                    },
                    "description": {
                        "type": "string",
                        "description": "Pet description (optional)",
                        "maxLength": 500
                    }
                },
                "required": ["name", "species"],
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "species": {"type": "string"},
                    "breed": {"type": "string"},
                    "age": {"type": "integer"},
                    "description": {"type": "string"},
                    "is_adopted": {"type": "boolean"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["id", "name", "species", "is_adopted", "created_at"]
            },
            "annotations": {
                "audience": ["user", "assistant"],
                "priority": 0.7,
                "category": "modification",
                "requiresConfirmation": True,
                "sensitiveOperation": True
            }
        },
        {
            "name": "delete_pet",
            "title": "Delete Pet",
            "description": "Remove a pet from the system by ID or name",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pet_id": {
                        "type": "integer",
                        "description": "Pet ID to delete",
                        "minimum": 1
                    },
                    "pet_name": {
                        "type": "string",
                        "description": "Pet name to delete (alternative to pet_id)",
                        "minLength": 1
                    }
                },
                "required": [],
                "additionalProperties": False,
                "anyOf": [
                    {"required": ["pet_id"]},
                    {"required": ["pet_name"]}
                ]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "deleted_pet_id": {"type": "integer"}
                },
                "required": ["message", "deleted_pet_id"]
            },
            "annotations": {
                "audience": ["user", "assistant"],
                "priority": 0.6,
                "category": "modification",
                "requiresConfirmation": True,
                "sensitiveOperation": True,
                "destructiveOperation": True
            }
        }
    ]

# Enhanced capabilities declaration
def get_enhanced_capabilities() -> Dict[str, Any]:
    """
    Get enhanced capabilities declaration with full MCP compliance.
    
    Returns:
        Enhanced capabilities object
    """
    return {
        "tools": {
            "listChanged": True
        },
        "resources": {
            "subscribe": True,
            "listChanged": True
        },
        "prompts": {
            "listChanged": True
        },
        "logging": {
            "level": "info"
        }
    }

# Example of structured content response
def create_structured_tool_result(result: Any) -> Dict[str, Any]:
    """
    Create a tool result with both text and structured content.
    
    Args:
        result: Tool execution result
        
    Returns:
        MCP-compliant tool result with structured content
    """
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2, ensure_ascii=False),
                "annotations": {
                    "audience": ["user", "assistant"],
                    "priority": 0.8,
                    "lastModified": datetime.utcnow().isoformat() + "Z"
                }
            }
        ],
        "structuredContent": result,
        "isError": False
    }

# Example of list changed notification
def create_list_changed_notification() -> Dict[str, Any]:
    """
    Create a tools list changed notification.
    
    Returns:
        MCP-compliant notification
    """
    return {
        "jsonrpc": "2.0",
        "method": "notifications/tools/list_changed"
    }
