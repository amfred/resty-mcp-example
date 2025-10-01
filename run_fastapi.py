#!/usr/bin/env python3
"""
FastAPI Application Startup Script

Production-ready startup script for the Pet Adoption API with FastAPI.
Includes proper configuration, logging, and error handling.
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fastapi_app.log')
    ]
)

logger = logging.getLogger(__name__)


def get_config():
    """Get configuration from environment variables with defaults."""
    return {
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': int(os.getenv('PORT', '5001')),
        'workers': int(os.getenv('WORKERS', '1')),
        'reload': os.getenv('RELOAD', 'false').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'info').lower(),
        'app_name': os.getenv('APP_NAME', 'Pet Adoption API'),
        'app_version': os.getenv('APP_VERSION', '2.0.0'),
    }


def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        logger.info("✅ All required dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return False


def check_database():
    """Check database connectivity and setup."""
    try:
        from database import engine
        from models import Pet
        logger.info("✅ Database models and engine configured")
        return True
    except Exception as e:
        logger.error(f"❌ Database configuration error: {e}")
        return False


def main():
    """Main startup function."""
    logger.info("🚀 Starting Pet Adoption API with FastAPI")
    logger.info("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database
    if not check_database():
        logger.warning("⚠️  Database check failed, but continuing...")
    
    # Get configuration
    config = get_config()
    
    logger.info(f"📋 Configuration:")
    logger.info(f"   Host: {config['host']}")
    logger.info(f"   Port: {config['port']}")
    logger.info(f"   Workers: {config['workers']}")
    logger.info(f"   Reload: {config['reload']}")
    logger.info(f"   Log Level: {config['log_level']}")
    logger.info(f"   App: {config['app_name']} v{config['app_version']}")
    
    # Start the server
    try:
        logger.info("🌐 Starting FastAPI server...")
        logger.info(f"📖 API Documentation: http://{config['host']}:{config['port']}/docs")
        logger.info(f"📚 ReDoc Documentation: http://{config['host']}:{config['port']}/redoc")
        logger.info(f"🔍 MCP Server Info: http://{config['host']}:{config['port']}/api/v1/mcp/info")
        logger.info("=" * 50)
        
        uvicorn.run(
            "main:app",
            host=config['host'],
            port=config['port'],
            workers=config['workers'] if not config['reload'] else 1,
            reload=config['reload'],
            log_level=config['log_level'],
            access_log=True,
            use_colors=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
