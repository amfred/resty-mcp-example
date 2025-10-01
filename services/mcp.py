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
        
        # Common pet species (matches original Flask app)
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
    def get_available_tools() -> List[MCPTool]:
        """
        Get list of all available MCP tools.
        
        Returns:
            List of MCPTool schemas describing available tools
        """
        return [
            MCPTool(
                name="get_pets_summary",
                title="Get Pets Summary",
                description="Get comprehensive pet statistics by species and adoption status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "summary_by_species": {
                            "type": "object",
                            "description": "Statistics grouped by pet species"
                        },
                        "overall_totals": {
                            "type": "object",
                            "description": "Overall adoption statistics"
                        }
                    }
                }
            ),
            MCPTool(
                name="search_pets",
                title="Search Pets",
                description="Search pets with optional filters for species, breed, availability, and age",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "species": {"type": "string", "description": "Filter by species"},
                        "breed": {"type": "string", "description": "Filter by breed"},
                        "available_only": {"type": "boolean", "description": "Only available pets"},
                        "min_age": {"type": "integer", "description": "Minimum age"},
                        "max_age": {"type": "integer", "description": "Maximum age"}
                    },
                    "required": []
                }
            ),
            MCPTool(
                name="create_pet",
                title="Create Pet",
                description="Add a new pet to the adoption system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Pet name"},
                        "species": {"type": "string", "description": "Pet species"},
                        "breed": {"type": "string", "description": "Pet breed (optional)"},
                        "age": {"type": "integer", "description": "Pet age (optional)"},
                        "description": {"type": "string", "description": "Pet description (optional)"}
                    },
                    "required": ["name", "species"]
                }
            ),
            MCPTool(
                name="adopt_pet_by_name",
                title="Adopt Pet by Name",
                description="Mark a pet as adopted by searching for its name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Pet name to search for"}
                    },
                    "required": ["name"]
                }
            ),
            MCPTool(
                name="update_pet_info",
                title="Update Pet Information",
                description="Update pet details like name, species, breed, age, or description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pet_id": {"type": "integer", "description": "Pet ID to update"},
                        "name": {"type": "string", "description": "New pet name"},
                        "species": {"type": "string", "description": "New pet species"},
                        "breed": {"type": "string", "description": "New pet breed"},
                        "age": {"type": "integer", "description": "New pet age"},
                        "description": {"type": "string", "description": "New pet description"}
                    },
                    "required": ["pet_id"]
                }
            ),
            MCPTool(
                name="get_valid_species",
                title="Get Valid Pet Species",
                description="Get list of valid pet species including existing and common options",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            MCPTool(
                name="get_pet_by_name",
                title="Get Pet by Name",
                description="Find a pet by searching for its name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Pet name to search for"}
                    },
                    "required": ["name"]
                }
            ),
            MCPTool(
                name="get_pet_by_id",
                title="Get Pet by ID",
                description="Get a specific pet by its ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pet_id": {"type": "integer", "description": "Pet ID to retrieve"}
                    },
                    "required": ["pet_id"]
                }
            ),
            MCPTool(
                name="get_available_pets",
                title="Get Available Pets",
                description="Get all pets that are currently available for adoption",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            MCPTool(
                name="get_adoption_stats",
                title="Get Adoption Statistics",
                description="Get overall adoption statistics including rates and counts",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
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
    def format_tool_result(result: Any, is_error: bool = False) -> List[MCPContent]:
        """
        Format tool execution result into MCP content format.
        
        Args:
            result: Tool execution result
            is_error: Whether the result represents an error
            
        Returns:
            List of MCPContent objects
        """
        if is_error:
            return [MCPContent(
                type="text",
                text=f"Error: {str(result)}"
            )]
        
        # Format successful result as JSON text
        import json
        return [MCPContent(
            type="text", 
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
