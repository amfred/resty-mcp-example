#!/bin/bash

# Demo script: LLM Integration with MCP Server
# This script demonstrates how to:
# 1. Connect to MCP server and retrieve available tools
# 2. Send tools to LLM with a user query
# 3. Execute the LLM's tool call response

set -e  # Exit on any error

# Configuration
MCP_SERVER_URL="http://127.0.0.1:5001/api/v1/mcp/"
OPENAI_API_URL="${OPENAI_API_URL:-https://api.openai.com}/v1/chat/completions}"
OPENAI_API_KEY="${OPENAI_API_KEY:-your-api-key-here}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    
    local response=$(curl -s -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "$init_request")
    
    if echo "$response" | jq -e '.result' > /dev/null 2>&1; then
        print_success "MCP session initialized successfully"
        echo "$response" | jq '.result'
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
    
    local response=$(curl -s -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "$tools_request")
    
    if echo "$response" | jq -e '.result.tools' > /dev/null 2>&1; then
        print_success "Retrieved $(echo "$response" | jq '.result.tools | length') available tools"
        echo "$response" | jq '.result.tools'
        return 0
    else
        print_error "Failed to retrieve tools"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Function to send query to LLM with available tools
query_llm() {
    local tools_json="$1"
    local user_query="$2"
    
    print_step "Sending query to LLM with available tools..."
    
    # Construct the OpenAI chat completions request
    local openai_request=$(cat <<EOF
{
    "model": "gpt-4o",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant that can interact with a pet adoption system. You have access to various tools to help users find and manage pets. When a user asks about pets, use the appropriate tools to get the information they need. Always respond with a tool call when you need to retrieve data."
        },
        {
            "role": "user",
            "content": "$user_query"
        }
    ],
    "tools": $tools_json,
    "tool_choice": "auto",
    "temperature": 0.1
}
EOF
)
    
    print_step "Sending request to OpenAI API..."
    echo "Request payload:"
    echo "$openai_request" | jq '.'
    
    local response=$(curl -s -X POST "$OPENAI_API_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -d "$openai_request")
    
    if echo "$response" | jq -e '.choices[0].message' > /dev/null 2>&1; then
        print_success "Received response from LLM"
        echo "$response" | jq '.choices[0].message'
        return 0
    else
        print_error "Failed to get response from LLM"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Function to execute tool call from LLM response
execute_tool_call() {
    local tool_call="$1"
    
    print_step "Executing tool call from LLM response..."
    
    # Extract tool name and arguments from LLM response
    local tool_name=$(echo "$tool_call" | jq -r '.function.name')
    local tool_args=$(echo "$tool_call" | jq -r '.function.arguments')
    
    print_step "Tool: $tool_name"
    print_step "Arguments: $tool_args"
    
    # Construct MCP tool call request
    local mcp_request=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "$tool_name",
        "arguments": $tool_args
    }
}
EOF
)
    
    print_step "Sending tool call to MCP server..."
    echo "MCP request:"
    echo "$mcp_request" | jq '.'
    
    local response=$(curl -s -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "$mcp_request")
    
    if echo "$response" | jq -e '.result' > /dev/null 2>&1; then
        print_success "Tool executed successfully"
        echo "$response" | jq '.result'
        return 0
    else
        print_error "Failed to execute tool"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Function to format and display results
display_results() {
    local result="$1"
    
    print_step "Formatting results for display..."
    
    echo ""
    echo "=========================================="
    echo "           PET ADOPTION RESULTS           "
    echo "=========================================="
    echo ""
    
    # Check if result contains pets data
    if echo "$result" | jq -e '.content[0].text' > /dev/null 2>&1; then
        local pets_data=$(echo "$result" | jq -r '.content[0].text')
        
        # Try to parse as JSON and format nicely
        if echo "$pets_data" | jq -e '.pets' > /dev/null 2>&1; then
            echo "Available pets for adoption:"
            echo "$pets_data" | jq -r '.pets[] | "• \(.name) (\(.species), \(.breed), age \(.age)) - \(if .is_adopted then "Adopted" else "Available" end)"'
            echo ""
            echo "Total pets: $(echo "$pets_data" | jq -r '.total_count')"
        else
            echo "Raw result:"
            echo "$pets_data"
        fi
    else
        echo "Raw result:"
        echo "$result" | jq '.'
    fi
    
    echo ""
    echo "=========================================="
}

# Main execution function
main() {
    echo "🤖 LLM Integration Demo with MCP Server"
    echo "========================================"
    echo ""
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq first."
        exit 1
    fi
    
    # Check if OpenAI API key is set
    if [ "$OPENAI_API_KEY" = "your-api-key-here" ]; then
        print_warning "Please set your OpenAI API key:"
        print_warning "export OPENAI_API_KEY='your-actual-api-key'"
        print_warning "Or edit this script to set it directly."
        exit 1
    fi
    
    # Step 1: Check MCP server
    check_mcp_server
    
    # Step 2: Initialize MCP session
    initialize_mcp
    
    # Step 3: Get available tools
    local tools_response=$(get_available_tools)
    local tools_json=$(echo "$tools_response" | jq '.result.tools')
    
    # Step 4: Query LLM with tools
    local user_query="List all pets that are available for adoption"
    local llm_response=$(query_llm "$tools_json" "$user_query")
    
    # Step 5: Check if LLM wants to make a tool call
    if echo "$llm_response" | jq -e '.choices[0].message.tool_calls[0]' > /dev/null 2>&1; then
        local tool_call=$(echo "$llm_response" | jq '.choices[0].message.tool_calls[0]')
        
        # Step 6: Execute the tool call
        local tool_result=$(execute_tool_call "$tool_call")
        
        # Step 7: Display formatted results
        display_results "$tool_result"
        
        print_success "Demo completed successfully! 🎉"
    else
        print_warning "LLM did not make a tool call. Response:"
        echo "$llm_response" | jq '.choices[0].message.content'
    fi
}

# Run the main function
main "$@"
