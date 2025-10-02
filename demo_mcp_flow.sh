#!/bin/bash

# Demo script: MCP Server Integration Flow
# This script demonstrates the MCP server interaction flow:
# 1. Initialize MCP session
# 2. Retrieve available tools
# 3. Show how to construct LLM request
# 4. Execute a tool call directly

set -e  # Exit on any error

# Configuration
MCP_SERVER_URL="http://127.0.0.1:5001/api/v1/mcp/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Function to check if MCP server is running
check_mcp_server() {
    print_step "Checking if MCP server is running..."
    
    # Check the health endpoint instead of MCP endpoint
    if curl -s -f "http://127.0.0.1:5001/health" > /dev/null 2>&1; then
        print_success "MCP server is running at $MCP_SERVER_URL"
    else
        print_error "MCP server is not running. Please start it with: uvicorn main:app --host 127.0.0.1 --port 5001"
        exit 1
    fi
}

# Function to initialize MCP session
initialize_mcp() {
    print_step "Initializing MCP session..."
    
    local init_request='{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "demo-script",
                "version": "1.0.0"
            }
        }
    }'
    
    echo "Sending initialization request:"
    echo "$init_request" | jq '.'
    echo ""
    
    local response=$(curl -s -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "$init_request")
    
    if echo "$response" | jq -e '.result' > /dev/null 2>&1; then
        print_success "MCP session initialized successfully"
        echo "Response:"
        echo "$response" | jq '.result'
        echo ""
    else
        print_error "Failed to initialize MCP session"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Function to get available tools from MCP server
get_available_tools() {
    print_step "Retrieving available tools from MCP server..."
    
    local tools_request='{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }'
    
    echo "Sending tools/list request:"
    echo "$tools_request" | jq '.'
    echo ""
    
    local response=$(curl -s -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "$tools_request")
    
    if echo "$response" | jq -e '.result.tools' > /dev/null 2>&1; then
        local tool_count=$(echo "$response" | jq '.result.tools | length')
        print_success "Retrieved $tool_count available tools"
        echo "Available tools:"
        echo "$response" | jq '.result.tools[] | {name: .name, description: .description}'
        echo ""
        return 0
    else
        print_error "Failed to retrieve tools"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Function to show how to construct LLM request
show_llm_request_example() {
    print_step "Showing how to construct LLM request with available tools..."
    
    local tools_request='{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }'
    
    local tools_response=$(curl -s -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "$tools_request")
    
    local tools_json=$(echo "$tools_response" | jq '.result.tools')
    
    print_info "Example OpenAI Chat Completions request:"
    echo ""
    echo "curl -X POST https://api.openai.com/v1/chat/completions \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -H 'Authorization: Bearer \$OPENAI_API_KEY' \\"
    echo "  -d '{"
    echo "    \"model\": \"gpt-4o\","
    echo "    \"messages\": ["
    echo "      {"
    echo "        \"role\": \"system\","
    echo "        \"content\": \"You are a helpful assistant that can interact with a pet adoption system. Use the available tools to help users find and manage pets.\""
    echo "      },"
    echo "      {"
    echo "        \"role\": \"user\","
    echo "        \"content\": \"List all pets that are available for adoption\""
    echo "      }"
    echo "    ],"
    echo "    \"tools\": $(echo "$tools_json" | jq -c .),"
    echo "    \"tool_choice\": \"auto\","
    echo "    \"temperature\": 0.1"
    echo "  }'"
    echo ""
    
    print_info "The LLM would likely respond with a tool call like:"
    echo ""
    echo "{"
    echo "  \"id\": \"call_123\","
    echo "  \"type\": \"function\","
    echo "  \"function\": {"
    echo "    \"name\": \"get_available_pets\","
    echo "    \"arguments\": \"{}\""
    echo "  }"
    echo "}"
    echo ""
}

# Function to execute a tool call directly
execute_direct_tool_call() {
    print_step "Executing tool call directly (simulating LLM response)..."
    
    # Simulate what an LLM would return for "list available pets"
    local tool_call_request='{
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_available_pets",
            "arguments": {}
        }
    }'
    
    echo "Sending tool call request:"
    echo "$tool_call_request" | jq '.'
    echo ""
    
    local response=$(curl -s -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "$tool_call_request")
    
    if echo "$response" | jq -e '.result' > /dev/null 2>&1; then
        print_success "Tool executed successfully"
        echo "Result:"
        echo "$response" | jq '.result'
        echo ""
        
        # Format the results nicely
        print_step "Formatted results:"
        echo "=========================================="
        echo "           AVAILABLE PETS FOR ADOPTION     "
        echo "=========================================="
        
        local pets_data=$(echo "$response" | jq -r '.result.content[0].text')
        if echo "$pets_data" | jq -e '.pets' > /dev/null 2>&1; then
            echo "$pets_data" | jq -r '.pets[] | "• \(.name) (\(.species), \(.breed), age \(.age)) - \(if .is_adopted then "Adopted" else "Available" end)"'
            echo ""
            echo "Total available pets: $(echo "$pets_data" | jq -r '.pets | map(select(.is_adopted == false)) | length')"
        else
            echo "Raw result: $pets_data"
        fi
        
        echo "=========================================="
        echo ""
    else
        print_error "Failed to execute tool"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Function to show alternative tool calls
show_alternative_tool_calls() {
    print_step "Showing alternative tool calls for different queries..."
    
    echo "For 'List all pets':"
    echo "Tool: list_all_pets"
    echo "Arguments: {}"
    echo ""
    
    echo "For 'Find a specific pet by name':"
    echo "Tool: get_pet_by_name"
    echo "Arguments: {\"pet_name\": \"Buddy\"}"
    echo ""
    
    echo "For 'Search for dogs':"
    echo "Tool: search_pets"
    echo "Arguments: {\"species\": \"Dog\"}"
    echo ""
    
    echo "For 'Get adoption statistics':"
    echo "Tool: get_adoption_stats"
    echo "Arguments: {}"
    echo ""
}

# Main execution function
main() {
    echo "🤖 MCP Server Integration Flow Demo"
    echo "===================================="
    echo ""
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq first."
        exit 1
    fi
    
    # Step 1: Check MCP server
    check_mcp_server
    
    # Step 2: Initialize MCP session
    initialize_mcp
    
    # Step 3: Get available tools
    get_available_tools
    
    # Step 4: Show LLM request construction
    show_llm_request_example
    
    # Step 5: Execute a tool call directly
    execute_direct_tool_call
    
    # Step 6: Show alternative tool calls
    show_alternative_tool_calls
    
    print_success "Demo completed successfully! 🎉"
    echo ""
    print_info "To use with a real LLM:"
    print_info "1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'"
    print_info "2. Run the full demo: ./demo_llm_integration.sh"
    print_info "3. Or use the curl command shown above with your preferred LLM API"
}

# Run the main function
main "$@"
