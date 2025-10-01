"""
Statistics service for Pet Adoption API

Async database operations for generating pet statistics and summaries.
"""

from typing import Dict, Any, List
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models import Pet


class StatsService:
    """
    Async service for pet statistics and reporting operations.
    
    This service handles all statistics-related database queries with 
    proper async/await patterns and efficient aggregation.
    """

    @staticmethod
    async def get_pets_summary(db: AsyncSession) -> Dict[str, Any]:
        """
        Get comprehensive pet statistics by species and adoption status.
        
        Args:
            db: Async database session
            
        Returns:
            Dictionary containing species stats and overall totals
        """
        # Get counts by species and adoption status
        result = await db.execute(
            select(
                Pet.species,
                func.count(Pet.id).label('total'),
                func.sum(case((Pet.is_adopted == True, 1), else_=0)).label('adopted'),
                func.sum(case((Pet.is_adopted == False, 1), else_=0)).label('available')
            )
            .group_by(Pet.species)
            .order_by(Pet.species)
        )
        
        species_data = result.all()
        
        # Build species statistics
        species_stats = {}
        total_pets = 0
        total_adopted = 0
        total_available = 0
        
        for row in species_data:
            species = row.species
            total = int(row.total)
            adopted = int(row.adopted or 0)
            available = int(row.available or 0)
            
            species_stats[species] = {
                'total': total,
                'adopted': adopted,
                'available': available
            }
            
            total_pets += total
            total_adopted += adopted
            total_available += available
        
        # Build overall statistics
        overall_totals = {
            'total_pets': total_pets,
            'adopted_pets': total_adopted,
            'available_pets': total_available
        }
        
        return {
            'species_stats': species_stats,
            'overall_totals': overall_totals
        }

    @staticmethod
    async def get_species_counts(db: AsyncSession) -> Dict[str, int]:
        """
        Get count of pets by species.
        
        Args:
            db: Async database session
            
        Returns:
            Dictionary mapping species to pet counts
        """
        result = await db.execute(
            select(
                Pet.species,
                func.count(Pet.id).label('count')
            )
            .group_by(Pet.species)
            .order_by(Pet.species)
        )
        
        return {row.species: int(row.count) for row in result.all()}

    @staticmethod
    async def get_adoption_stats(db: AsyncSession) -> Dict[str, int]:
        """
        Get overall adoption statistics.
        
        Args:
            db: Async database session
            
        Returns:
            Dictionary with adoption statistics
        """
        # Get overall counts
        result = await db.execute(
            select(
                func.count(Pet.id).label('total'),
                func.sum(case((Pet.is_adopted == True, 1), else_=0)).label('adopted'),
                func.sum(case((Pet.is_adopted == False, 1), else_=0)).label('available')
            )
        )
        
        row = result.one()
        
        total = int(row.total or 0)
        adopted = int(row.adopted or 0)
        available = int(row.available or 0)
        
        # Calculate adoption rate
        adoption_rate = (adopted / total * 100) if total > 0 else 0
        
        return {
            'total_pets': total,
            'adopted_pets': adopted,
            'available_pets': available,
            'adoption_rate': round(adoption_rate, 2)
        }

    @staticmethod
    async def get_age_distribution(db: AsyncSession) -> Dict[str, Any]:
        """
        Get age distribution statistics for pets.
        
        Args:
            db: Async database session
            
        Returns:
            Dictionary with age distribution data
        """
        # Get age statistics
        result = await db.execute(
            select(
                func.min(Pet.age).label('min_age'),
                func.max(Pet.age).label('max_age'),
                func.avg(Pet.age).label('avg_age'),
                func.count(Pet.age).label('pets_with_age')  # Non-null ages only
            )
        )
        
        row = result.one()
        
        # Age group counts
        age_groups_result = await db.execute(
            select(
                func.sum(case((Pet.age == None, 1), else_=0)).label('unknown_age'),
                func.sum(case((and_(Pet.age >= 0, Pet.age <= 1), 1), else_=0)).label('baby'),
                func.sum(case((and_(Pet.age >= 2, Pet.age <= 5), 1), else_=0)).label('young'),
                func.sum(case((and_(Pet.age >= 6, Pet.age <= 10), 1), else_=0)).label('adult'),
                func.sum(case((Pet.age > 10, 1), else_=0)).label('senior')
            )
        )
        
        age_groups = age_groups_result.one()
        
        return {
            'statistics': {
                'min_age': int(row.min_age or 0),
                'max_age': int(row.max_age or 0),
                'average_age': round(float(row.avg_age or 0), 1),
                'pets_with_known_age': int(row.pets_with_age or 0)
            },
            'age_groups': {
                'unknown_age': int(age_groups.unknown_age or 0),
                'baby_0_1': int(age_groups.baby or 0),
                'young_2_5': int(age_groups.young or 0),
                'adult_6_10': int(age_groups.adult or 0),
                'senior_10plus': int(age_groups.senior or 0)
            }
        }

    @staticmethod
    async def get_breed_distribution(
        db: AsyncSession, 
        species: str = None
    ) -> Dict[str, int]:
        """
        Get breed distribution, optionally filtered by species.
        
        Args:
            db: Async database session
            species: Optional species filter
            
        Returns:
            Dictionary mapping breeds to counts
        """
        query = select(
            Pet.breed,
            func.count(Pet.id).label('count')
        ).group_by(Pet.breed)
        
        if species:
            query = query.where(Pet.species.ilike(species))
            
        query = query.order_by(func.count(Pet.id).desc())
        
        result = await db.execute(query)
        
        return {
            (row.breed or 'Unknown'): int(row.count) 
            for row in result.all()
        }

    @staticmethod
    async def get_recent_adoptions(
        db: AsyncSession, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recently adopted pets (ordered by updated_at).
        
        Args:
            db: Async database session  
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with pet adoption information
        """
        result = await db.execute(
            select(Pet)
            .where(Pet.is_adopted == True)
            .order_by(Pet.updated_at.desc())
            .limit(limit)
        )
        
        pets = result.scalars().all()
        
        return [
            {
                'id': pet.id,
                'name': pet.name,
                'species': pet.species,
                'breed': pet.breed,
                'age': pet.age,
                'adopted_at': pet.updated_at.isoformat() if pet.updated_at else None
            }
            for pet in pets
        ]

    @staticmethod
    async def get_monthly_adoption_trends(
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get adoption trends by month (based on updated_at for adopted pets).
        
        Args:
            db: Async database session
            
        Returns:
            Dictionary with monthly adoption data
        """
        # Get adoptions grouped by month
        result = await db.execute(
            select(
                func.date_trunc('month', Pet.updated_at).label('month'),
                func.count(Pet.id).label('adoptions')
            )
            .where(Pet.is_adopted == True)
            .group_by(func.date_trunc('month', Pet.updated_at))
            .order_by(func.date_trunc('month', Pet.updated_at))
        )
        
        monthly_data = []
        for row in result.all():
            monthly_data.append({
                'month': row.month.strftime('%Y-%m') if row.month else 'Unknown',
                'adoptions': int(row.adoptions)
            })
        
        return {
            'monthly_trends': monthly_data,
            'total_months': len(monthly_data)
        }

    @staticmethod 
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """
        Get key statistics for a dashboard overview.
        
        Args:
            db: Async database session
            
        Returns:
            Dictionary with dashboard statistics
        """
        # Get overall stats
        overall_result = await db.execute(
            select(
                func.count(Pet.id).label('total'),
                func.sum(case((Pet.is_adopted == True, 1), else_=0)).label('adopted'),
                func.sum(case((Pet.is_adopted == False, 1), else_=0)).label('available')
            )
        )
        
        overall = overall_result.one()
        total = int(overall.total or 0)
        adopted = int(overall.adopted or 0)
        available = int(overall.available or 0)
        
        # Get species count
        species_result = await db.execute(
            select(func.count(func.distinct(Pet.species)).label('species_count'))
        )
        species_count = int(species_result.scalar() or 0)
        
        # Calculate rates
        adoption_rate = (adopted / total * 100) if total > 0 else 0
        
        return {
            'totals': {
                'total_pets': total,
                'available_pets': available,
                'adopted_pets': adopted,
                'species_count': species_count
            },
            'rates': {
                'adoption_rate': round(adoption_rate, 2),
                'availability_rate': round((available / total * 100) if total > 0 else 0, 2)
            },
            'quick_stats': {
                'most_adopted_ready': available > 0,
                'has_adopted_pets': adopted > 0,
                'database_populated': total > 0
            }
        }
