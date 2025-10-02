"""
MCP (Model Context Protocol) router for Pet Adoption API

FastAPI router implementing JSON-RPC 2.0 MCP endpoints for tool execution,
resource access, and prompt management.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from dependencies import DatabaseDep
from schemas import (
    MCPRequest, MCPResponse, MCPError, 
    MCPInitializeParams, MCPInitializeResult,
    MCPToolCallParams, MCPToolCallResult,
    MCPResourceReadParams, MCPResourceReadResult,
    MCPPromptGetParams, MCPPromptGetResult,
    MCPLoggingSetLevelParams,
    MCPContent
)
from services import MCPService

# Create router for MCP endpoints
router = APIRouter(prefix="/mcp", tags=["mcp"])

# Current logging level (in-memory for demonstration)
current_log_level = "info"


def create_mcp_error_response(request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """Create a standard MCP error response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
            "data": data
        }
    }


def create_mcp_success_response(request_id: Any, result: Any) -> Dict[str, Any]:
    """Create a standard MCP success response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


@router.post("/")
async def mcp_server(request: Request, db: DatabaseDep):
    """
    Full MCP server implementation using JSON-RPC 2.0 protocol.
    
    Handles all MCP methods including initialize, tools, resources, prompts, and logging.
    Follows the MCP specification October 2025.
    """
    try:
        # Parse the JSON-RPC request
        body = await request.json()
        
        # Validate basic JSON-RPC structure
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=create_mcp_error_response(
                    body.get("id"), -32600, "Invalid Request"
                )
            )
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        if not method:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=create_mcp_error_response(request_id, -32600, "Missing method")
            )
        
        # Route to appropriate handler
        try:
            if method == "initialize":
                result = await handle_mcp_initialize(params)
            elif method == "initialized":
                result = await handle_mcp_initialized(params)
            elif method == "tools/list":
                result = await handle_mcp_tools_list(params)
            elif method == "tools/call":
                result = await handle_mcp_tools_call(params, db)
            elif method == "resources/list":
                result = await handle_mcp_resources_list(params)
            elif method == "resources/read":
                result = await handle_mcp_resources_read(params)
            elif method == "resources/subscribe":
                result = await handle_mcp_resources_subscribe(params)
            elif method == "prompts/list":
                result = await handle_mcp_prompts_list(params)
            elif method == "prompts/get":
                result = await handle_mcp_prompts_get(params)
            elif method == "logging/setLevel":
                result = await handle_mcp_logging_setLevel(params)
            else:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=create_mcp_error_response(
                        request_id, -32601, f"Method not found: {method}"
                    )
                )
            
            return JSONResponse(
                content=create_mcp_success_response(request_id, result)
            )
            
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=create_mcp_error_response(
                    request_id, -32602, f"Invalid params: {str(e)}"
                )
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=create_mcp_error_response(
                    request_id, -32603, f"Internal error: {str(e)}"
                )
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_mcp_error_response(
                None, -32700, f"Parse error: {str(e)}"
            )
        )


async def handle_mcp_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize method."""
    # Validate parameters
    try:
        init_params = MCPInitializeParams(**params)
    except Exception as e:
        raise ValueError(f"Invalid initialize parameters: {e}")
    
    # Return server capabilities and info with enhanced MCP compliance
    result = MCPInitializeResult(
        protocolVersion="2025-06-18",
        capabilities={
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
        },
        serverInfo={
            "name": "Pet Adoption API",
            "version": "2.0.0",
            "description": "A REST API for pet adoption with MCP tool integration"
        }
    )
    
    return result.model_dump()


async def handle_mcp_initialized(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialized notification."""
    # This is a notification, so we just acknowledge it
    return {}


async def handle_mcp_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/list method."""
    tools = MCPService.get_available_tools()
    return {
        "tools": [tool.model_dump() for tool in tools]
    }


async def handle_mcp_tools_call(params: Dict[str, Any], db) -> Dict[str, Any]:
    """Handle MCP tools/call method."""
    try:
        call_params = MCPToolCallParams(**params)
    except Exception as e:
        raise ValueError(f"Invalid tool call parameters: {e}")
    
    try:
        # Enhanced validation of tool arguments
        validated_arguments = MCPService.validate_tool_arguments(call_params.name, call_params.arguments)
        
        # Execute the tool using MCPService
        result = await MCPService.execute_tool(db, call_params.name, validated_arguments)
        
        # Check if notifications should be sent for this operation
        notification_flags = MCPService.should_send_notification(call_params.name)
        
        # Format the result as MCP content with structured content support
        content = MCPService.format_tool_result(result, is_error=False)
        
        # Create response with both content and structured content
        response = {
            "content": [item.model_dump() for item in content],
            "isError": False
        }
        
        # Add structured content for programmatic access
        if isinstance(result, (dict, list)):
            response["structuredContent"] = result
        
        # Add notification information to response
        if any(notification_flags.values()):
            response["notifications"] = {
                "tools_list_changed": notification_flags["tools"],
                "resources_list_changed": notification_flags["resources"],
                "prompts_list_changed": notification_flags["prompts"]
            }
        
        return response
        
    except Exception as e:
        # Enhanced error handling
        error_info = MCPService.format_error_response(e)
        error_content = MCPService.format_tool_result(str(e), is_error=True)
        
        return {
            "content": [item.model_dump() for item in error_content],
            "isError": True,
            "error": error_info
        }


async def handle_mcp_resources_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP resources/list method."""
    resources = MCPService.get_available_resources()
    return {
        "resources": [resource.model_dump() for resource in resources]
    }


async def handle_mcp_resources_read(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP resources/read method."""
    try:
        read_params = MCPResourceReadParams(**params)
    except Exception as e:
        raise ValueError(f"Invalid resource read parameters: {e}")
    
    uri = read_params.uri
    
    # Handle different resource types
    if uri == "file://adoption-form.pdf":
        content = MCPContent(
            type="text",
            text="# Pet Adoption Application Form\n\n"
                 "This is a sample adoption form that would contain:\n"
                 "- Applicant personal information\n"
                 "- Housing situation details\n"
                 "- Pet care experience\n"
                 "- References and veterinarian information\n"
                 "- Agreement to adoption terms"
        )
    elif uri == "file://pet-care-guide.md":
        content = MCPContent(
            type="text",
            text="# Pet Care Guidelines\n\n"
                 "## General Care Requirements\n"
                 "- Daily feeding schedule\n"
                 "- Regular exercise and mental stimulation\n"
                 "- Routine veterinary care\n"
                 "- Grooming and hygiene maintenance\n\n"
                 "## Species-Specific Care\n"
                 "Different species have unique care requirements. "
                 "Consult with veterinarians for specific guidance."
        )
    elif uri == "file://adoption-process.md":
        content = MCPContent(
            type="text",
            text="# Pet Adoption Process\n\n"
                 "## Step 1: Browse Available Pets\n"
                 "Use our search features to find pets that match your preferences.\n\n"
                 "## Step 2: Submit Application\n"
                 "Complete the adoption application form.\n\n"
                 "## Step 3: Meet and Greet\n"
                 "Schedule a meeting with your potential new companion.\n\n"
                 "## Step 4: Home Visit\n"
                 "Our team will conduct a home visit to ensure suitability.\n\n"
                 "## Step 5: Adoption Finalization\n"
                 "Complete paperwork and welcome your new family member!"
        )
    elif uri == "file://species-info.json":
        content = MCPContent(
            type="text",
            text='{\n'
                 '  "species_info": {\n'
                 '    "Dog": {"lifespan": "12-15 years", "exercise": "high", "social": "very social"},\n'
                 '    "Cat": {"lifespan": "13-17 years", "exercise": "moderate", "social": "independent"},\n'
                 '    "Bird": {"lifespan": "5-80 years", "exercise": "moderate", "social": "varies"},\n'
                 '    "Rabbit": {"lifespan": "8-12 years", "exercise": "high", "social": "social"}\n'
                 '  }\n'
                 '}'
        )
    else:
        raise ValueError(f"Resource not found: {uri}")
    
    return {
        "contents": [content.model_dump()]
    }


async def handle_mcp_resources_subscribe(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP resources/subscribe method."""
    try:
        # For now, we'll accept any subscription request
        # In a real implementation, this would manage active subscriptions
        uri = params.get("uri", "")
        
        return {
            "message": f"Successfully subscribed to resource: {uri}",
            "uri": uri,
            "subscription_id": f"sub_{hash(uri) % 10000}",
            "status": "active"
        }
    except Exception as e:
        raise ValueError(f"Invalid resource subscription parameters: {e}")


async def handle_mcp_prompts_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP prompts/list method."""
    prompts = MCPService.get_available_prompts()
    return {
        "prompts": [prompt.model_dump() for prompt in prompts]
    }


async def handle_mcp_prompts_get(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP prompts/get method."""
    try:
        prompt_params = MCPPromptGetParams(**params)
    except Exception as e:
        raise ValueError(f"Invalid prompt get parameters: {e}")
    
    try:
        # Generate prompt content
        messages = MCPService.get_prompt_content(prompt_params.name, prompt_params.arguments)
        
        # Convert to MCP message format
        mcp_messages = []
        for message in messages:
            mcp_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        # Find the prompt description
        prompts = MCPService.get_available_prompts()
        prompt_desc = next(
            (p.description for p in prompts if p.name == prompt_params.name),
            f"Prompt: {prompt_params.name}"
        )
        
        return {
            "description": prompt_desc,
            "messages": mcp_messages
        }
        
    except ValueError as e:
        raise ValueError(str(e))


async def handle_mcp_logging_setLevel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP logging/setLevel method."""
    global current_log_level
    
    try:
        logging_params = MCPLoggingSetLevelParams(**params)
    except Exception as e:
        raise ValueError(f"Invalid logging parameters: {e}")
    
    current_log_level = logging_params.level
    return {
        "message": f"Logging level set to {current_log_level}",
        "level": current_log_level
    }


# Notification endpoints for list change notifications
@router.post("/notifications/tools/list_changed")
async def tools_list_changed_notification():
    """
    Handle tools list changed notification.
    
    This endpoint can be called by clients to simulate or trigger
    a tools list changed notification.
    """
    notification = MCPService.create_tools_list_changed_notification()
    return notification


@router.post("/notifications/resources/list_changed")
async def resources_list_changed_notification():
    """
    Handle resources list changed notification.
    
    This endpoint can be called by clients to simulate or trigger
    a resources list changed notification.
    """
    notification = MCPService.create_resources_list_changed_notification()
    return notification


@router.post("/notifications/prompts/list_changed")
async def prompts_list_changed_notification():
    """
    Handle prompts list changed notification.
    
    This endpoint can be called by clients to simulate or trigger
    a prompts list changed notification.
    """
    notification = MCPService.create_prompts_list_changed_notification()
    return notification


# Additional endpoint for MCP server info (non-JSON-RPC)
@router.get("/info")
async def mcp_server_info():
    """
    Get MCP server information (non-JSON-RPC endpoint).
    
    Provides basic information about the MCP server capabilities.
    """
    tools = MCPService.get_available_tools()
    resources = MCPService.get_available_resources()
    prompts = MCPService.get_available_prompts()
    
    return {
        "server": {
            "name": "Pet Adoption API",
            "version": "2.0.0",
            "description": "A REST API for pet adoption with MCP tool integration",
            "protocol_version": "2025-06-18"
        },
        "capabilities": {
            "tools": {
                "count": len(tools),
                "available": [tool.name for tool in tools]
            },
            "resources": {
                "count": len(resources),
                "available": [resource.name for resource in resources]
            },
            "prompts": {
                "count": len(prompts),
                "available": [prompt.name for prompt in prompts]
            },
            "logging": {
                "current_level": current_log_level,
                "supported_levels": ["debug", "info", "warning", "error"]
            }
        }
    }
