"""
MCP (Model Context Protocol) service for Pet Adoption API

Async service for MCP tool execution, resource management, and prompt handling.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models import Pet
from schemas import PetCreate, PetUpdate, MCPContent, MCPTool, MCPResource, MCPPrompt
from services.pet import PetService
from services.stats import StatsService


class MCPService:
    """
    Async service for MCP protocol operations.
    
    This service handles tool execution, resource management, and prompt 
    generation for the Model Context Protocol integration.
    """

    @staticmethod
    async def execute_tool(
        db: AsyncSession, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool with the given arguments.
        
        Args:
            db: Async database session
            tool_name: Name of the tool to execute
            arguments: Tool arguments dictionary
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool is not found or arguments are invalid
        """
        if tool_name == "get_pets_summary":
            return await MCPService._execute_get_pets_summary(db)
            
        elif tool_name == "search_pets":
            return await MCPService._execute_search_pets(db, arguments)
            
        elif tool_name == "create_pet":
            return await MCPService._execute_create_pet(db, arguments)
            
        elif tool_name == "adopt_pet_by_name":
            return await MCPService._execute_adopt_pet_by_name(db, arguments)
            
        elif tool_name == "update_pet_info":
            return await MCPService._execute_update_pet_info(db, arguments)
            
        elif tool_name == "get_valid_species":
            return await MCPService._execute_get_valid_species(db)
            
        elif tool_name == "get_pet_by_name":
            return await MCPService._execute_get_pet_by_name(db, arguments)
            
        elif tool_name == "get_pet_by_id":
            return await MCPService._execute_get_pet_by_id(db, arguments)
            
        elif tool_name == "get_available_pets":
            return await MCPService._execute_get_available_pets(db)
            
        elif tool_name == "get_adoption_stats":
            return await MCPService._execute_get_adoption_stats(db)
            
        elif tool_name == "list_all_pets":
            return await MCPService._execute_list_all_pets(db)
            
        elif tool_name == "delete_pet":
            return await MCPService._execute_delete_pet(db, arguments)
            
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    @staticmethod
    async def _execute_get_pets_summary(db: AsyncSession) -> Dict[str, Any]:
        """Execute the get_pets_summary tool."""
        summary = await StatsService.get_pets_summary(db)
        return {
            'summary_by_species': summary['species_stats'],
            'overall_totals': summary['overall_totals']
        }

    @staticmethod
    async def _execute_search_pets(
        db: AsyncSession, 
        arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute the search_pets tool."""
        pets = await PetService.search_pets(
            db,
            species=arguments.get('species'),
            breed=arguments.get('breed'),
            available_only=arguments.get('available_only', False),
            min_age=arguments.get('min_age'),
            max_age=arguments.get('max_age')
        )
        
        return [
            {
                'id': pet.id,
                'name': pet.name,
                'species': pet.species,
                'breed': pet.breed,
                'age': pet.age,
                'description': pet.description,
                'is_adopted': pet.is_adopted,
                'created_at': pet.created_at.isoformat() if pet.created_at else None,
                'updated_at': pet.updated_at.isoformat() if pet.updated_at else None
            }
            for pet in pets
        ]

    @staticmethod
    async def _execute_create_pet(
        db: AsyncSession, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the create_pet tool."""
        name = arguments.get('name')
        species = arguments.get('species')
        
        if not name or not species:
            raise ValueError('Name and species are required')
        
        pet_data = PetCreate(
            name=name,
            species=species,
            breed=arguments.get('breed'),
            age=arguments.get('age'),
            description=arguments.get('description')
        )
        
        pet = await PetService.create_pet(db, pet_data)
        
        return {
            'id': pet.id,
            'name': pet.name,
            'species': pet.species,
            'breed': pet.breed,
            'age': pet.age,
            'description': pet.description,
            'is_adopted': pet.is_adopted,
            'created_at': pet.created_at.isoformat() if pet.created_at else None,
            'updated_at': pet.updated_at.isoformat() if pet.updated_at else None
        }

    @staticmethod
    async def _execute_adopt_pet_by_name(
        db: AsyncSession, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the adopt_pet_by_name tool."""
        name = arguments.get('name')
        
        if not name:
            raise ValueError('Name parameter is required')
        
        pet = await PetService.find_pet_by_name(db, name)
        
        if not pet:
            raise ValueError(f'No pet found with name containing "{name}"')
        
        if pet.is_adopted:
            raise ValueError(f'{pet.name} is already adopted')
        
        adopted_pet = await PetService.adopt_pet(db, pet.id)
        
        return {
            'message': f'{adopted_pet.name} has been successfully adopted!',
            'pet': {
                'id': adopted_pet.id,
                'name': adopted_pet.name,
                'species': adopted_pet.species,
                'breed': adopted_pet.breed,
                'age': adopted_pet.age,
                'description': adopted_pet.description,
                'is_adopted': adopted_pet.is_adopted,
                'created_at': adopted_pet.created_at.isoformat() if adopted_pet.created_at else None,
                'updated_at': adopted_pet.updated_at.isoformat() if adopted_pet.updated_at else None
            }
        }

    @staticmethod
    async def _execute_update_pet_info(
        db: AsyncSession, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the update_pet_info tool."""
        pet_id = arguments.get('pet_id')
        
        if not pet_id:
            raise ValueError('pet_id is required')
        
        # Validate the pet exists
        existing_pet = await PetService.get_pet_by_id(db, pet_id)
        if not existing_pet:
            raise ValueError(f'Pet with ID {pet_id} not found')
        
        # Prepare update data (exclude pet_id from arguments)
        update_data = {k: v for k, v in arguments.items() if k != 'pet_id'}
        
        # Additional validation
        if 'name' in update_data and not update_data['name']:
            raise ValueError('Name cannot be empty')
        if 'species' in update_data and not update_data['species']:
            raise ValueError('Species cannot be empty')
        if 'age' in update_data:
            age = update_data['age']
            if age is not None and (not isinstance(age, int) or age < 0):
                raise ValueError('Age must be a non-negative integer')
        
        pet_update = PetUpdate(**update_data)
        updated_pet = await PetService.update_pet(db, pet_id, pet_update)
        
        return {
            'id': updated_pet.id,
            'name': updated_pet.name,
            'species': updated_pet.species,
            'breed': updated_pet.breed,
            'age': updated_pet.age,
            'description': updated_pet.description,
            'is_adopted': updated_pet.is_adopted,
            'created_at': updated_pet.created_at.isoformat() if updated_pet.created_at else None,
            'updated_at': updated_pet.updated_at.isoformat() if updated_pet.updated_at else None
        }

    @staticmethod
    async def _execute_get_valid_species(db: AsyncSession) -> Dict[str, Any]:
        """Execute the get_valid_species tool."""
        # Get unique species from existing pets
        result = await db.execute(
            select(Pet.species)
            .distinct()
            .order_by(Pet.species)
        )
        existing_species = [row[0] for row in result.all()]
        
        # Common pet species
        common_species = ['Dog', 'Cat', 'Bird', 'Rabbit', 'Hamster', 'Guinea Pig', 'Fish', 'Reptile']
        
        # Combine and deduplicate
        all_species = list(set(existing_species + common_species))
        all_species.sort()
        
        return {
            'species': all_species,
            'existing_in_database': existing_species,
            'common_options': common_species
        }

    @staticmethod
    async def _execute_get_pet_by_name(
        db: AsyncSession, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the get_pet_by_name tool."""
        name = arguments.get('name')
        
        if not name:
            raise ValueError('Name parameter is required')
        
        pet = await PetService.find_pet_by_name(db, name)
        
        if not pet:
            raise ValueError(f'No pet found with name containing "{name}"')
        
        return {
            'id': pet.id,
            'name': pet.name,
            'species': pet.species,
            'breed': pet.breed,
            'age': pet.age,
            'description': pet.description,
            'is_adopted': pet.is_adopted,
            'created_at': pet.created_at.isoformat() if pet.created_at else None,
            'updated_at': pet.updated_at.isoformat() if pet.updated_at else None
        }

    @staticmethod
    async def _execute_get_pet_by_id(
        db: AsyncSession, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the get_pet_by_id tool."""
        pet_id = arguments.get('pet_id')
        
        if not pet_id:
            raise ValueError('pet_id parameter is required')
        
        pet = await PetService.get_pet_by_id(db, pet_id)
        
        if not pet:
            raise ValueError(f'Pet with ID {pet_id} not found')
        
        return {
            'id': pet.id,
            'name': pet.name,
            'species': pet.species,
            'breed': pet.breed,
            'age': pet.age,
            'description': pet.description,
            'is_adopted': pet.is_adopted,
            'created_at': pet.created_at.isoformat() if pet.created_at else None,
            'updated_at': pet.updated_at.isoformat() if pet.updated_at else None
        }

    @staticmethod
    async def _execute_get_available_pets(db: AsyncSession) -> List[Dict[str, Any]]:
        """Execute the get_available_pets tool."""
        pets = await PetService.get_available_pets(db)
        
        return [
            {
                'id': pet.id,
                'name': pet.name,
                'species': pet.species,
                'breed': pet.breed,
                'age': pet.age,
                'description': pet.description,
                'is_adopted': pet.is_adopted,
                'created_at': pet.created_at.isoformat() if pet.created_at else None,
                'updated_at': pet.updated_at.isoformat() if pet.updated_at else None
            }
            for pet in pets
        ]

    @staticmethod
    async def _execute_get_adoption_stats(db: AsyncSession) -> Dict[str, Any]:
        """Execute the get_adoption_stats tool."""
        return await StatsService.get_adoption_stats(db)

    @staticmethod
    async def _execute_list_all_pets(db: AsyncSession) -> Dict[str, Any]:
        """Execute the list_all_pets tool."""
        pets = await PetService.get_all_pets(db)
        return {
            'pets': [
                {
                    'id': pet.id,
                    'name': pet.name,
                    'species': pet.species,
                    'breed': pet.breed,
                    'age': pet.age,
                    'description': pet.description,
                    'is_adopted': pet.is_adopted,
                    'created_at': pet.created_at.isoformat() if pet.created_at else None,
                    'updated_at': pet.updated_at.isoformat() if pet.updated_at else None
                }
                for pet in pets
            ],
            'total_count': len(pets)
        }

    @staticmethod
    async def _execute_delete_pet(db: AsyncSession, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the delete_pet tool."""
        pet_id = arguments.get('pet_id')
        pet_name = arguments.get('pet_name')
        
        if not pet_id and not pet_name:
            raise ValueError("Either pet_id or pet_name must be provided")
        
        # If pet_name is provided, find the pet first
        if pet_name and not pet_id:
            pet = await PetService.find_pet_by_name(db, pet_name)
            if not pet:
                raise ValueError(f"Pet with name '{pet_name}' not found")
            pet_id = pet.id
        
        # Delete the pet
        success = await PetService.delete_pet(db, pet_id)
        
        if not success:
            raise ValueError(f"Failed to delete pet with ID {pet_id}")
        
        return {
            'message': f'Pet with ID {pet_id} has been successfully deleted',
            'deleted_pet_id': pet_id
        }

    @staticmethod
    def get_available_tools() -> List[MCPTool]:
        """
        Get list of all available MCP tools with enhanced MCP compliance.
        
        Returns:
            List of MCPTool schemas describing available tools with annotations and output schemas
        """
        return [
            MCPTool(
                name="get_pets_summary",
                title="Get Pets Summary",
                description="Get comprehensive pet statistics by species and adoption status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "summary_by_species": {
                            "type": "object",
                            "description": "Statistics grouped by pet species",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "total": {"type": "integer"},
                                    "adopted": {"type": "integer"},
                                    "available": {"type": "integer"}
                                }
                            }
                        },
                        "overall_totals": {
                            "type": "object",
                            "description": "Overall adoption statistics",
                            "properties": {
                                "total_pets": {"type": "integer"},
                                "adopted_pets": {"type": "integer"},
                                "available_pets": {"type": "integer"},
                                "adoption_rate": {"type": "number"}
                            }
                        }
                    },
                    "required": ["summary_by_species", "overall_totals"],
                    "additionalProperties": False
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.9,
                    "category": "analytics",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="search_pets",
                title="Search Pets",
                description="Search pets with optional filters for species, breed, availability, and age",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "species": {
                            "type": "string",
                            "description": "Filter by species",
                            "examples": ["Dog", "Cat", "Bird"]
                        },
                        "breed": {
                            "type": "string",
                            "description": "Filter by breed"
                        },
                        "available_only": {
                            "type": "boolean",
                            "description": "Only available pets",
                            "default": False
                        },
                        "min_age": {
                            "type": "integer",
                            "description": "Minimum age",
                            "minimum": 0
                        },
                        "max_age": {
                            "type": "integer",
                            "description": "Maximum age",
                            "minimum": 0
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "species": {"type": "string"},
                            "breed": {"type": "string"},
                            "age": {"type": "integer"},
                            "description": {"type": "string"},
                            "is_adopted": {"type": "boolean"},
                            "created_at": {"type": "string", "format": "date-time"},
                            "updated_at": {"type": "string", "format": "date-time"}
                        },
                        "required": ["id", "name", "species", "is_adopted"]
                    }
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.8,
                    "category": "search",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="create_pet",
                title="Create Pet",
                description="Add a new pet to the adoption system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pet name",
                            "minLength": 1,
                            "maxLength": 100
                        },
                        "species": {
                            "type": "string",
                            "description": "Pet species",
                            "enum": ["Dog", "Cat", "Bird", "Rabbit", "Hamster", "Guinea Pig", "Fish", "Reptile"]
                        },
                        "breed": {
                            "type": "string",
                            "description": "Pet breed (optional)",
                            "maxLength": 100
                        },
                        "age": {
                            "type": "integer",
                            "description": "Pet age (optional)",
                            "minimum": 0,
                            "maximum": 30
                        },
                        "description": {
                            "type": "string",
                            "description": "Pet description (optional)",
                            "maxLength": 500
                        }
                    },
                    "required": ["name", "species"],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "species": {"type": "string"},
                        "breed": {"type": "string"},
                        "age": {"type": "integer"},
                        "description": {"type": "string"},
                        "is_adopted": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "name", "species", "is_adopted", "created_at"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.7,
                    "category": "modification",
                    "requiresConfirmation": True,
                    "sensitiveOperation": True
                }
            ),
            MCPTool(
                name="adopt_pet_by_name",
                title="Adopt Pet by Name",
                description="Mark a pet as adopted by searching for its name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pet name to search for",
                            "minLength": 1
                        }
                    },
                    "required": ["name"],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "pet_id": {"type": "integer"},
                        "pet_name": {"type": "string"},
                        "is_adopted": {"type": "boolean"}
                    },
                    "required": ["message", "pet_id", "pet_name", "is_adopted"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.8,
                    "category": "modification",
                    "requiresConfirmation": True,
                    "sensitiveOperation": True
                }
            ),
            MCPTool(
                name="update_pet_info",
                title="Update Pet Information",
                description="Update pet details like name, species, breed, age, or description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pet_id": {
                            "type": "integer",
                            "description": "Pet ID to update",
                            "minimum": 1
                        },
                        "name": {
                            "type": "string",
                            "description": "New pet name",
                            "minLength": 1,
                            "maxLength": 100
                        },
                        "species": {
                            "type": "string",
                            "description": "New pet species",
                            "enum": ["Dog", "Cat", "Bird", "Rabbit", "Hamster", "Guinea Pig", "Fish", "Reptile"]
                        },
                        "breed": {
                            "type": "string",
                            "description": "New pet breed",
                            "maxLength": 100
                        },
                        "age": {
                            "type": "integer",
                            "description": "New pet age",
                            "minimum": 0,
                            "maximum": 30
                        },
                        "description": {
                            "type": "string",
                            "description": "New pet description",
                            "maxLength": 500
                        }
                    },
                    "required": ["pet_id"],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "species": {"type": "string"},
                        "breed": {"type": "string"},
                        "age": {"type": "integer"},
                        "description": {"type": "string"},
                        "is_adopted": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "name", "species", "is_adopted", "updated_at"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.7,
                    "category": "modification",
                    "requiresConfirmation": True,
                    "sensitiveOperation": True
                }
            ),
            MCPTool(
                name="get_valid_species",
                title="Get Valid Pet Species",
                description="Get list of valid pet species including existing and common options",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "species": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "All valid pet species"
                        },
                        "existing_in_database": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Species currently in database"
                        },
                        "common_options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Common pet species options"
                        }
                    },
                    "required": ["species", "existing_in_database", "common_options"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.6,
                    "category": "reference",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="get_pet_by_name",
                title="Get Pet by Name",
                description="Find a pet by searching for its name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pet name to search for",
                            "minLength": 1
                        }
                    },
                    "required": ["name"],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "species": {"type": "string"},
                        "breed": {"type": "string"},
                        "age": {"type": "integer"},
                        "description": {"type": "string"},
                        "is_adopted": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "name", "species", "is_adopted"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.8,
                    "category": "search",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="get_pet_by_id",
                title="Get Pet by ID",
                description="Get a specific pet by its ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pet_id": {
                            "type": "integer",
                            "description": "Pet ID to retrieve",
                            "minimum": 1
                        }
                    },
                    "required": ["pet_id"],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "species": {"type": "string"},
                        "breed": {"type": "string"},
                        "age": {"type": "integer"},
                        "description": {"type": "string"},
                        "is_adopted": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "name", "species", "is_adopted"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.8,
                    "category": "search",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="get_available_pets",
                title="Get Available Pets",
                description="Get all pets that are currently available for adoption",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "species": {"type": "string"},
                            "breed": {"type": "string"},
                            "age": {"type": "integer"},
                            "description": {"type": "string"},
                            "is_adopted": {"type": "boolean"},
                            "created_at": {"type": "string", "format": "date-time"},
                            "updated_at": {"type": "string", "format": "date-time"}
                        },
                        "required": ["id", "name", "species", "is_adopted"]
                    }
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.9,
                    "category": "search",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="get_adoption_stats",
                title="Get Adoption Statistics",
                description="Get overall adoption statistics including rates and counts",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "total_pets": {"type": "integer"},
                        "adopted_pets": {"type": "integer"},
                        "available_pets": {"type": "integer"},
                        "adoption_rate": {"type": "number"},
                        "species_breakdown": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "total": {"type": "integer"},
                                    "adopted": {"type": "integer"},
                                    "available": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "required": ["total_pets", "adopted_pets", "available_pets", "adoption_rate"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.8,
                    "category": "analytics",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="list_all_pets",
                title="List All Pets",
                description="Get a complete list of all pets in the system",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "pets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"},
                                    "species": {"type": "string"},
                                    "breed": {"type": "string"},
                                    "age": {"type": "integer"},
                                    "description": {"type": "string"},
                                    "is_adopted": {"type": "boolean"},
                                    "created_at": {"type": "string", "format": "date-time"},
                                    "updated_at": {"type": "string", "format": "date-time"}
                                },
                                "required": ["id", "name", "species", "is_adopted"]
                            }
                        },
                        "total_count": {"type": "integer"}
                    },
                    "required": ["pets", "total_count"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.7,
                    "category": "search",
                    "requiresConfirmation": False
                }
            ),
            MCPTool(
                name="delete_pet",
                title="Delete Pet",
                description="Remove a pet from the system by ID or name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pet_id": {
                            "type": "integer",
                            "description": "Pet ID to delete",
                            "minimum": 1
                        },
                        "pet_name": {
                            "type": "string",
                            "description": "Pet name to delete (alternative to pet_id)",
                            "minLength": 1
                        }
                    },
                    "required": [],
                    "additionalProperties": False,
                    "anyOf": [
                        {"required": ["pet_id"]},
                        {"required": ["pet_name"]}
                    ]
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "deleted_pet_id": {"type": "integer"}
                    },
                    "required": ["message", "deleted_pet_id"]
                },
                annotations={
                    "audience": ["user", "assistant"],
                    "priority": 0.6,
                    "category": "modification",
                    "requiresConfirmation": True,
                    "sensitiveOperation": True,
                    "destructiveOperation": True
                }
            )
        ]

    @staticmethod
    def get_available_resources() -> List[MCPResource]:
        """
        Get list of all available MCP resources.
        
        Returns:
            List of MCPResource schemas describing available resources
        """
        return [
            MCPResource(
                uri="file://adoption-form.pdf",
                name="Pet Adoption Application Form",
                description="Standard form for pet adoption applications",
                mimeType="application/pdf"
            ),
            MCPResource(
                uri="file://pet-care-guide.md",
                name="Pet Care Guidelines",
                description="Comprehensive guide for pet care and responsibilities",
                mimeType="text/markdown"
            ),
            MCPResource(
                uri="file://adoption-process.md",
                name="Adoption Process Documentation",
                description="Step-by-step guide to the pet adoption process",
                mimeType="text/markdown"
            ),
            MCPResource(
                uri="file://species-info.json",
                name="Pet Species Information",
                description="Detailed information about different pet species and their care requirements",
                mimeType="application/json"
            )
        ]

    @staticmethod
    def get_available_prompts() -> List[MCPPrompt]:
        """
        Get list of all available MCP prompts.
        
        Returns:
            List of MCPPrompt schemas describing available prompts
        """
        return [
            MCPPrompt(
                name="adoption_assistant",
                description="AI assistant for pet adoption counseling and guidance",
                arguments=[
                    {"name": "pet_type", "description": "Type of pet interested in", "required": False},
                    {"name": "experience_level", "description": "Pet owner experience level", "required": False}
                ]
            ),
            MCPPrompt(
                name="pet_care_advisor",
                description="Provide specific care advice for adopted pets",
                arguments=[
                    {"name": "species", "description": "Pet species", "required": True},
                    {"name": "age", "description": "Pet age", "required": False},
                    {"name": "special_needs", "description": "Any special care requirements", "required": False}
                ]
            ),
            MCPPrompt(
                name="species_recommender",
                description="Recommend suitable pet species based on lifestyle and preferences",
                arguments=[
                    {"name": "living_situation", "description": "Housing situation", "required": False},
                    {"name": "time_available", "description": "Time available for pet care", "required": False},
                    {"name": "experience", "description": "Previous pet experience", "required": False}
                ]
            )
        ]

    @staticmethod
    def get_prompt_content(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate prompt content based on name and arguments.
        
        Args:
            name: Prompt template name
            arguments: Prompt arguments
            
        Returns:
            List of message dictionaries for the prompt
            
        Raises:
            ValueError: If prompt name is not found
        """
        if name == "adoption_assistant":
            pet_type = arguments.get('pet_type', 'any pet')
            experience = arguments.get('experience_level', 'beginner')
            
            return [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": f"You are a knowledgeable and compassionate pet adoption counselor. Help the user find the perfect {pet_type} companion based on their {experience} experience level. Provide personalized advice about pet care, responsibilities, and what to expect during the adoption process."
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I'm interested in adopting {pet_type} and I consider myself a {experience} pet owner. Can you help guide me through the adoption process and what I should consider?"
                    }
                }
            ]
            
        elif name == "pet_care_advisor":
            species = arguments.get('species', 'pet')
            age = arguments.get('age')
            special_needs = arguments.get('special_needs')
            
            age_info = f" that is {age} years old" if age else ""
            special_info = f" with special needs: {special_needs}" if special_needs else ""
            
            return [
                {
                    "role": "system", 
                    "content": {
                        "type": "text",
                        "text": f"You are an expert veterinarian and pet care specialist. Provide detailed, practical advice for caring for a {species}{age_info}{special_info}. Include information about feeding, exercise, health care, grooming, and any species-specific needs."
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I just adopted a {species}{age_info}{special_info}. What specific care advice do you have for me to ensure my new pet is healthy and happy?"
                    }
                }
            ]
            
        elif name == "species_recommender":
            living_situation = arguments.get('living_situation', 'not specified')
            time_available = arguments.get('time_available', 'moderate')
            experience = arguments.get('experience', 'some')
            
            return [
                {
                    "role": "system",
                    "content": {
                        "type": "text", 
                        "text": "You are a pet adoption specialist who helps match people with the most suitable pet species based on their lifestyle, living situation, and experience. Consider factors like space requirements, time commitment, maintenance needs, and compatibility."
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"I live in a {living_situation} and have {time_available} time available for pet care. I have {experience} experience with pets. What species would you recommend for me and why?"
                    }
                }
            ]
            
        else:
            raise ValueError(f"Unknown prompt: {name}")

    @staticmethod
    def format_tool_result(result: Any, is_error: bool = False, content_type: str = "text") -> List[MCPContent]:
        """
        Format tool execution result into MCP content format with enhanced compliance.
        
        Args:
            result: Tool execution result
            is_error: Whether the result represents an error
            content_type: Type of content to generate (text, image, audio, resource_link, resource)
            
        Returns:
            List of MCPContent objects with annotations
        """
        from datetime import datetime
        import json
        import base64
        
        # Base annotations for all content
        base_annotations = {
            "audience": ["user", "assistant"],
            "priority": 0.8,
            "lastModified": datetime.utcnow().isoformat() + "Z"
        }
        
        if is_error:
            return [MCPContent(
                type="text",
                text=f"Error: {str(result)}",
                annotations={
                    **base_annotations,
                    "priority": 0.1,
                    "category": "error"
                }
            )]
        
        # Handle different content types
        if content_type == "text":
            return [MCPContent(
                type="text", 
                text=json.dumps(result, indent=2, ensure_ascii=False),
                annotations=base_annotations
            )]
        
        elif content_type == "image":
            # For demonstration, create a simple image placeholder
            if isinstance(result, dict) and "image_data" in result:
                return [MCPContent(
                    type="image",
                    data=result["image_data"],
                    mimeType=result.get("mime_type", "image/png"),
                    annotations=base_annotations
                )]
            else:
                # Fallback to text if no image data
                return [MCPContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                    annotations=base_annotations
                )]
        
        elif content_type == "audio":
            # For demonstration, create a simple audio placeholder
            if isinstance(result, dict) and "audio_data" in result:
                return [MCPContent(
                    type="audio",
                    data=result["audio_data"],
                    mimeType=result.get("mime_type", "audio/mpeg"),
                    annotations=base_annotations
                )]
            else:
                # Fallback to text if no audio data
                return [MCPContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                    annotations=base_annotations
                )]
        
        elif content_type == "resource_link":
            # Create resource link content
            if isinstance(result, dict) and "uri" in result:
                return [MCPContent(
                    type="resource_link",
                    uri=result["uri"],
                    name=result.get("name", "Resource"),
                    description=result.get("description", ""),
                    annotations=base_annotations
                )]
            else:
                # Fallback to text if no URI
                return [MCPContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                    annotations=base_annotations
                )]
        
        elif content_type == "resource":
            # Create resource content
            if isinstance(result, dict) and "uri" in result:
                return [MCPContent(
                    type="resource",
                    uri=result["uri"],
                    name=result.get("name", "Resource"),
                    description=result.get("description", ""),
                    mimeType=result.get("mime_type", "application/octet-stream"),
                    annotations=base_annotations
                )]
            else:
                # Fallback to text if no URI
                return [MCPContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                    annotations=base_annotations
                )]
        
        else:
            # Default to text content
            return [MCPContent(
                type="text", 
                text=json.dumps(result, indent=2, ensure_ascii=False),
                annotations=base_annotations
            )]

    @staticmethod
    def create_tools_list_changed_notification() -> Dict[str, Any]:
        """
        Create a tools list changed notification.
        
        Returns:
            Dictionary representing the notification
        """
        from schemas.mcp import MCPToolsListChangedNotification
        return MCPToolsListChangedNotification().model_dump()

    @staticmethod
    def create_resources_list_changed_notification() -> Dict[str, Any]:
        """
        Create a resources list changed notification.
        
        Returns:
            Dictionary representing the notification
        """
        from schemas.mcp import MCPResourcesListChangedNotification
        return MCPResourcesListChangedNotification().model_dump()

    @staticmethod
    def create_prompts_list_changed_notification() -> Dict[str, Any]:
        """
        Create a prompts list changed notification.
        
        Returns:
            Dictionary representing the notification
        """
        from schemas.mcp import MCPPromptsListChangedNotification
        return MCPPromptsListChangedNotification().model_dump()

    @staticmethod
    def should_send_notification(operation: str) -> bool:
        """
        Determine if a notification should be sent for the given operation.
        
        Args:
            operation: The operation that was performed
            
        Returns:
            True if a notification should be sent
        """
        # Operations that change the tools list
        tools_changing_operations = [
            "create_pet", "update_pet_info", "delete_pet", "adopt_pet_by_name"
        ]
        
        # Operations that change the resources list
        resources_changing_operations = [
            "create_pet", "update_pet_info", "delete_pet"
        ]
        
        # Operations that change the prompts list
        prompts_changing_operations = [
            "create_pet", "update_pet_info", "delete_pet"
        ]
        
        return {
            "tools": operation in tools_changing_operations,
            "resources": operation in resources_changing_operations,
            "prompts": operation in prompts_changing_operations
        }

    @staticmethod
    def format_error_response(error: Exception, error_code: int = -32603) -> Dict[str, Any]:
        """
        Format an error response with enhanced error handling.
        
        Args:
            error: The exception that occurred
            error_code: JSON-RPC error code
            
        Returns:
            Formatted error response
        """
        from datetime import datetime
        
        # Enhanced error information
        error_info = {
            "code": error_code,
            "message": str(error),
            "data": {
                "error_type": type(error).__name__,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "traceback": None  # In production, you might want to include this
            }
        }
        
        # Add specific error codes for common issues
        if "not found" in str(error).lower():
            error_info["code"] = -32602  # Invalid params
        elif "validation" in str(error).lower():
            error_info["code"] = -32602  # Invalid params
        elif "permission" in str(error).lower() or "unauthorized" in str(error).lower():
            error_info["code"] = -32603  # Internal error (could be 401 in HTTP)
        
        return error_info

    @staticmethod
    def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced validation for tool arguments.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments to validate
            
        Returns:
            Validated and sanitized arguments
            
        Raises:
            ValueError: If validation fails
        """
        # Get the tool definition
        tools = MCPService.get_available_tools()
        tool_def = None
        for tool in tools:
            if tool.name == tool_name:
                tool_def = tool
                break
        
        if not tool_def:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Basic validation
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")
        
        # Validate required fields
        if tool_def.inputSchema and "required" in tool_def.inputSchema:
            for required_field in tool_def.inputSchema["required"]:
                if required_field not in arguments:
                    raise ValueError(f"Required field '{required_field}' is missing")
        
        # Validate field types and constraints
        if tool_def.inputSchema and "properties" in tool_def.inputSchema:
            for field_name, field_def in tool_def.inputSchema["properties"].items():
                if field_name in arguments:
                    value = arguments[field_name]
                    
                    # Type validation
                    if field_def.get("type") == "string":
                        if not isinstance(value, str):
                            raise ValueError(f"Field '{field_name}' must be a string")
                        
                        # Length validation
                        if "minLength" in field_def and len(value) < field_def["minLength"]:
                            raise ValueError(f"Field '{field_name}' must be at least {field_def['minLength']} characters")
                        if "maxLength" in field_def and len(value) > field_def["maxLength"]:
                            raise ValueError(f"Field '{field_name}' must be at most {field_def['maxLength']} characters")
                    
                    elif field_def.get("type") == "integer":
                        if not isinstance(value, int):
                            raise ValueError(f"Field '{field_name}' must be an integer")
                        
                        # Range validation
                        if "minimum" in field_def and value < field_def["minimum"]:
                            raise ValueError(f"Field '{field_name}' must be at least {field_def['minimum']}")
                        if "maximum" in field_def and value > field_def["maximum"]:
                            raise ValueError(f"Field '{field_name}' must be at most {field_def['maximum']}")
                    
                    elif field_def.get("type") == "boolean":
                        if not isinstance(value, bool):
                            raise ValueError(f"Field '{field_name}' must be a boolean")
                    
                    # Enum validation
                    if "enum" in field_def and value not in field_def["enum"]:
                        raise ValueError(f"Field '{field_name}' must be one of: {field_def['enum']}")
        
        return arguments
