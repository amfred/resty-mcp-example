# Resty MCP Example - Pet Adoption API

A fun REST API example built with Flask that simulates a pet adoption system. This project demonstrates basic CRUD operations, database integration, and RESTful API design.

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

This project includes a comprehensive test suite that covers all API endpoints, MCP functionality, error handling, and edge cases.

### Test Coverage

The test suite includes **23 test methods** covering:
- ✅ All REST API endpoints (14 endpoints)
- ✅ MCP server functionality (JSON-RPC 2.0 protocol)
- ✅ Validation and error handling
- ✅ CORS functionality
- ✅ Edge cases and negative scenarios
- ✅ Proper test isolation and cleanup

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

#### Using the Test Runner Script (Recommended)

```bash
# Make the script executable (first time only)
chmod +x run_tests.sh

# Run tests with different options:
./run_tests.sh                    # Default: pytest mode
./run_tests.sh pytest            # Pytest with verbose output (recommended)
./run_tests.sh coverage          # With coverage analysis
./run_tests.sh html              # Generate HTML test report
./run_tests.sh ci                # CI mode with JUnit XML output
./run_tests.sh quick             # Quick smoke tests only
```

#### Direct Commands

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

### Test Structure

The test suite is organized into logical groups:

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

## Development

This is a simple Flask application perfect for:
- Learning REST API concepts
- Understanding database integration
- Practicing CRUD operations
- Building frontend applications

Feel free to extend it with additional features like user authentication, photo uploads, or more complex relationships!
