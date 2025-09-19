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
