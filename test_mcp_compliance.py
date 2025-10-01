#!/usr/bin/env python3
"""
Comprehensive MCP (Model Context Protocol) Compliance Test Suite
For Pet Adoption API - October 2025 MCP Specification Compliance

This test suite ensures full compliance with the MCP specification as of October 2025,
including enhanced error handling, protocol version negotiation, structured tool output,
and security requirements.

Usage:
    python test_mcp_compliance.py              # Run with unittest
    pytest test_mcp_compliance.py              # Run with pytest (recommended)
    pytest test_mcp_compliance.py -v           # Verbose output
"""

import unittest
import requests
import json
import time
import sys
from typing import Dict, Any, List, Optional

# Configuration
API_BASE_URL = "http://127.0.0.1:5001"
TIMEOUT = 10  # seconds
MCP_ENDPOINT = f"{API_BASE_URL}/mcp"

class MCPComplianceTest(unittest.TestCase):
    """Comprehensive MCP Protocol Compliance Test Suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment - check if API is running"""
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=TIMEOUT)
            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}")
            print("✅ MCP server is running and responsive")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to MCP server at {API_BASE_URL}")
            print(f"Error: {e}")
            print("Please make sure the FastAPI app is running: python run_fastapi.py")
            sys.exit(1)
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = API_BASE_URL
        self.mcp_endpoint = MCP_ENDPOINT
        self.headers = {'Content-Type': 'application/json'}
        self.request_id = 1000  # Start with high ID to avoid conflicts
    
    def get_next_request_id(self):
        """Get unique request ID for each test"""
        self.request_id += 1
        return self.request_id
    
    def make_mcp_request(self, method: str, params: Optional[Dict] = None, request_id: Optional[int] = None) -> requests.Response:
        """Helper to make MCP JSON-RPC requests"""
        if request_id is None:
            request_id = self.get_next_request_id()
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }
        
        if params is not None:
            payload["params"] = params
        
        return requests.post(self.mcp_endpoint, json=payload, headers=self.headers)
    
    def assert_valid_jsonrpc_response(self, response: requests.Response, expected_id: int):
        """Assert that response is a valid JSON-RPC 2.0 response"""
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('jsonrpc'), '2.0')
        self.assertEqual(data.get('id'), expected_id)
        return data
    
    def assert_jsonrpc_error(self, response: requests.Response, expected_error_code: int, expected_id: Optional[int] = None):
        """Assert that response contains a JSON-RPC error"""
        data = response.json()
        self.assertEqual(data.get('jsonrpc'), '2.0')
        if expected_id is not None:
            self.assertEqual(data.get('id'), expected_id)
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], expected_error_code)
        return data
    
    # ========================================
    # Core Protocol Compliance Tests
    # ========================================
    
    def test_001_mcp_initialize_basic(self):
        """Test MCP initialize method - basic functionality"""
        request_id = self.get_next_request_id()
        params = {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-compliance-tester",
                "version": "1.0.0"
            }
        }
        
        response = self.make_mcp_request("initialize", params, request_id)
        data = self.assert_valid_jsonrpc_response(response, request_id)
        
        result = data['result']
        self.assertIn('protocolVersion', result)
        self.assertIn('capabilities', result)
        self.assertIn('serverInfo', result)
        
        # Validate server info structure
        server_info = result['serverInfo']
        self.assertIn('name', server_info)
        self.assertIn('version', server_info)
        
        print("✅ MCP initialize basic functionality working")
    
    def test_002_mcp_protocol_version_validation(self):
        """Test protocol version compatibility and negotiation"""
        test_cases = [
            ("2025-06-18", True, "Current supported version"),
            ("2024-12-01", False, "Older version should be rejected or handled gracefully"),
            ("2026-01-01", False, "Future version should be rejected"),
            ("invalid-version", False, "Invalid version format"),
            ("", False, "Empty version"),
        ]
        
        for version, should_succeed, description in test_cases:
            with self.subTest(version=version, description=description):
                request_id = self.get_next_request_id()
                params = {
                    "protocolVersion": version,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "version-test-client",
                        "version": "1.0.0"
                    }
                }
                
                response = self.make_mcp_request("initialize", params, request_id)
                
                if should_succeed and version == "2025-06-18":
                    # Only the current version should definitely succeed
                    data = self.assert_valid_jsonrpc_response(response, request_id)
                    self.assertIn('result', data)
                else:
                    # Other versions may succeed with graceful handling or fail appropriately
                    data = response.json()
                    self.assertEqual(data.get('jsonrpc'), '2.0')
                    # Either success with version negotiation or appropriate error
                    if 'error' in data:
                        self.assertIn(data['error']['code'], [-32602, -32600])  # Invalid params or request
        
        print("✅ Protocol version validation working")
    
    def test_003_mcp_initialized_notification(self):
        """Test MCP initialized notification"""
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("initialized", {}, request_id)
        data = self.assert_valid_jsonrpc_response(response, request_id)
        
        # initialized should return empty result
        self.assertIn('result', data)
        self.assertEqual(data['result'], {})
        
        print("✅ MCP initialized notification working")
    
    def test_004_mcp_capabilities_validation(self):
        """Test server capabilities declaration and validation"""
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"}
        }, request_id)
        
        data = self.assert_valid_jsonrpc_response(response, request_id)
        capabilities = data['result']['capabilities']
        
        # Validate current capabilities structure
        self.assertIn('tools', capabilities)
        self.assertIsInstance(capabilities['tools'], dict)
        self.assertIn('listChanged', capabilities['tools'])
        self.assertIsInstance(capabilities['tools']['listChanged'], bool)
        
        # Check for additional capabilities that should be supported
        expected_capabilities = ['tools']
        optional_capabilities = ['resources', 'prompts', 'logging', 'sampling']
        
        for cap in expected_capabilities:
            self.assertIn(cap, capabilities, f"Required capability '{cap}' missing")
        
        # Log optional capabilities for completeness analysis
        supported_optional = [cap for cap in optional_capabilities if cap in capabilities]
        missing_optional = [cap for cap in optional_capabilities if cap not in capabilities]
        
        if missing_optional:
            print(f"ℹ️  Optional capabilities not implemented: {missing_optional}")
        if supported_optional:
            print(f"✅ Optional capabilities implemented: {supported_optional}")
        
        print("✅ MCP capabilities validation working")
    
    def test_005_tools_list_comprehensive(self):
        """Test tools/list method comprehensively"""
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("tools/list", {}, request_id)
        data = self.assert_valid_jsonrpc_response(response, request_id)
        
        result = data['result']
        self.assertIn('tools', result)
        tools = result['tools']
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0, "Should have at least one tool")
        
        # Validate each tool definition
        required_tool_fields = ['name', 'description']
        for i, tool in enumerate(tools):
            with self.subTest(tool_index=i, tool_name=tool.get('name', f'tool_{i}')):
                for field in required_tool_fields:
                    self.assertIn(field, tool, f"Tool missing required field '{field}'")
                
                # Validate input schema if present
                if 'inputSchema' in tool:
                    schema = tool['inputSchema']
                    self.assertIn('type', schema)
                    if 'properties' in schema:
                        self.assertIsInstance(schema['properties'], dict)
                
                # Validate name format (should be alphanumeric with underscores/hyphens)
                name = tool['name']
                self.assertRegex(name, r'^[a-zA-Z0-9_-]+$', f"Tool name '{name}' should be alphanumeric")
        
        print(f"✅ Tools list comprehensive validation working - {len(tools)} tools validated")
    
    def test_006_tools_call_validation(self):
        """Test tools/call method with validation"""
        # First get list of available tools
        tools_response = self.make_mcp_request("tools/list")
        tools_data = tools_response.json()
        tools = tools_data['result']['tools']
        
        if not tools:
            self.skipTest("No tools available to test")
        
        # Test with a safe tool (get_pets_summary doesn't modify data)
        test_tool = None
        for tool in tools:
            if tool['name'] == 'get_pets_summary':
                test_tool = tool
                break
        
        if not test_tool:
            self.skipTest("get_pets_summary tool not available")
        
        # Test valid tool call
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("tools/call", {
            "name": "get_pets_summary",
            "arguments": {}
        }, request_id)
        
        data = self.assert_valid_jsonrpc_response(response, request_id)
        result = data['result']
        
        # Validate tool call result structure
        self.assertIn('content', result)
        self.assertIsInstance(result['content'], list)
        self.assertGreater(len(result['content']), 0)
        
        # Validate content structure
        content = result['content'][0]
        self.assertIn('type', content)
        self.assertIn('text', content)
        
        # Validate isError field
        self.assertIn('isError', result)
        self.assertIsInstance(result['isError'], bool)
        
        print("✅ Tools call validation working")
    
    def test_007_tools_call_error_handling(self):
        """Test tools/call error scenarios"""
        test_cases = [
            ({}, "Missing tool name"),
            ({"name": ""}, "Empty tool name"),
            ({"name": "nonexistent_tool"}, "Nonexistent tool"),
            ({"name": "get_pets_summary", "arguments": "invalid"}, "Invalid arguments type"),
        ]
        
        for params, description in test_cases:
            with self.subTest(params=params, description=description):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("tools/call", params, request_id)
                
                # Should either return error response or tool execution error
                data = response.json()
                if response.status_code == 200 and 'result' in data:
                    # Tool execution error should be in result.isError
                    result = data['result']
                    if 'isError' in result:
                        self.assertTrue(result['isError'], f"Expected error for {description}")
                    else:
                        self.fail(f"Expected error response for {description}")
                else:
                    # JSON-RPC error response
                    self.assert_jsonrpc_error(response, -32602)  # Invalid params
        
        print("✅ Tools call error handling working")
    
    # ========================================
    # JSON-RPC Protocol Compliance Tests  
    # ========================================
    
    def test_008_jsonrpc_format_validation(self):
        """Test JSON-RPC 2.0 format validation"""
        invalid_requests = [
            ({}, "Empty request"),
            ({"jsonrpc": "1.0", "method": "test", "id": 1}, "Wrong JSON-RPC version"),
            ({"method": "test", "id": 1}, "Missing jsonrpc field"),
            ({"jsonrpc": "2.0", "id": 1}, "Missing method field"),
            ({"jsonrpc": "2.0", "method": "", "id": 1}, "Empty method name"),
            ({"jsonrpc": "2.0", "method": 123, "id": 1}, "Invalid method type"),
        ]
        
        for request_data, description in invalid_requests:
            with self.subTest(request=request_data, description=description):
                response = requests.post(self.mcp_endpoint, json=request_data, headers=self.headers)
                
                if not request_data:  # Empty request
                    self.assertEqual(response.status_code, 400)
                    self.assert_jsonrpc_error(response, -32700)  # Parse error
                else:
                    self.assertEqual(response.status_code, 400)
                    self.assert_jsonrpc_error(response, -32600)  # Invalid Request
        
        print("✅ JSON-RPC format validation working")
    
    def test_009_jsonrpc_error_codes(self):
        """Test standard JSON-RPC error codes"""
        test_cases = [
            # Parse error (-32700)
            ("invalid json", -32700, "Parse error"),
            
            # Invalid Request (-32600) - tested via malformed requests
            ({"jsonrpc": "2.0", "method": "", "id": 1}, -32600, "Invalid Request"),
            
            # Method not found (-32601)
            ({"jsonrpc": "2.0", "method": "nonexistent_method", "id": 1}, -32601, "Method not found"),
            
            # Invalid params (-32602) - tested via malformed parameters
            ({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": 123}, "id": 1}, -32602, "Invalid params"),
        ]
        
        for request_data, expected_code, description in test_cases:
            with self.subTest(request=request_data, expected_code=expected_code):
                if isinstance(request_data, str):
                    # Test parse error with invalid JSON
                    response = requests.post(self.mcp_endpoint, data=request_data, headers=self.headers)
                else:
                    response = requests.post(self.mcp_endpoint, json=request_data, headers=self.headers)
                
                if expected_code == -32601:
                    self.assertEqual(response.status_code, 404)
                else:
                    self.assertEqual(response.status_code, 400)
                
                self.assert_jsonrpc_error(response, expected_code)
        
        print("✅ JSON-RPC error codes working")
    
    def test_010_request_id_handling(self):
        """Test request ID handling in responses"""
        test_cases = [
            (1, "Integer ID"),
            ("test_id", "String ID"), 
            (None, "Null ID"),
            (0, "Zero ID"),
            (-1, "Negative ID"),
        ]
        
        for request_id, description in test_cases:
            with self.subTest(request_id=request_id, description=description):
                response = self.make_mcp_request("tools/list", {}, request_id)
                data = response.json()
                
                self.assertEqual(data.get('jsonrpc'), '2.0')
                self.assertEqual(data.get('id'), request_id)
        
        print("✅ Request ID handling working")
    
    # ========================================
    # Advanced MCP Feature Tests
    # ========================================
    
    def test_011_structured_tool_output(self):
        """Test structured tool output compliance (MCP 2025 requirement)"""
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("tools/call", {
            "name": "get_pets_summary",
            "arguments": {}
        }, request_id)
        
        data = self.assert_valid_jsonrpc_response(response, request_id)
        result = data['result']
        
        # Validate structured output format
        self.assertIn('content', result)
        content = result['content']
        self.assertIsInstance(content, list)
        
        for item in content:
            self.assertIn('type', item)
            # Common content types: text, image, resource, etc.
            self.assertIn(item['type'], ['text', 'image', 'resource', 'data'])
            
            if item['type'] == 'text':
                self.assertIn('text', item)
                self.assertIsInstance(item['text'], str)
        
        print("✅ Structured tool output validation working")
    
    def test_012_capability_negotiation(self):
        """Test capability negotiation between client and server"""
        # Test with different client capabilities
        client_capabilities = [
            {},  # Basic client
            {"tools": {}},  # Tools-aware client
            {"tools": {}, "resources": {}},  # Extended client
            {"tools": {}, "resources": {}, "prompts": {}, "logging": {}},  # Full-featured client
        ]
        
        for i, client_caps in enumerate(client_capabilities):
            with self.subTest(client_capabilities=client_caps, test_index=i):
                request_id = self.get_next_request_id()
                params = {
                    "protocolVersion": "2025-06-18",
                    "capabilities": client_caps,
                    "clientInfo": {
                        "name": f"capability-test-client-{i}",
                        "version": "1.0.0"
                    }
                }
                
                response = self.make_mcp_request("initialize", params, request_id)
                data = self.assert_valid_jsonrpc_response(response, request_id)
                
                server_caps = data['result']['capabilities']
                
                # Server should respond with its own capabilities
                self.assertIn('tools', server_caps)
                
                # Server capabilities should be consistent regardless of client
                self.assertIsInstance(server_caps['tools'], dict)
        
        print("✅ Capability negotiation working")
    
    def test_013_session_lifecycle(self):
        """Test complete MCP session lifecycle"""
        # 1. Initialize
        request_id = self.get_next_request_id()
        init_response = self.make_mcp_request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "session-test", "version": "1.0.0"}
        }, request_id)
        
        self.assert_valid_jsonrpc_response(init_response, request_id)
        
        # 2. Initialized notification
        request_id = self.get_next_request_id()
        initialized_response = self.make_mcp_request("initialized", {}, request_id)
        self.assert_valid_jsonrpc_response(initialized_response, request_id)
        
        # 3. Use tools
        request_id = self.get_next_request_id()
        tools_response = self.make_mcp_request("tools/list", {}, request_id)
        self.assert_valid_jsonrpc_response(tools_response, request_id)
        
        request_id = self.get_next_request_id()
        call_response = self.make_mcp_request("tools/call", {
            "name": "get_pets_summary",
            "arguments": {}
        }, request_id)
        self.assert_valid_jsonrpc_response(call_response, request_id)
        
        print("✅ Session lifecycle working")
    
    # ========================================
    # Performance and Reliability Tests
    # ========================================
    
    def test_014_concurrent_requests(self):
        """Test handling of concurrent MCP requests"""
        import threading
        import queue
        
        num_threads = 5
        results_queue = queue.Queue()
        
        def make_concurrent_request(thread_id):
            try:
                request_id = 2000 + thread_id  # Unique IDs
                response = self.make_mcp_request("tools/list", {}, request_id)
                data = response.json()
                results_queue.put((thread_id, data.get('id'), response.status_code == 200))
            except Exception as e:
                results_queue.put((thread_id, None, False))
        
        # Start concurrent threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=make_concurrent_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Validate results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        self.assertEqual(len(results), num_threads)
        
        # All requests should succeed with correct IDs
        for thread_id, response_id, success in results:
            expected_id = 2000 + thread_id
            self.assertTrue(success, f"Thread {thread_id} failed")
            self.assertEqual(response_id, expected_id, f"Thread {thread_id} got wrong ID")
        
        print(f"✅ Concurrent requests working - {num_threads} threads")
    
    def test_015_large_payload_handling(self):
        """Test handling of large payloads"""
        # Create a large pet description
        large_description = "A" * 10000  # 10KB description
        
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("tools/call", {
            "name": "create_pet",
            "arguments": {
                "name": "Large Data Pet",
                "species": "Dog",
                "description": large_description
            }
        }, request_id)
        
        # Should handle large payload gracefully
        data = response.json()
        self.assertEqual(data.get('jsonrpc'), '2.0')
        
        # Clean up if pet was created successfully
        if response.status_code == 200 and 'result' in data:
            result = data['result']
            if not result.get('isError', True):
                try:
                    # Parse the response to get pet ID and clean up
                    content_text = result['content'][0]['text']
                    pet_data = json.loads(content_text)
                    if 'id' in pet_data:
                        requests.delete(f"{self.base_url}/pets/{pet_data['id']}")
                except:
                    pass  # Cleanup failed, but test still valid
        
        print("✅ Large payload handling working")
    
    # ========================================
    # Security and Validation Tests
    # ========================================
    
    def test_016_input_sanitization(self):
        """Test input sanitization and validation"""
        malicious_inputs = [
            {"name": "<script>alert('xss')</script>", "species": "Dog"},
            {"name": "../../../etc/passwd", "species": "Cat"},
            {"name": "'; DROP TABLE pets; --", "species": "Bird"},
            {"name": "\x00null\x00byte", "species": "Fish"},
        ]
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("tools/call", {
                    "name": "create_pet",
                    "arguments": malicious_input
                }, request_id)
                
                # Should either reject input or sanitize it
                data = response.json()
                self.assertEqual(data.get('jsonrpc'), '2.0')
                
                # If successful, verify sanitization occurred
                if response.status_code == 200 and 'result' in data:
                    result = data['result']
                    if not result.get('isError', True):
                        # If pet was created, clean it up and verify name was sanitized
                        content_text = result['content'][0]['text']
                        pet_data = json.loads(content_text)
                        if 'id' in pet_data:
                            # Clean up
                            requests.delete(f"{self.base_url}/pets/{pet_data['id']}")
                            
                            # Name should be sanitized (not contain original malicious content)
                            created_name = pet_data.get('name', '')
                            original_malicious = malicious_input['name']
                            self.assertNotEqual(created_name, original_malicious, 
                                              "Malicious input should be sanitized")
        
        print("✅ Input sanitization working")
    
    def test_017_rate_limiting_awareness(self):
        """Test server behavior under rapid requests (rate limiting awareness)"""
        # Make rapid sequential requests
        rapid_requests = 10
        responses = []
        
        for i in range(rapid_requests):
            request_id = self.get_next_request_id()
            response = self.make_mcp_request("tools/list", {}, request_id)
            responses.append((response.status_code, response.headers))
        
        # All should succeed (assuming no rate limiting implemented)
        # Or handle rate limiting gracefully
        success_count = sum(1 for status, headers in responses if status == 200)
        
        # Either all succeed or rate limiting is handled properly
        if success_count < rapid_requests:
            # Check for rate limiting headers
            rate_limited_responses = [r for r in responses if r[0] == 429]
            if rate_limited_responses:
                print("ℹ️  Rate limiting detected (429 responses)")
            else:
                print("ℹ️  Some requests failed (may indicate load handling)")
        
        self.assertGreater(success_count, 0, "At least some requests should succeed")
        
        print(f"✅ Rate limiting awareness - {success_count}/{rapid_requests} succeeded")
    
    # ========================================
    # Edge Cases and Boundary Tests
    # ========================================
    
    def test_018_boundary_value_testing(self):
        """Test boundary values and edge cases"""
        boundary_tests = [
            # Empty strings
            ({"name": "", "species": "Dog"}, "Empty name"),
            ({"name": "Pet", "species": ""}, "Empty species"),
            
            # Very long strings
            ({"name": "A" * 100, "species": "Dog"}, "Long name"),
            ({"name": "Pet", "species": "B" * 100}, "Long species"),
            
            # Special characters
            ({"name": "Pét Namé", "species": "Dög"}, "Unicode characters"),
            ({"name": "Pet-Name_123", "species": "Cat/Dog"}, "Special characters"),
            
            # Numeric edge cases
            ({"name": "Pet", "species": "Dog", "age": -1}, "Negative age"),
            ({"name": "Pet", "species": "Dog", "age": 1000}, "Very high age"),
            ({"name": "Pet", "species": "Dog", "age": 0}, "Zero age"),
        ]
        
        for args, description in boundary_tests:
            with self.subTest(args=args, description=description):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("tools/call", {
                    "name": "create_pet",
                    "arguments": args
                }, request_id)
                
                data = response.json()
                self.assertEqual(data.get('jsonrpc'), '2.0')
                
                # Either succeeds with validation or fails appropriately
                if response.status_code == 200 and 'result' in data:
                    result = data['result']
                    # If successful, clean up
                    if not result.get('isError', True):
                        try:
                            content_text = result['content'][0]['text']
                            pet_data = json.loads(content_text)
                            if 'id' in pet_data:
                                requests.delete(f"{self.base_url}/pets/{pet_data['id']}")
                        except:
                            pass
        
        print("✅ Boundary value testing working")
    
    def test_019_method_case_sensitivity(self):
        """Test method name case sensitivity"""
        method_variants = [
            ("tools/list", True, "Standard case"),
            ("Tools/List", False, "Pascal case"),
            ("TOOLS/LIST", False, "Upper case"),
            ("tools/List", False, "Mixed case"),
            ("tools/LIST", False, "Mixed case upper"),
        ]
        
        for method, should_work, description in method_variants:
            with self.subTest(method=method, description=description):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request(method, {}, request_id)
                
                if should_work:
                    self.assert_valid_jsonrpc_response(response, request_id)
                else:
                    # Should return method not found error
                    self.assertEqual(response.status_code, 404)
                    self.assert_jsonrpc_error(response, -32601)
        
        print("✅ Method case sensitivity working")
    
    def test_020_empty_and_null_parameters(self):
        """Test handling of empty and null parameters"""
        param_variants = [
            ({}, "Empty params"),
            ({"arguments": {}}, "Empty arguments"),
            ({"name": "get_pets_summary"}, "Missing arguments"),
            ({"name": "get_pets_summary", "arguments": None}, "Null arguments"),
        ]
        
        for params, description in param_variants:
            with self.subTest(params=params, description=description):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("tools/call", params, request_id)
                
                # Should handle gracefully - either succeed or proper error
                data = response.json()
                self.assertEqual(data.get('jsonrpc'), '2.0')
                
                if 'error' in data:
                    # Error should be appropriate (invalid params)
                    self.assertIn(data['error']['code'], [-32602, -32603])
                else:
                    # If successful, should have valid result
                    self.assertIn('result', data)
        
        print("✅ Empty and null parameter handling working")
    
    # ========================================
    # Extended MCP Capabilities Tests (New in October 2025)
    # ========================================
    
    def test_021_resources_list(self):
        """Test MCP resources/list method"""
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("resources/list", {}, request_id)
        data = self.assert_valid_jsonrpc_response(response, request_id)
        
        result = data['result']
        self.assertIn('resources', result)
        resources = result['resources']
        self.assertIsInstance(resources, list)
        
        # Validate resource structure
        for resource in resources:
            required_fields = ['uri', 'name', 'description']
            for field in required_fields:
                self.assertIn(field, resource)
            
            # Optional but common fields
            if 'mimeType' in resource:
                self.assertIsInstance(resource['mimeType'], str)
        
        print(f"✅ Resources list working - {len(resources)} resources available")
    
    def test_022_resources_read(self):
        """Test MCP resources/read method"""
        # First get list of available resources
        list_response = self.make_mcp_request("resources/list")
        list_data = list_response.json()
        resources = list_data['result']['resources']
        
        if not resources:
            self.skipTest("No resources available to test")
        
        # Test reading a resource
        test_resource = resources[0]
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("resources/read", {"uri": test_resource['uri']}, request_id)
        data = self.assert_valid_jsonrpc_response(response, request_id)
        
        result = data['result']
        self.assertIn('contents', result)
        contents = result['contents']
        self.assertIsInstance(contents, list)
        
        # Validate content structure
        for content_item in contents:
            self.assertIn('type', content_item)
            # Common content types
            self.assertIn(content_item['type'], ['text', 'image', 'resource', 'data'])
            
            if content_item['type'] == 'text':
                self.assertIn('text', content_item)
        
        print(f"✅ Resources read working - read resource {test_resource['name']}")
    
    def test_023_resources_read_error_handling(self):
        """Test MCP resources/read error handling"""
        test_cases = [
            ({}, "Missing URI"),
            ({"uri": ""}, "Empty URI"),
            ({"uri": "file://nonexistent.txt"}, "Nonexistent resource"),
            ({"uri": "invalid-uri-format"}, "Invalid URI format"),
        ]
        
        for params, description in test_cases:
            with self.subTest(params=params, description=description):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("resources/read", params, request_id)
                
                # Should return error for all invalid cases
                data = response.json()
                self.assertEqual(data.get('jsonrpc'), '2.0')
                self.assertIn('error', data)
                self.assertEqual(data['error']['code'], -32602)  # Invalid params
        
        print("✅ Resources read error handling working")
    
    def test_024_prompts_list(self):
        """Test MCP prompts/list method"""
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("prompts/list", {}, request_id)
        data = self.assert_valid_jsonrpc_response(response, request_id)
        
        result = data['result']
        self.assertIn('prompts', result)
        prompts = result['prompts']
        self.assertIsInstance(prompts, list)
        
        # Validate prompt structure
        for prompt in prompts:
            required_fields = ['name', 'description']
            for field in required_fields:
                self.assertIn(field, prompt)
            
            # Validate arguments if present
            if 'arguments' in prompt:
                self.assertIsInstance(prompt['arguments'], list)
                for arg in prompt['arguments']:
                    self.assertIn('name', arg)
                    self.assertIn('description', arg)
                    if 'required' in arg:
                        self.assertIsInstance(arg['required'], bool)
        
        print(f"✅ Prompts list working - {len(prompts)} prompts available")
    
    def test_025_prompts_get(self):
        """Test MCP prompts/get method"""
        # First get list of available prompts
        list_response = self.make_mcp_request("prompts/list")
        list_data = list_response.json()
        prompts = list_data['result']['prompts']
        
        if not prompts:
            self.skipTest("No prompts available to test")
        
        # Test getting a prompt
        test_prompt = prompts[0]
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("prompts/get", {
            "name": test_prompt['name'],
            "arguments": {}
        }, request_id)
        data = self.assert_valid_jsonrpc_response(response, request_id)
        
        result = data['result']
        self.assertIn('description', result)
        self.assertIn('messages', result)
        
        # Validate messages structure
        messages = result['messages']
        self.assertIsInstance(messages, list)
        
        for message in messages:
            self.assertIn('role', message)
            self.assertIn('content', message)
            
            # Content should have type and text
            content = message['content']
            self.assertIn('type', content)
            if content['type'] == 'text':
                self.assertIn('text', content)
        
        print(f"✅ Prompts get working - retrieved prompt {test_prompt['name']}")
    
    def test_026_prompts_get_error_handling(self):
        """Test MCP prompts/get error handling"""
        test_cases = [
            ({}, "Missing prompt name"),
            ({"name": ""}, "Empty prompt name"),
            ({"name": "nonexistent_prompt"}, "Nonexistent prompt"),
        ]
        
        for params, description in test_cases:
            with self.subTest(params=params, description=description):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("prompts/get", params, request_id)
                
                # Should return error for all invalid cases
                data = response.json()
                self.assertEqual(data.get('jsonrpc'), '2.0')
                self.assertIn('error', data)
                self.assertEqual(data['error']['code'], -32602)  # Invalid params
        
        print("✅ Prompts get error handling working")
    
    def test_027_logging_setLevel(self):
        """Test MCP logging/setLevel method"""
        valid_levels = ['debug', 'info', 'notice', 'warning', 'error', 'critical', 'alert', 'emergency']
        
        # Test valid log levels
        for level in ['info', 'warning', 'error']:
            with self.subTest(level=level):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("logging/setLevel", {"level": level}, request_id)
                data = self.assert_valid_jsonrpc_response(response, request_id)
                
                # Should return empty result for successful level set
                result = data['result']
                self.assertEqual(result, {})
        
        print("✅ Logging setLevel working")
    
    def test_028_logging_setLevel_error_handling(self):
        """Test MCP logging/setLevel error handling"""
        test_cases = [
            ({}, "Missing level"),
            ({"level": ""}, "Empty level"),
            ({"level": "invalid_level"}, "Invalid level"),
            ({"level": "DEBUG"}, "Case sensitive level"),
        ]
        
        for params, description in test_cases:
            with self.subTest(params=params, description=description):
                request_id = self.get_next_request_id()
                response = self.make_mcp_request("logging/setLevel", params, request_id)
                
                # Should return error for all invalid cases
                data = response.json()
                self.assertEqual(data.get('jsonrpc'), '2.0')
                self.assertIn('error', data)
                self.assertEqual(data['error']['code'], -32602)  # Invalid params
        
        print("✅ Logging setLevel error handling working")
    
    def test_029_enhanced_capabilities_validation(self):
        """Test enhanced MCP capabilities from October 2025 spec"""
        request_id = self.get_next_request_id()
        response = self.make_mcp_request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "enhanced-test", "version": "1.0.0"}
        }, request_id)
        
        data = self.assert_valid_jsonrpc_response(response, request_id)
        capabilities = data['result']['capabilities']
        
        # Validate enhanced capabilities structure
        expected_capabilities = {
            'tools': {'listChanged': bool},
            'resources': {'subscribe': bool, 'listChanged': bool},
            'prompts': {'listChanged': bool},
            'logging': {}
        }
        
        for cap_name, cap_structure in expected_capabilities.items():
            self.assertIn(cap_name, capabilities, f"Missing capability: {cap_name}")
            
            if isinstance(cap_structure, dict):
                for field, field_type in cap_structure.items():
                    if field in capabilities[cap_name]:
                        self.assertIsInstance(capabilities[cap_name][field], field_type)
        
        print("✅ Enhanced capabilities validation working")
    
    def test_030_complete_mcp_workflow(self):
        """Test complete MCP workflow with all capabilities"""
        # 1. Initialize with full capabilities
        request_id = self.get_next_request_id()
        init_response = self.make_mcp_request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "logging": {}
            },
            "clientInfo": {"name": "workflow-test", "version": "1.0.0"}
        }, request_id)
        self.assert_valid_jsonrpc_response(init_response, request_id)
        
        # 2. Initialized notification
        request_id = self.get_next_request_id()
        initialized_response = self.make_mcp_request("initialized", {}, request_id)
        self.assert_valid_jsonrpc_response(initialized_response, request_id)
        
        # 3. List tools
        request_id = self.get_next_request_id()
        tools_response = self.make_mcp_request("tools/list", {}, request_id)
        self.assert_valid_jsonrpc_response(tools_response, request_id)
        
        # 4. List resources
        request_id = self.get_next_request_id()
        resources_response = self.make_mcp_request("resources/list", {}, request_id)
        self.assert_valid_jsonrpc_response(resources_response, request_id)
        
        # 5. List prompts
        request_id = self.get_next_request_id()
        prompts_response = self.make_mcp_request("prompts/list", {}, request_id)
        self.assert_valid_jsonrpc_response(prompts_response, request_id)
        
        # 6. Set logging level
        request_id = self.get_next_request_id()
        logging_response = self.make_mcp_request("logging/setLevel", {"level": "info"}, request_id)
        self.assert_valid_jsonrpc_response(logging_response, request_id)
        
        # 7. Use a tool
        request_id = self.get_next_request_id()
        tool_call_response = self.make_mcp_request("tools/call", {
            "name": "get_pets_summary",
            "arguments": {}
        }, request_id)
        self.assert_valid_jsonrpc_response(tool_call_response, request_id)
        
        print("✅ Complete MCP workflow working - all capabilities tested")

def run_mcp_compliance_tests():
    """Run the complete MCP compliance test suite"""
    print("🔍 MCP (Model Context Protocol) Compliance Test Suite")
    print("📋 Testing against October 2025 MCP Specification")  
    print("=" * 60)
    
    # Create test loader to run tests in order
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(MCPComplianceTest)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    print(f"🔍 MCP Compliance Tests Completed!")
    print(f"✅ Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests failed: {len(result.failures)}")
    print(f"🚨 Tests errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # Return success status
    return len(result.failures) + len(result.errors) == 0

if __name__ == "__main__":
    success = run_mcp_compliance_tests()
    sys.exit(0 if success else 1)
