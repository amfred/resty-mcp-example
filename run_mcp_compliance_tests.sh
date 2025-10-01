#!/bin/bash

# MCP (Model Context Protocol) Compliance Test Runner
# Pet Adoption API - October 2025 MCP Specification Compliance Tests

set -e

echo "🔍 MCP Compliance Test Runner"
echo "=============================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Flask app is running
echo -e "${BLUE}Checking if API server is running...${NC}"
if ! curl -s http://127.0.0.1:5001/ > /dev/null; then
    echo -e "${RED}❌ API server is not running!${NC}"
    echo -e "${YELLOW}Please start the Flask app first: python app.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ API server is running${NC}"
echo ""

# Function to run tests with different modes
run_mcp_tests() {
    local mode=$1
    local extra_args=$2
    
    case $mode in
        "pytest")
            echo -e "${BLUE}Running MCP compliance tests with pytest...${NC}"
            pytest test_mcp_compliance.py -v $extra_args
            ;;
        "coverage")
            echo -e "${BLUE}Running MCP compliance tests with coverage analysis...${NC}"
            coverage run -m pytest test_mcp_compliance.py -v
            coverage report
            coverage html --directory htmlcov_mcp
            echo -e "${GREEN}HTML coverage report generated in htmlcov_mcp/${NC}"
            ;;
        "html")
            echo -e "${BLUE}Running MCP compliance tests with HTML report...${NC}"
            pytest test_mcp_compliance.py -v --html=mcp_compliance_report.html --self-contained-html
            echo -e "${GREEN}HTML test report generated: mcp_compliance_report.html${NC}"
            ;;
        "ci")
            echo -e "${BLUE}Running MCP compliance tests in CI mode...${NC}"
            pytest test_mcp_compliance.py --junitxml=mcp_compliance_results.xml -v
            echo -e "${GREEN}JUnit XML report generated: mcp_compliance_results.xml${NC}"
            ;;
        "quick")
            echo -e "${BLUE}Running quick MCP compliance smoke tests...${NC}"
            pytest test_mcp_compliance.py -k "test_001 or test_004 or test_021 or test_024 or test_027" -v
            ;;
        "unittest")
            echo -e "${BLUE}Running MCP compliance tests with unittest...${NC}"
            python test_mcp_compliance.py
            ;;
        *)
            echo -e "${BLUE}Running MCP compliance tests with pytest (default)...${NC}"
            pytest test_mcp_compliance.py -v
            ;;
    esac
}

# Parse command line arguments
MODE=${1:-"pytest"}

# Validate test dependencies
echo -e "${BLUE}Checking test dependencies...${NC}"
if ! python -c "import requests, json" 2>/dev/null; then
    echo -e "${RED}❌ Missing required dependencies!${NC}"
    echo -e "${YELLOW}Please install: pip install requests${NC}"
    exit 1
fi

if [[ "$MODE" == "coverage" ]] && ! python -c "import coverage" 2>/dev/null; then
    echo -e "${RED}❌ Coverage module not found!${NC}"
    echo -e "${YELLOW}Please install: pip install coverage${NC}"
    exit 1
fi

if [[ "$MODE" == "html" ]] && ! python -c "import pytest_html" 2>/dev/null; then
    echo -e "${RED}❌ pytest-html module not found!${NC}"
    echo -e "${YELLOW}Please install: pip install pytest-html${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Test dependencies are satisfied${NC}"
echo ""

# Run the tests
echo -e "${BLUE}🧪 Starting MCP Compliance Tests${NC}"
echo -e "${BLUE}Testing against October 2025 MCP Specification${NC}"
echo "================================================"

run_mcp_tests $MODE

echo ""
echo "================================================"
echo -e "${GREEN}✅ MCP Compliance Tests Completed!${NC}"

# Show usage if no arguments provided
if [[ $# -eq 0 ]]; then
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  $0 [MODE]"
    echo ""
    echo -e "${YELLOW}Available modes:${NC}"
    echo -e "  pytest     - Run with pytest (default)"
    echo -e "  coverage   - Run with coverage analysis"
    echo -e "  html       - Generate HTML test report"
    echo -e "  ci         - CI mode with JUnit XML output"
    echo -e "  quick      - Quick smoke tests only"
    echo -e "  unittest   - Run with unittest"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 pytest"
    echo -e "  $0 coverage"
    echo -e "  $0 html"
fi
