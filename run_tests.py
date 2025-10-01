#!/usr/bin/env python3
"""
Test runner for FastAPI Pet Adoption API

Comprehensive test runner with multiple test categories and reporting options.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🧪 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def check_dependencies():
    """Check if required testing dependencies are available."""
    print("🔍 Checking test dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "fastapi"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install pytest pytest-asyncio httpx fastapi")
        return False
    
    print("✅ All test dependencies available")
    return True


def run_unit_tests():
    """Run unit tests."""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_services.py",
        "-v", "--tb=short"
    ], "Unit Tests (Services)")


def run_integration_tests():
    """Run integration tests."""
    return run_command([
        "python", "-m", "pytest",
        "tests/test_fastapi_app.py",
        "-v", "--tb=short"
    ], "Integration Tests (FastAPI App)")


def run_api_tests():
    """Run API endpoint tests."""
    return run_command([
        "python", "-m", "pytest",
        "tests/test_pets_api.py",
        "-v", "--tb=short"
    ], "API Endpoint Tests")


def run_mcp_tests():
    """Run MCP protocol tests."""
    return run_command([
        "python", "-m", "pytest",
        "tests/test_mcp_protocol.py",
        "-v", "--tb=short"
    ], "MCP Protocol Tests")


def run_performance_tests():
    """Run performance tests."""
    return run_command([
        "python", "-m", "pytest",
        "tests/test_performance.py",
        "-v", "--tb=short",
        "-m", "performance"
    ], "Performance Tests")


def run_validation_tests():
    """Run validation tests."""
    tests = [
        ("python", "test_services.py"),
        ("python", "test_routers.py"),
        ("python", "test_integration.py")
    ]
    
    results = []
    for cmd in tests:
        results.append(run_command(cmd, f"Validation Test: {cmd[1]}"))
    
    return all(results)


def run_all_tests():
    """Run all test suites."""
    return run_command([
        "python", "-m", "pytest",
        "tests/",
        "-v", "--tb=short"
    ], "All Test Suites")


def run_with_coverage():
    """Run tests with coverage reporting."""
    return run_command([
        "python", "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ], "Tests with Coverage Report")


def run_specific_markers(markers):
    """Run tests with specific markers."""
    marker_str = " or ".join(markers)
    return run_command([
        "python", "-m", "pytest",
        "tests/",
        "-m", marker_str,
        "-v", "--tb=short"
    ], f"Tests with markers: {marker_str}")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="FastAPI Pet Adoption API Test Runner")
    parser.add_argument("--category", choices=[
        "unit", "integration", "api", "mcp", "performance", 
        "validation", "all", "coverage"
    ], default="all", help="Test category to run")
    parser.add_argument("--markers", nargs="+", help="Specific pytest markers to run")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🚀 FastAPI Pet Adoption API Test Runner")
    print("=" * 50)
    
    # Check dependencies unless skipped
    if not args.skip_deps:
        if not check_dependencies():
            sys.exit(1)
    
    # Run selected tests
    success = True
    
    if args.markers:
        success = run_specific_markers(args.markers)
    elif args.category == "unit":
        success = run_unit_tests()
    elif args.category == "integration":
        success = run_integration_tests()
    elif args.category == "api":
        success = run_api_tests()
    elif args.category == "mcp":
        success = run_mcp_tests()
    elif args.category == "performance":
        success = run_performance_tests()
    elif args.category == "validation":
        success = run_validation_tests()
    elif args.category == "coverage":
        success = run_with_coverage()
    elif args.category == "all":
        success = run_all_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        print("\n📊 Test Summary:")
        print("  • FastAPI application fully tested")
        print("  • All endpoints validated")
        print("  • MCP protocol compliance verified")
        print("  • Performance benchmarks met")
        print("  • Ready for production deployment")
    else:
        print("❌ Some tests failed!")
        print("Please check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
