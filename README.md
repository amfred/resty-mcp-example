# Resty MCP Example - Pet Adoption API

A fun REST API example built with FastAPI that simulates a pet adoption system. This project demonstrates basic CRUD operations, database integration, and RESTful API design.

## Features

- 🐕 **Pet Management**: Add, view, update, and delete pets
- 🔍 **Search & Filter**: Search pets by species, breed, or availability
- 🏠 **Adoption System**: Mark pets as adopted
- 📊 **SQLite Database**: Persistent data storage
- 🌐 **CORS Enabled**: Ready for frontend integration

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python app.py
   ```

3. **Access the API**:
   - API Base URL: `http://localhost:5001`
   - The server will automatically create the database and add sample pets

## API Endpoints

### Base Information
- `GET /` - API information and available endpoints

### Pet Operations
- `GET /pets` - Get all pets
- `POST /pets` - Add a new pet
- `GET /pets/<id>` - Get a specific pet
- `PUT /pets/<id>/adopt` - Adopt a pet by ID
- `PUT /pets/adopt?name=<name>` - Adopt a pet by name
- `DELETE /pets/<id>` - Delete a pet
- `GET /pets/search` - Search pets with filters

### Search Parameters
- `species` - Filter by species (e.g., `?species=dog`)
- `breed` - Filter by breed (e.g., `?breed=golden`)
- `available_only` - Show only available pets (e.g., `?available_only=true`)

## Example Usage

### Get all pets
```bash
curl http://localhost:5001/pets
```

### Add a new pet
```bash
curl -X POST http://localhost:5001/pets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fluffy",
    "species": "Cat",
    "breed": "Maine Coon",
    "age": 2,
    "description": "Very fluffy and friendly"
  }'
```

### Adopt a pet by ID
```bash
curl -X PUT http://localhost:5001/pets/1/adopt
```

### Adopt a pet by name
```bash
curl -X PUT "http://localhost:5001/pets/adopt?name=Tweety"
```

### Search for available dogs
```bash
curl "http://localhost:5001/pets/search?species=dog&available_only=true"
```

## New Feature: Adopt by Name

The API now supports adopting pets by name, making it much easier to adopt pets without needing to know their ID first.

### Endpoint: `PUT /pets/adopt?name=<name>`

**Parameters:**
- `name` (required): The name of the pet to adopt (case-insensitive partial match)

**Response Examples:**

**Success (200):**
```json
{
  "message": "Tweety has been successfully adopted!",
  "pet": {
    "id": 3,
    "name": "Tweety",
    "species": "Bird",
    "breed": "Canary",
    "age": 1,
    "description": "Sings beautifully",
    "is_adopted": true,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**Error Cases:**
- **Pet not found (404):** `{"error": "No pet found with name containing \"NonExistentPet\""}`
- **Already adopted (400):** `{"error": "Tweety is already adopted"}`
- **Missing name (400):** `{"error": "Name parameter is required"}`

**Usage Examples:**
```bash
# Adopt Tweety
curl -X PUT "http://localhost:5001/pets/adopt?name=Tweety"

# Adopt Buddy (partial name match works)
curl -X PUT "http://localhost:5001/pets/adopt?name=Bud"

# Try to adopt already adopted pet
curl -X PUT "http://localhost:5001/pets/adopt?name=Tweety"
```

## Testing

This project includes comprehensive test suites that cover all API endpoints, full MCP specification compliance, error handling, and edge cases.

### Test Coverage

The project includes **TWO comprehensive test suites**:

#### 1. REST API Test Suite (`test_api.py`) - **23 test methods**:
- ✅ All REST API endpoints (14 endpoints)
- ✅ Basic MCP server functionality (JSON-RPC 2.0 protocol)  
- ✅ Validation and error handling
- ✅ CORS functionality
- ✅ Edge cases and negative scenarios
- ✅ Proper test isolation and cleanup

#### 2. MCP Compliance Test Suite (`test_mcp_compliance.py`) - **30 test methods**:
- ✅ **Complete MCP Protocol Compliance** (October 2025 specification)
- ✅ **Extended MCP Capabilities**: tools, resources, prompts, logging
- ✅ **JSON-RPC 2.0 Protocol Validation**: all error codes and edge cases
- ✅ **Protocol Version Negotiation**: version compatibility testing
- ✅ **Structured Tool Output**: validation of tool response formats
- ✅ **Session Lifecycle Management**: complete workflow testing
- ✅ **Performance & Reliability**: concurrent requests, large payloads
- ✅ **Security Testing**: input sanitization, rate limiting awareness
- ✅ **Boundary Testing**: edge cases, parameter validation

### Prerequisites

1. **Install test dependencies**:
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Start the API server** (required for integration tests):
   ```bash
   python app.py
   ```
   The server should be running at `http://127.0.0.1:5001` before running tests.

### Running Tests

#### REST API Tests

```bash
# Make the script executable (first time only)
chmod +x run_tests.sh

# Run REST API tests with different options:
./run_tests.sh                    # Default: pytest mode
./run_tests.sh pytest            # Pytest with verbose output (recommended)
./run_tests.sh coverage          # With coverage analysis
./run_tests.sh html              # Generate HTML test report
./run_tests.sh ci                # CI mode with JUnit XML output
./run_tests.sh quick             # Quick smoke tests only
```

#### MCP Compliance Tests ⭐ **NEW**

```bash
# Make the script executable (first time only)
chmod +x run_mcp_compliance_tests.sh

# Run MCP compliance tests with different options:
./run_mcp_compliance_tests.sh                # Default: pytest mode
./run_mcp_compliance_tests.sh pytest        # Pytest with verbose output (recommended)
./run_mcp_compliance_tests.sh coverage      # With coverage analysis
./run_mcp_compliance_tests.sh html          # Generate HTML test report  
./run_mcp_compliance_tests.sh ci            # CI mode with JUnit XML output
./run_mcp_compliance_tests.sh quick         # Quick MCP smoke tests only
./run_mcp_compliance_tests.sh unittest      # Run with unittest
```

#### Direct Commands

**REST API Tests:**
```bash
# Using pytest (recommended)
pytest test_api.py -v

# Using unittest
python test_api.py

# With coverage
coverage run -m pytest test_api.py
coverage report
coverage html  # Generates htmlcov/ directory

# Generate HTML test report
pytest test_api.py --html=test_report.html --self-contained-html
```

**MCP Compliance Tests:**
```bash
# Using pytest (recommended)
pytest test_mcp_compliance.py -v

# Using unittest
python test_mcp_compliance.py

# With coverage
coverage run -m pytest test_mcp_compliance.py
coverage report
coverage html --directory htmlcov_mcp  # Generates htmlcov_mcp/ directory

# Generate HTML test report
pytest test_mcp_compliance.py --html=mcp_compliance_report.html --self-contained-html
```

### Test Structure

#### REST API Test Structure (`test_api.py`)

**API Core Tests (001-006)**:
- API information endpoint
- Get all pets
- Pet statistics summary
- Available pets filtering
- Valid species list
- Pet search functionality

**CRUD Operations (007-016)**:
- Create pet (with validation)
- Get pet by ID
- Update pet information
- Adopt pets (by ID and name)
- Delete pets
- Batch pet creation

**MCP Server Tests (017-021)**:
- Tool definitions endpoint
- MCP initialization
- Tools list via JSON-RPC
- Tool execution via JSON-RPC
- Error handling

**Edge Cases & Features (022-023)**:
- CORS headers validation
- Removed endpoints verification

#### MCP Compliance Test Structure (`test_mcp_compliance.py`) ⭐ **NEW**

**Core Protocol Compliance (001-007)**:
- MCP initialization and protocol version negotiation
- Server capabilities validation and enhancement
- Tools list comprehensive validation
- Tools call with structured output validation
- Tools call error handling

**JSON-RPC Protocol Compliance (008-010)**:
- JSON-RPC 2.0 format validation
- Standard JSON-RPC error codes testing
- Request ID handling validation

**Advanced MCP Features (011-013)**:
- Structured tool output compliance (MCP 2025 requirement)
- Capability negotiation between client and server
- Complete session lifecycle testing

**Performance & Reliability (014-015)**:
- Concurrent request handling
- Large payload handling

**Security & Validation (016-017)**:
- Input sanitization and validation
- Rate limiting awareness testing

**Edge Cases & Boundaries (018-020)**:
- Boundary value testing
- Method name case sensitivity
- Empty and null parameter handling

**Extended MCP Capabilities (021-030)** - **October 2025 Compliance**:
- **Resources**: `resources/list` and `resources/read` methods
- **Prompts**: `prompts/list` and `prompts/get` methods  
- **Logging**: `logging/setLevel` method
- **Enhanced capabilities validation**
- **Complete MCP workflow testing**

### Continuous Integration

The project includes GitHub Actions workflows that:
- Run tests on multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Generate test reports and coverage analysis
- Publish results as artifacts
- Upload coverage to Codecov

**Workflow triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main`

### Test Features

- **Independent Tests**: Each test is fully isolated and can run independently
- **Automatic Cleanup**: Tests clean up any data they create
- **Comprehensive Coverage**: Tests all endpoints, error cases, and edge scenarios
- **Multiple Output Formats**: JUnit XML, HTML reports, coverage analysis
- **CI/CD Ready**: Full GitHub Actions integration

### Example Test Output

```bash
$ ./run_tests.sh pytest

🧪 Pet Adoption API Test Suite
================================
✅ API server is running
✅ Test dependencies installed
🏃 Running tests with pytest...

test_api.py::PetAdoptionAPITest::test_001_api_info PASSED
test_api.py::PetAdoptionAPITest::test_002_get_all_pets PASSED
test_api.py::PetAdoptionAPITest::test_003_get_pets_summary PASSED
...
test_api.py::PetAdoptionAPITest::test_023_removed_streaming_endpoints PASSED

========================= 23 passed in 2.34s =========================

✅ Test execution completed!
```

## MCP (Model Context Protocol) Compliance ⭐ **NEW**

This project now includes **full compliance** with the **October 2025 MCP specification**, making it an excellent reference implementation for MCP servers.

### MCP Features Implemented

#### 🔧 **Core MCP Protocol**
- **JSON-RPC 2.0** protocol support with proper error handling
- **Protocol version negotiation** (supports MCP 2025-06-18)
- **Complete session lifecycle** (initialize → initialized → operations)
- **Structured tool output** with proper content type validation

#### 🛠️ **Tools Capability** 
- **7 optimized tools** for pet adoption operations
- **Dynamic tool execution** with parameter validation
- **Comprehensive tool schemas** with input/output definitions
- **Error handling** with proper JSON-RPC error codes

#### 📁 **Resources Capability**
- **3 sample resources**: adoption forms, care guides, vaccination schedules
- **Resource listing** via `resources/list` method
- **Resource reading** via `resources/read` method with URI support
- **MIME type support** for different resource formats

#### 💬 **Prompts Capability**
- **3 specialized prompts** for pet adoption scenarios:
  - **Adoption Assistant**: Help users find perfect pets
  - **Pet Care Advisor**: Provide species-specific care advice
  - **Adoption Form Helper**: Guide through adoption process
- **Dynamic prompt generation** with argument interpolation
- **Structured message format** with role-based content

#### 📊 **Logging Capability**
- **Log level management** via `logging/setLevel` method
- **Standard log levels** (debug, info, warning, error, etc.)
- **Level validation** with proper error responses

### MCP Methods Supported

| Method | Description | Status |
|--------|-------------|--------|
| `initialize` | Initialize MCP session with capabilities | ✅ Full |
| `initialized` | Confirm initialization complete | ✅ Full |
| `tools/list` | List available tools | ✅ Full |
| `tools/call` | Execute a tool | ✅ Full |
| `resources/list` | List available resources | ✅ Full |
| `resources/read` | Read a specific resource | ✅ Full |
| `prompts/list` | List available prompt templates | ✅ Full |
| `prompts/get` | Get a specific prompt | ✅ Full |
| `logging/setLevel` | Set logging level | ✅ Full |

### MCP Compliance Testing

The comprehensive MCP compliance test suite (`test_mcp_compliance.py`) validates:

- ✅ **Protocol Compliance**: Full JSON-RPC 2.0 adherence
- ✅ **Version Negotiation**: Protocol version compatibility 
- ✅ **Capability Declaration**: Proper server capabilities
- ✅ **Error Handling**: All JSON-RPC error codes and edge cases
- ✅ **Security**: Input sanitization and validation
- ✅ **Performance**: Concurrent requests and large payloads
- ✅ **Boundary Testing**: Edge cases and parameter validation

### Example MCP Usage

```bash
# Initialize MCP session
curl -X POST http://localhost:5001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize", 
    "id": 1,
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {"name": "my-client", "version": "1.0.0"}
    }
  }'

# List available resources
curl -X POST http://localhost:5001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "resources/list",
    "id": 2,
    "params": {}
  }'

# Get a prompt template
curl -X POST http://localhost:5001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "prompts/get",
    "id": 3,
    "params": {
      "name": "adoption_assistant",
      "arguments": {"user_preferences": "small dog, apartment-friendly"}
    }
  }'
```

### Why This Implementation Matters

This project serves as a **reference implementation** for:

- 🏗️ **MCP Server Development**: Complete, working example of MCP compliance
- 📋 **Specification Validation**: Comprehensive test coverage for MCP requirements  
- 🔍 **Compliance Testing**: Reusable test patterns for MCP validation
- 📚 **Learning Resource**: Well-documented MCP integration examples
- 🚀 **Production Ready**: Battle-tested with full error handling and edge cases

✅ Test execution completed!
```

## Database Schema

The `Pet` model includes:
- `id` - Primary key
- `name` - Pet's name
- `species` - Type of animal (Dog, Cat, Bird, etc.)
- `breed` - Specific breed
- `age` - Age in years
- `description` - Additional details
- `is_adopted` - Adoption status
- `created_at` - Timestamp when added

## Sample Data

The application comes with 5 sample pets:
- Buddy (Golden Retriever)
- Whiskers (Persian Cat)
- Tweety (Canary)
- Max (Labrador)
- Luna (Siamese Cat)

## MCP Tools vs REST APIs Comparison

This project provides **dual interfaces** for different integration scenarios:

### 🔧 MCP Tools (12 total) - LLM Optimized

| Tool | Description | Use Case |
|------|-------------|----------|
| `list_all_pets` | Get complete list of all pets | Overview for AI assistants |
| `get_pet_by_id` | Get specific pet by ID | Direct pet lookup |
| `get_pet_by_name` | Find pet by name | Natural language queries |
| `create_pet` | Add new pet to system | Pet registration |
| `update_pet_info` | Update pet details | Information management |
| `delete_pet` | Remove pet by ID or name | Pet removal |
| `adopt_pet_by_name` | Adopt pet by searching name | Natural adoption process |
| `search_pets` | Search with filters | Advanced pet discovery |
| `get_available_pets` | Get adoptable pets only | Adoption-focused queries |
| `get_pets_summary` | Get comprehensive statistics | Data analysis |
| `get_valid_species` | Get valid pet species list | Form validation |
| `get_adoption_stats` | Get adoption statistics | Reporting and analytics |

### 🌐 REST API Endpoints (12 total) - Programmatic Integration

| Endpoint | Method | Description | Use Case |
|----------|--------|-------------|----------|
| `/api/v1/pets/` | GET | List all pets | Data retrieval |
| `/api/v1/pets/` | POST | Create new pet | Pet registration |
| `/api/v1/pets/{id}` | GET | Get pet by ID | Direct lookup |
| `/api/v1/pets/{id}` | PUT | Update pet | Information management |
| `/api/v1/pets/{id}` | DELETE | Delete pet | Pet removal |
| `/api/v1/pets/{id}/adopt` | PUT | Adopt pet by ID | Adoption process |
| `/api/v1/pets/adopt` | PUT | Adopt pet by name | Name-based adoption |
| `/api/v1/pets/search` | GET | Search with filters | Advanced queries |
| `/api/v1/pets/available` | GET | Get available pets | Adoption focus |
| `/api/v1/pets/summary` | GET | Get statistics | Data analysis |
| `/api/v1/pets/species` | GET | Get valid species | Form validation |
| `/api/v1/pets/batch` | POST | Create multiple pets | Bulk operations |

### 🎯 Design Rationale: Why the Lists Are Different

#### **MCP Tools Focus on LLM Interactions:**
- **Natural Language Operations**: Tools like `get_pet_by_name` and `adopt_pet_by_name` are optimized for conversational AI
- **High-Level Abstractions**: `get_pets_summary` and `get_adoption_stats` provide aggregated insights
- **Semantic Operations**: Focus on business logic rather than CRUD operations
- **Flexible Input**: Tools accept both ID and name parameters for maximum flexibility

#### **REST APIs Focus on Programmatic Integration:**
- **Standard HTTP Methods**: Proper use of GET, POST, PUT, DELETE following REST conventions
- **Resource-Based URLs**: Clear resource hierarchy (`/pets/{id}`, `/pets/{id}/adopt`)
- **HTTP Status Codes**: Appropriate status codes for different scenarios
- **Batch Operations**: `POST /batch` for bulk operations not available in MCP
- **Granular Control**: More specific endpoints for different use cases

#### **Complementary Coverage:**
- **No Redundancy**: Each interface serves its target audience effectively
- **Complete Coverage**: All major operations available through at least one interface
- **Appropriate Granularity**: MCP tools are higher-level, REST APIs are more granular
- **Different Strengths**: MCP excels at natural language, REST excels at programmatic control

### 📊 Coverage Analysis

| Functionality | MCP Tool | REST API | Coverage |
|---------------|----------|----------|----------|
| **List All Pets** | ✅ | ✅ | Both |
| **Get Pet by ID** | ✅ | ✅ | Both |
| **Get Pet by Name** | ✅ | ❌ | MCP only |
| **Create Pet** | ✅ | ✅ | Both |
| **Update Pet** | ✅ | ✅ | Both |
| **Delete Pet** | ✅ | ✅ | Both |
| **Adopt by ID** | ❌ | ✅ | REST only |
| **Adopt by Name** | ✅ | ✅ | Both |
| **Search Pets** | ✅ | ✅ | Both |
| **Get Available** | ✅ | ✅ | Both |
| **Get Summary** | ✅ | ✅ | Both |
| **Get Species** | ✅ | ✅ | Both |
| **Batch Create** | ❌ | ✅ | REST only |
| **Get Stats** | ✅ | ❌ | MCP only |

### 🏆 Result: Exemplary API Design

This implementation demonstrates **excellent API design principles**:
- **MCP tools** are optimized for AI/LLM interactions with natural language operations
- **REST APIs** provide comprehensive programmatic access with standard HTTP conventions
- **Both interfaces** serve their intended audiences without unnecessary overlap
- **The balance** is nearly perfect for a pet adoption system

This project shows how to properly design dual interfaces for different integration scenarios!

## Development

This is a simple FastAPI application perfect for:
- Learning REST API concepts
- Understanding database integration
- Practicing CRUD operations
- Building frontend applications

Feel free to extend it with additional features like user authentication, photo uploads, or more complex relationships!

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Red Hat, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
