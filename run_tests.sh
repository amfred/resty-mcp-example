#!/bin/bash

# Pet Adoption API Test Runner Script
# Usage: ./run_tests.sh [options]

set -e  # Exit on any error

echo "🧪 Pet Adoption API Test Suite"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if API server is running
echo "🔍 Checking if API server is running..."
if ! curl -s http://127.0.0.1:5001/ > /dev/null; then
    echo "❌ API server is not running at http://127.0.0.1:5001"
    echo "   Please start the server first: python app.py"
    exit 1
fi
echo "✅ API server is running"

# Install test dependencies if needed
echo "📦 Checking test dependencies..."
if command -v pip &> /dev/null; then
    pip install -q -r requirements-test.txt
    echo "✅ Test dependencies installed"
fi

# Run tests with different options based on arguments
case "${1:-pytest}" in
    "unittest")
        echo "🏃 Running tests with unittest..."
        python test_api.py
        ;;
    "pytest")
        echo "🏃 Running tests with pytest..."
        python -m pytest test_api.py -v
        ;;
    "coverage")
        echo "🏃 Running tests with coverage report..."
        python -m coverage run -m pytest test_api.py
        python -m coverage report
        python -m coverage html
        echo "📊 Coverage report generated in htmlcov/"
        ;;
    "html")
        echo "🏃 Running tests with HTML report..."
        python -m pytest test_api.py --html=test_report.html --self-contained-html
        echo "📊 HTML report generated: test_report.html"
        ;;
    "ci")
        echo "🏃 Running tests for CI (JUnit XML output)..."
        python -m pytest test_api.py --junitxml=test_results.xml -v
        ;;
    "quick")
        echo "🏃 Running quick smoke tests..."
        python -m pytest test_api.py -k "test_001 or test_002 or test_017" -v
        ;;
    *)
        echo "Usage: $0 [unittest|pytest|coverage|html|ci|quick]"
        echo ""
        echo "Options:"
        echo "  unittest  - Run with Python unittest (default)"
        echo "  pytest    - Run with pytest (recommended)"
        echo "  coverage  - Run with coverage analysis"
        echo "  html      - Generate HTML test report"
        echo "  ci        - CI mode with JUnit XML output"
        echo "  quick     - Run quick smoke tests only"
        exit 1
        ;;
esac

echo ""
echo "✅ Test execution completed!"

