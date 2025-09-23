#!/usr/bin/env python3
"""
Comprehensive test suite for Pet Adoption API
Can be run from command line or in CI/CD pipelines

Usage:
    python test_api.py              # Run with unittest
    pytest test_api.py              # Run with pytest (recommended)
    pytest test_api.py -v           # Verbose output
    pytest test_api.py --tb=short   # Short traceback format
"""

import unittest
import requests
import json
import time
import sys
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://127.0.0.1:5001"
TIMEOUT = 10  # seconds

class PetAdoptionAPITest(unittest.TestCase):
    """Test suite for Pet Adoption API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment - check if API is running"""
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=TIMEOUT)
            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}")
            print("✅ API server is running and responsive")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to API at {API_BASE_URL}")
            print(f"Error: {e}")
            print("Please make sure the Flask app is running: python app.py")
            sys.exit(1)
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = API_BASE_URL
        self.headers = {'Content-Type': 'application/json'}
        
    def test_001_api_info(self):
        """Test GET / - API information endpoint"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('endpoints', data)
        self.assertIsInstance(data['endpoints'], dict)
        
        # Should have 14 endpoints
        self.assertEqual(len(data['endpoints']), 14)
        print(f"✅ API info endpoint working - {len(data['endpoints'])} endpoints")
    
    def test_002_get_all_pets(self):
        """Test GET /pets - Get all pets"""
        response = requests.get(f"{self.base_url}/pets")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Validate pet structure if pets exist
        if data:
            pet = data[0]
            required_fields = ['id', 'name', 'species', 'is_adopted', 'created_at']
            for field in required_fields:
                self.assertIn(field, pet)
        
        print(f"✅ Get all pets working - {len(data)} pets found")
    
    def test_003_get_pets_summary(self):
        """Test GET /pets/summary - Get pet statistics"""
        response = requests.get(f"{self.base_url}/pets/summary")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('summary_by_species', data)
        self.assertIn('overall_totals', data)
        
        totals = data['overall_totals']
        required_fields = ['total_pets', 'available_pets', 'adopted_pets']
        for field in required_fields:
            self.assertIn(field, totals)
            self.assertIsInstance(totals[field], int)
        
        print(f"✅ Pet summary working - {totals['total_pets']} total pets")
    
    def test_004_get_available_pets(self):
        """Test GET /pets/available - Get available pets only"""
        response = requests.get(f"{self.base_url}/pets/available")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        # All pets should be available (not adopted)
        for pet in data:
            self.assertFalse(pet['is_adopted'])
        
        print(f"✅ Get available pets working - {len(data)} available pets")
    
    def test_005_get_valid_species(self):
        """Test GET /pets/species - Get valid species list"""
        response = requests.get(f"{self.base_url}/pets/species")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('species', data)
        self.assertIn('existing_in_database', data)
        self.assertIn('common_options', data)
        
        self.assertIsInstance(data['species'], list)
        self.assertIsInstance(data['existing_in_database'], list)
        self.assertIsInstance(data['common_options'], list)
        
        print(f"✅ Valid species working - {len(data['species'])} species available")
    
    def test_006_search_pets(self):
        """Test GET /pets/search - Search pets with filters"""
        # Test search without filters
        response = requests.get(f"{self.base_url}/pets/search")
        self.assertEqual(response.status_code, 200)
        all_pets = response.json()
        
        # Test search with available_only filter
        response = requests.get(f"{self.base_url}/pets/search?available_only=true")
        self.assertEqual(response.status_code, 200)
        available_pets = response.json()
        
        # Available pets should be subset of all pets
        self.assertLessEqual(len(available_pets), len(all_pets))
        
        # Test search with species filter
        response = requests.get(f"{self.base_url}/pets/search?species=Dog")
        self.assertEqual(response.status_code, 200)
        dog_pets = response.json()
        
        for pet in dog_pets:
            self.assertIn('Dog', pet['species'])
        
        print(f"✅ Search pets working - various filters tested")
    
    def test_007_create_pet(self):
        """Test POST /pets - Create new pet"""
        new_pet = {
            "name": "Test Pet",
            "species": "Dog",
            "breed": "Test Breed",
            "age": 2,
            "description": "Test pet for API testing"
        }
        
        response = requests.post(f"{self.base_url}/pets", 
                               json=new_pet, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], new_pet['name'])
        self.assertEqual(data['species'], new_pet['species'])
        self.assertFalse(data['is_adopted'])
        
        # Cleanup the created pet
        pet_id = data['id']
        requests.delete(f"{self.base_url}/pets/{pet_id}")
        
        print(f"✅ Create pet working - created and cleaned up pet ID {pet_id}")
    
    def test_008_create_pet_validation(self):
        """Test POST /pets - Validation errors"""
        # Test missing required fields
        invalid_pet = {"description": "Missing name and species"}
        
        response = requests.post(f"{self.base_url}/pets", 
                               json=invalid_pet, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
        
        print("✅ Create pet validation working")
    
    def test_009_get_pet_by_id(self):
        """Test GET /pets/<id> - Get specific pet"""
        # First create a pet to get
        new_pet = {
            "name": "Get Test Pet",
            "species": "Dog",
            "breed": "Test Breed",
            "age": 2,
            "description": "Test pet for get by ID testing"
        }
        
        create_response = requests.post(f"{self.base_url}/pets", 
                                      json=new_pet, headers=self.headers)
        self.assertEqual(create_response.status_code, 201)
        pet_id = create_response.json()['id']
        
        # Test getting the pet
        response = requests.get(f"{self.base_url}/pets/{pet_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['id'], pet_id)
        self.assertEqual(data['name'], new_pet['name'])
        self.assertEqual(data['species'], new_pet['species'])
        
        # Cleanup
        requests.delete(f"{self.base_url}/pets/{pet_id}")
        
        print(f"✅ Get pet by ID working - retrieved pet {pet_id}")
    
    def test_010_get_pet_not_found(self):
        """Test GET /pets/<id> - Pet not found"""
        response = requests.get(f"{self.base_url}/pets/99999")
        self.assertEqual(response.status_code, 404)
        
        print("✅ Get pet not found handling working")
    
    def test_011_update_pet(self):
        """Test PUT /pets/<id> - Update pet information"""
        # First create a pet to update
        new_pet = {
            "name": "Update Test Pet",
            "species": "Cat",
            "breed": "Persian",
            "age": 2,
            "description": "Pet for update testing"
        }
        
        create_response = requests.post(f"{self.base_url}/pets", 
                                      json=new_pet, headers=self.headers)
        self.assertEqual(create_response.status_code, 201)
        pet_id = create_response.json()['id']
        
        # Update the pet
        updates = {
            "name": "Updated Test Pet",
            "age": 3,
            "description": "Updated description"
        }
        
        response = requests.put(f"{self.base_url}/pets/{pet_id}", 
                              json=updates, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['name'], updates['name'])
        self.assertEqual(data['age'], updates['age'])
        self.assertEqual(data['description'], updates['description'])
        
        # Cleanup
        requests.delete(f"{self.base_url}/pets/{pet_id}")
        
        print(f"✅ Update pet working - updated pet {pet_id}")
    
    def test_012_adopt_pet_by_id(self):
        """Test PUT /pets/<id>/adopt - Adopt pet by ID"""
        # First create a pet to adopt
        new_pet = {
            "name": "Adopt Test Pet ID",
            "species": "Bird",
            "breed": "Canary",
            "age": 1,
            "description": "Pet for adoption testing by ID"
        }
        
        create_response = requests.post(f"{self.base_url}/pets", 
                                      json=new_pet, headers=self.headers)
        self.assertEqual(create_response.status_code, 201)
        pet_id = create_response.json()['id']
        
        # Adopt the pet
        response = requests.put(f"{self.base_url}/pets/{pet_id}/adopt")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['is_adopted'])
        
        # Cleanup
        requests.delete(f"{self.base_url}/pets/{pet_id}")
        
        print(f"✅ Adopt pet by ID working - adopted pet {pet_id}")
    
    def test_013_adopt_pet_by_name(self):
        """Test PUT /pets/adopt?name=<name> - Adopt pet by name"""
        # First create a pet to adopt
        new_pet = {
            "name": "Adopt Test Pet Name",
            "species": "Rabbit",
            "breed": "Holland Lop",
            "age": 1,
            "description": "Pet for adoption testing by name"
        }
        
        create_response = requests.post(f"{self.base_url}/pets", 
                                      json=new_pet, headers=self.headers)
        self.assertEqual(create_response.status_code, 201)
        pet_id = create_response.json()['id']
        
        # Adopt the pet by name
        response = requests.put(f"{self.base_url}/pets/adopt?name=Adopt Test Pet Name")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('pet', data)
        self.assertTrue(data['pet']['is_adopted'])
        
        # Cleanup
        requests.delete(f"{self.base_url}/pets/{pet_id}")
        
        print("✅ Adopt pet by name working")
    
    def test_014_adopt_pet_validation(self):
        """Test adoption validation - already adopted, not found"""
        # Test adopting non-existent pet
        response = requests.put(f"{self.base_url}/pets/adopt?name=NonExistentPet")
        self.assertEqual(response.status_code, 404)
        
        # Test missing name parameter
        response = requests.put(f"{self.base_url}/pets/adopt")
        self.assertEqual(response.status_code, 400)
        
        print("✅ Adopt pet validation working")
    
    def test_015_create_multiple_pets(self):
        """Test POST /pets/batch - Create multiple pets"""
        pets_data = {
            "pets": [
                {
                    "name": "Batch Pet 1",
                    "species": "Cat",
                    "breed": "Persian",
                    "age": 1
                },
                {
                    "name": "Batch Pet 2", 
                    "species": "Dog",
                    "breed": "Labrador",
                    "age": 2
                }
            ]
        }
        
        response = requests.post(f"{self.base_url}/pets/batch", 
                               json=pets_data, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('created_pets', data)
        self.assertEqual(len(data['created_pets']), 2)
        
        # Cleanup created pets
        for pet in data['created_pets']:
            requests.delete(f"{self.base_url}/pets/{pet['id']}")
        
        print("✅ Create multiple pets working")
    
    def test_016_delete_pet(self):
        """Test DELETE /pets/<id> - Delete pet"""
        # First create a pet to delete
        new_pet = {
            "name": "Delete Test Pet",
            "species": "Hamster",
            "breed": "Syrian",
            "age": 1,
            "description": "Pet for deletion testing"
        }
        
        create_response = requests.post(f"{self.base_url}/pets", 
                                      json=new_pet, headers=self.headers)
        self.assertEqual(create_response.status_code, 201)
        pet_id = create_response.json()['id']
        
        # Delete the pet
        response = requests.delete(f"{self.base_url}/pets/{pet_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('message', data)
        
        # Verify pet is deleted
        response = requests.get(f"{self.base_url}/pets/{pet_id}")
        self.assertEqual(response.status_code, 404)
        
        print(f"✅ Delete pet working - deleted pet {pet_id}")
    
    def test_017_tools_list(self):
        """Test GET /tools/list - Get MCP tool definitions"""
        response = requests.get(f"{self.base_url}/tools/list")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('tools', data)
        self.assertIsInstance(data['tools'], list)
        
        # Should have 7 simplified tools
        self.assertEqual(len(data['tools']), 7)
        
        # Validate tool structure
        for tool in data['tools']:
            required_fields = ['name', 'title', 'description', 'inputSchema']
            for field in required_fields:
                self.assertIn(field, tool)
        
        print(f"✅ Tools list working - {len(data['tools'])} tools defined")
    
    def test_018_mcp_initialize(self):
        """Test MCP server initialization"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = requests.post(f"{self.base_url}/mcp", 
                               json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['jsonrpc'], '2.0')
        self.assertEqual(data['id'], 1)
        self.assertIn('result', data)
        
        result = data['result']
        self.assertIn('protocolVersion', result)
        self.assertIn('capabilities', result)
        self.assertIn('serverInfo', result)
        
        print("✅ MCP initialization working")
    
    def test_019_mcp_tools_list(self):
        """Test MCP tools/list method"""
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = requests.post(f"{self.base_url}/mcp", 
                               json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['jsonrpc'], '2.0')
        self.assertEqual(data['id'], 2)
        self.assertIn('result', data)
        
        result = data['result']
        self.assertIn('tools', result)
        self.assertEqual(len(result['tools']), 7)
        
        print("✅ MCP tools/list working")
    
    def test_020_mcp_tools_call(self):
        """Test MCP tools/call method"""
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_pets_summary",
                "arguments": {}
            }
        }
        
        response = requests.post(f"{self.base_url}/mcp", 
                               json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['jsonrpc'], '2.0')
        self.assertEqual(data['id'], 3)
        self.assertIn('result', data)
        
        result = data['result']
        self.assertIn('content', result)
        self.assertFalse(result.get('isError', True))
        
        # Parse the content
        content_text = result['content'][0]['text']
        summary_data = json.loads(content_text)
        self.assertIn('overall_totals', summary_data)
        
        print("✅ MCP tools/call working")
    
    def test_021_mcp_error_handling(self):
        """Test MCP error handling"""
        # Test invalid method
        payload = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "invalid_method",
            "params": {}
        }
        
        response = requests.post(f"{self.base_url}/mcp", 
                               json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['jsonrpc'], '2.0')
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], -32601)  # Method not found
        
        print("✅ MCP error handling working")
    
    def test_022_cors_headers(self):
        """Test CORS headers are present"""
        response = requests.get(f"{self.base_url}/")
        
        # Check for CORS headers (Flask-CORS should add these)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        
        print("✅ CORS headers working")
    
    def test_023_removed_streaming_endpoints(self):
        """Test that streaming endpoints are properly removed"""
        streaming_endpoints = [
            '/pets/stream',
            '/events/adoptions', 
            '/pets/batch/stream',
            '/status/stream'
        ]
        
        for endpoint in streaming_endpoints:
            response = requests.get(f"{self.base_url}{endpoint}")
            self.assertEqual(response.status_code, 404)
        
        print("✅ Streaming endpoints properly removed")


def run_tests():
    """Run the test suite"""
    print("🧪 Starting Pet Adoption API Test Suite")
    print("=" * 50)
    
    # Run tests
    unittest.main(verbosity=2, exit=False, argv=[''])
    
    print("=" * 50)
    print("✅ Test suite completed!")


if __name__ == "__main__":
    run_tests()

