#!/usr/bin/env python3
"""
Database initialization script for FastAPI Pet Adoption API

This script creates the database tables manually to fix the initialization issue.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Import models and Base
from models import Pet, Base

async def init_database():
    """Initialize the database with all tables."""
    # Database URL
    database_url = "sqlite+aiosqlite:///./resty.db"
    
    print("🗄️  Initializing database...")
    print(f"Database URL: {database_url}")
    
    # Remove existing database file if it exists
    if os.path.exists("resty.db"):
        os.remove("resty.db")
        print("🗑️  Removed existing database file")
    
    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            print("📋 Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
            
        # Verify tables were created
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = result.fetchall()
            print(f"📊 Created tables: {[table[0] for table in tables]}")
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        raise
    finally:
        await engine.dispose()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(init_database())
