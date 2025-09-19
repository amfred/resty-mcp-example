from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "resty.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    description = db.Column(db.Text)
    is_adopted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'species': self.species,
            'breed': self.breed,
            'age': self.age,
            'description': self.description,
            'is_adopted': self.is_adopted,
            'created_at': self.created_at.isoformat()
        }

# Routes
@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to Resty MCP Example - Pet Adoption API!',
        'endpoints': {
            'GET /pets': 'Get all pets',
            'POST /pets': 'Add a new pet',
            'GET /pets/<id>': 'Get a specific pet',
            'PUT /pets/<id>': 'Update pet information',
            'PUT /pets/<id>/adopt': 'Adopt a pet by ID',
            'PUT /pets/adopt?name=<name>': 'Adopt a pet by name',
            'DELETE /pets/<id>': 'Delete a pet',
            'GET /pets/search': 'Search pets with filters',
            'GET /pets/summary': 'Get pet statistics by species and adoption status',
            'GET /pets/available': 'Get all available pets',
            'POST /pets/batch': 'Create multiple pets at once',
            'GET /pets/species': 'Get list of valid pet species',
            'GET /tools/list': 'Get MCP tool definitions for Pet Operations',
            'GET /tools/list?simplified=true': 'Get simplified MCP tool list (7 core tools for LLMs)'
        }
    })

@app.route('/pets', methods=['GET'])
def get_pets():
    pets = Pet.query.all()
    return jsonify([pet.to_dict() for pet in pets])

@app.route('/pets', methods=['POST'])
def create_pet():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('species'):
        return jsonify({'error': 'Name and species are required'}), 400
    
    pet = Pet(
        name=data['name'],
        species=data['species'],
        breed=data.get('breed'),
        age=data.get('age'),
        description=data.get('description')
    )
    
    db.session.add(pet)
    db.session.commit()
    
    return jsonify(pet.to_dict()), 201

@app.route('/pets/<int:pet_id>', methods=['GET'])
def get_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    return jsonify(pet.to_dict())

@app.route('/pets/<int:pet_id>/adopt', methods=['PUT'])
def adopt_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    
    if pet.is_adopted:
        return jsonify({'error': 'Pet is already adopted'}), 400
    
    pet.is_adopted = True
    db.session.commit()
    
    return jsonify(pet.to_dict())

@app.route('/pets/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    
    return jsonify({'message': 'Pet deleted successfully'})

@app.route('/pets/adopt', methods=['PUT'])
def adopt_pet_by_name():
    name = request.args.get('name')
    
    if not name:
        return jsonify({'error': 'Name parameter is required'}), 400
    
    # Find pet by name (case-insensitive)
    pet = Pet.query.filter(Pet.name.ilike(f'%{name}%')).first()
    
    if not pet:
        return jsonify({'error': f'No pet found with name containing "{name}"'}), 404
    
    if pet.is_adopted:
        return jsonify({'error': f'{pet.name} is already adopted'}), 400
    
    pet.is_adopted = True
    db.session.commit()
    
    return jsonify({
        'message': f'{pet.name} has been successfully adopted!',
        'pet': pet.to_dict()
    })

@app.route('/pets/search', methods=['GET'])
def search_pets():
    species = request.args.get('species')
    breed = request.args.get('breed')
    available_only = request.args.get('available_only', 'false').lower() == 'true'
    
    query = Pet.query
    
    if species:
        query = query.filter(Pet.species.ilike(f'%{species}%'))
    if breed:
        query = query.filter(Pet.breed.ilike(f'%{breed}%'))
    if available_only:
        query = query.filter(Pet.is_adopted == False)
    
    pets = query.all()
    return jsonify([pet.to_dict() for pet in pets])

@app.route('/pets/summary', methods=['GET'])
def get_pets_summary():
    """Get summary statistics of pets by species and adoption status"""
    from sqlalchemy import func
    
    # Get counts by species and adoption status
    summary_data = db.session.query(
        Pet.species,
        Pet.is_adopted,
        func.count(Pet.id).label('count')
    ).group_by(Pet.species, Pet.is_adopted).all()
    
    # Organize data by species
    summary = {}
    total_pets = 0
    total_available = 0
    total_adopted = 0
    
    for species, is_adopted, count in summary_data:
        if species not in summary:
            summary[species] = {'available': 0, 'adopted': 0, 'total': 0}
        
        if is_adopted:
            summary[species]['adopted'] = count
            total_adopted += count
        else:
            summary[species]['available'] = count
            total_available += count
        
        summary[species]['total'] = summary[species]['available'] + summary[species]['adopted']
        total_pets += count
    
    return jsonify({
        'summary_by_species': summary,
        'overall_totals': {
            'total_pets': total_pets,
            'available_pets': total_available,
            'adopted_pets': total_adopted
        }
    })

@app.route('/pets/available', methods=['GET'])
def get_available_pets():
    """Get all pets that are currently available for adoption"""
    pets = Pet.query.filter(Pet.is_adopted == False).all()
    return jsonify([pet.to_dict() for pet in pets])

@app.route('/pets/batch', methods=['POST'])
def create_multiple_pets():
    """Add multiple pets in a single operation"""
    data = request.get_json()
    
    if not data or 'pets' not in data or not isinstance(data['pets'], list):
        return jsonify({'error': 'Request must contain a "pets" array'}), 400
    
    if len(data['pets']) == 0:
        return jsonify({'error': 'Pets array cannot be empty'}), 400
    
    if len(data['pets']) > 50:  # Reasonable limit
        return jsonify({'error': 'Cannot create more than 50 pets at once'}), 400
    
    created_pets = []
    errors = []
    
    for i, pet_data in enumerate(data['pets']):
        if not pet_data.get('name') or not pet_data.get('species'):
            errors.append(f'Pet {i+1}: Name and species are required')
            continue
        
        try:
            pet = Pet(
                name=pet_data['name'],
                species=pet_data['species'],
                breed=pet_data.get('breed'),
                age=pet_data.get('age'),
                description=pet_data.get('description')
            )
            db.session.add(pet)
            created_pets.append(pet)
        except Exception as e:
            errors.append(f'Pet {i+1}: {str(e)}')
    
    if errors and not created_pets:
        return jsonify({'errors': errors}), 400
    
    try:
        db.session.commit()
        return jsonify({
            'message': f'Successfully created {len(created_pets)} pets',
            'created_pets': [pet.to_dict() for pet in created_pets],
            'errors': errors if errors else None
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/pets/species', methods=['GET'])
def get_valid_species():
    """Get list of valid/common pet species"""
    # Get unique species from existing pets
    existing_species = db.session.query(Pet.species).distinct().all()
    existing_species = [s[0] for s in existing_species]
    
    # Common pet species (can be extended)
    common_species = ['Dog', 'Cat', 'Bird', 'Rabbit', 'Hamster', 'Guinea Pig', 'Fish', 'Reptile']
    
    # Combine and deduplicate
    all_species = list(set(existing_species + common_species))
    all_species.sort()
    
    return jsonify({
        'species': all_species,
        'existing_in_database': existing_species,
        'common_options': common_species
    })

@app.route('/pets/<int:pet_id>', methods=['PUT'])
def update_pet_info(pet_id):
    """Update pet information (excluding adoption status)"""
    pet = Pet.query.get_or_404(pet_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update allowed fields
    if 'name' in data:
        if not data['name']:
            return jsonify({'error': 'Name cannot be empty'}), 400
        pet.name = data['name']
    
    if 'species' in data:
        if not data['species']:
            return jsonify({'error': 'Species cannot be empty'}), 400
        pet.species = data['species']
    
    if 'breed' in data:
        pet.breed = data['breed']
    
    if 'age' in data:
        if data['age'] is not None and (not isinstance(data['age'], int) or data['age'] < 0):
            return jsonify({'error': 'Age must be a non-negative integer'}), 400
        pet.age = data['age']
    
    if 'description' in data:
        pet.description = data['description']
    
    # Don't allow updating is_adopted through this endpoint
    if 'is_adopted' in data:
        return jsonify({'error': 'Use adoption endpoints to change adoption status'}), 400
    
    try:
        db.session.commit()
        return jsonify(pet.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/tools/list', methods=['GET'])
def get_tools():
    """Returns MCP-formatted tool definitions for all Pet Operations"""
    
    # Check if simplified tool list is requested
    simplified = request.args.get('simplified', 'false').lower() == 'true'
    
    # Pet object schema for responses
    pet_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "description": "Unique pet identifier"},
            "name": {"type": "string", "description": "Pet's name"},
            "species": {"type": "string", "description": "Pet's species (e.g., Dog, Cat, Bird)"},
            "breed": {"type": "string", "description": "Pet's breed"},
            "age": {"type": "integer", "description": "Pet's age in years"},
            "description": {"type": "string", "description": "Description of the pet"},
            "is_adopted": {"type": "boolean", "description": "Whether the pet has been adopted"},
            "created_at": {"type": "string", "format": "date-time", "description": "When the pet was added to the system"}
        },
        "required": ["id", "name", "species", "is_adopted", "created_at"]
    }
    
    # Define all available tools
    all_tools = [
        {
            "name": "get_all_pets",
            "title": "Get All Pets",
            "description": "Retrieve a list of all pets in the adoption system",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "array",
                "items": pet_schema,
                "description": "Array of all pets in the system"
            }
        },
        {
            "name": "create_pet",
            "title": "Add New Pet",
            "description": "Add a new pet to the adoption system",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Pet's name"},
                    "species": {"type": "string", "description": "Pet's species (e.g., Dog, Cat, Bird)"},
                    "breed": {"type": "string", "description": "Pet's breed (optional)"},
                    "age": {"type": "integer", "description": "Pet's age in years (optional)"},
                    "description": {"type": "string", "description": "Description of the pet (optional)"}
                },
                "required": ["name", "species"],
                "additionalProperties": False
            },
            "outputSchema": pet_schema
        },
        {
            "name": "get_pet_by_id",
            "title": "Get Pet by ID",
            "description": "Retrieve detailed information about a specific pet using its ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pet_id": {"type": "integer", "description": "Unique identifier of the pet", "minimum": 1}
                },
                "required": ["pet_id"],
                "additionalProperties": False
            },
            "outputSchema": pet_schema
        },
        {
            "name": "adopt_pet_by_id",
            "title": "Adopt Pet by ID",
            "description": "Mark a pet as adopted using its unique ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pet_id": {"type": "integer", "description": "Unique identifier of the pet to adopt", "minimum": 1}
                },
                "required": ["pet_id"],
                "additionalProperties": False
            },
            "outputSchema": pet_schema
        },
        {
            "name": "adopt_pet_by_name",
            "title": "Adopt Pet by Name",
            "description": "Mark a pet as adopted using its name (supports partial matching)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the pet to adopt (case-insensitive, supports partial matching)", "minLength": 1}
                },
                "required": ["name"],
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Success message"},
                    "pet": pet_schema
                },
                "required": ["message", "pet"]
            }
        },
        {
            "name": "delete_pet",
            "title": "Delete Pet",
            "description": "Remove a pet from the adoption system",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pet_id": {"type": "integer", "description": "Unique identifier of the pet to delete", "minimum": 1}
                },
                "required": ["pet_id"],
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Confirmation message"}
                },
                "required": ["message"]
            }
        },
        {
            "name": "search_pets",
            "title": "Search Pets",
            "description": "Search and filter pets by various criteria",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "species": {"type": "string", "description": "Filter by species (case-insensitive, supports partial matching)"},
                    "breed": {"type": "string", "description": "Filter by breed (case-insensitive, supports partial matching)"},
                    "available_only": {"type": "boolean", "description": "If true, only return pets that are not yet adopted", "default": False}
                },
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "array",
                "items": pet_schema,
                "description": "Array of pets matching the search criteria"
            }
        },
        {
            "name": "get_pets_summary",
            "title": "Get Pet Statistics Summary",
            "description": "Get summary statistics of pets grouped by species and adoption status",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "summary_by_species": {
                        "type": "object",
                        "description": "Statistics grouped by pet species",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "available": {"type": "integer", "description": "Number of available pets"},
                                "adopted": {"type": "integer", "description": "Number of adopted pets"},
                                "total": {"type": "integer", "description": "Total number of pets"}
                            }
                        }
                    },
                    "overall_totals": {
                        "type": "object",
                        "properties": {
                            "total_pets": {"type": "integer", "description": "Total number of pets in system"},
                            "available_pets": {"type": "integer", "description": "Total available pets"},
                            "adopted_pets": {"type": "integer", "description": "Total adopted pets"}
                        },
                        "required": ["total_pets", "available_pets", "adopted_pets"]
                    }
                },
                "required": ["summary_by_species", "overall_totals"]
            }
        },
        {
            "name": "get_available_pets",
            "title": "Get Available Pets",
            "description": "Get all pets that are currently available for adoption",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "array",
                "items": pet_schema,
                "description": "Array of all available pets"
            }
        },
        {
            "name": "create_multiple_pets",
            "title": "Create Multiple Pets",
            "description": "Add multiple pets to the adoption system in a single operation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pets": {
                        "type": "array",
                        "description": "Array of pet objects to create",
                        "minItems": 1,
                        "maxItems": 50,
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Pet's name"},
                                "species": {"type": "string", "description": "Pet's species (e.g., Dog, Cat, Bird)"},
                                "breed": {"type": "string", "description": "Pet's breed (optional)"},
                                "age": {"type": "integer", "description": "Pet's age in years (optional)"},
                                "description": {"type": "string", "description": "Description of the pet (optional)"}
                            },
                            "required": ["name", "species"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["pets"],
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Success message"},
                    "created_pets": {
                        "type": "array",
                        "items": pet_schema,
                        "description": "Array of successfully created pets"
                    },
                    "errors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of error messages for failed pet creations"
                    }
                },
                "required": ["message", "created_pets"]
            }
        },
        {
            "name": "get_valid_species",
            "title": "Get Valid Pet Species",
            "description": "Get list of valid/common pet species for data validation",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "species": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "All available species (existing + common)"
                    },
                    "existing_in_database": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Species currently in the database"
                    },
                    "common_options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Common pet species options"
                    }
                },
                "required": ["species", "existing_in_database", "common_options"]
            }
        },
        {
            "name": "update_pet_info",
            "title": "Update Pet Information",
            "description": "Update pet details (name, species, breed, age, description) excluding adoption status",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pet_id": {"type": "integer", "description": "Unique identifier of the pet to update", "minimum": 1},
                    "name": {"type": "string", "description": "Updated pet name (optional)"},
                    "species": {"type": "string", "description": "Updated pet species (optional)"},
                    "breed": {"type": "string", "description": "Updated pet breed (optional)"},
                    "age": {"type": "integer", "description": "Updated pet age in years (optional)", "minimum": 0},
                    "description": {"type": "string", "description": "Updated pet description (optional)"}
                },
                "required": ["pet_id"],
                "additionalProperties": False
            },
            "outputSchema": pet_schema
        }
    ]
    
    # Define simplified tool list (core essential tools for LLMs)
    simplified_tool_names = [
        "get_pets_summary",      # Most important - gives overview
        "search_pets",           # Most flexible - handles most queries  
        "create_pet",            # Basic creation
        "adopt_pet_by_name",     # User-friendly adoption
        "update_pet_info",       # Basic editing
        "get_valid_species",     # Validation helper
        "create_multiple_pets"   # Batch efficiency
    ]
    
    # Filter tools based on request
    if simplified:
        tools = [tool for tool in all_tools if tool["name"] in simplified_tool_names]
    else:
        tools = all_tools
    
    return jsonify({
        "tools": tools,
        "count": len(tools),
        "mode": "simplified" if simplified else "complete"
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add some sample data if the database is empty
        if Pet.query.count() == 0:
            sample_pets = [
                Pet(name='Buddy', species='Dog', breed='Golden Retriever', age=3, description='Friendly and energetic'),
                Pet(name='Whiskers', species='Cat', breed='Persian', age=2, description='Calm and cuddly'),
                Pet(name='Tweety', species='Bird', breed='Canary', age=1, description='Sings beautifully'),
                Pet(name='Max', species='Dog', breed='Labrador', age=5, description='Great with kids'),
                Pet(name='Luna', species='Cat', breed='Siamese', age=1, description='Playful and curious')
            ]
            
            for pet in sample_pets:
                db.session.add(pet)
            db.session.commit()
            print("Sample pets added to database!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
