from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, text
import logging 
import json
import pandas as pd
import asyncio
import os

logger = logging.getLogger('uvicorn.error')

# Remove the circular import - we'll get settings when needed
# DATABASE_URL = settings.database_url

# We'll create the engine when init_db is called
engine = None
AsyncSessionLocal = None
Base = declarative_base()

async def drop_all_tables():
    """Drop all tables from the database."""
    if engine is None:
        logger.warning("Engine not initialized, cannot drop tables")
        return

    logger.info("Dropping all tables")
    async with engine.begin() as conn:
        dialect_name = conn.dialect.name
        if dialect_name == "sqlite":
        # SQLite doesn't support DROP SCHEMA, just drop all tables
            await conn.run_sync(Base.metadata.drop_all)
        else:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
    logger.info("All tables dropped successfully")

async def init_db(drop_existing: bool = True, load_ctc_data: bool = False, load_brands_data: bool = False):
    from .config import settings  # Local import to avoid circular dependency
    global engine, AsyncSessionLocal
    DATABASE_URL = settings.database_url

    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    logger.info("Connecting to database")

    # Import models to ensure they are registered with SQLAlchemy
    from . import db_models

    if drop_existing:
        await drop_all_tables()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Load CTC data if requested
    if load_ctc_data:
        try:
            logger.info("Initializing CTC categories data...")
            from .init_ctc import initialize_ctc_categories
            
            # Run the async initialization directly
            success = await initialize_ctc_categories()
            
            if success:
                logger.info("CTC categories data initialized successfully")
            else:
                logger.warning("CTC categories initialization failed or not needed")
        except Exception as e:
            logger.error(f"Failed to initialize CTC data: {e}")
            # Don't fail the entire startup if CTC loading fails
    
    # Load distributors data FIRST (before brands)
    try:
        logger.info("Initializing enhanced distributors data...")
        from .init_distributors import initialize_distributors_data
        
        # Run the async initialization directly
        success = await initialize_distributors_data()
        
        if success:
            logger.info("Enhanced distributors data initialized successfully")
        else:
            logger.warning("Enhanced distributors initialization failed or not needed")
    except Exception as e:
        logger.error(f"Failed to initialize distributors data: {e}")
        # Don't fail the entire startup if distributors loading fails
    
    # Load brands data AFTER distributors (if requested)
    if load_brands_data:
        try:
            logger.info("Initializing brands data...")
            from .init_brands import initialize_brands_data
            
            # Run the async initialization directly
            success = await initialize_brands_data()
            
            if success:
                logger.info("Brands data initialized successfully")
            else:
                logger.warning("Brands initialization failed or not needed")
        except Exception as e:
            logger.error(f"Failed to initialize brands data: {e}")
            # Don't fail the entire startup if brands loading fails

    # Load products data
    try:
        logger.info("Initializing products data...")
        from .init_products import initialize_products_data
        await initialize_products_data()
        logger.info("Products data initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize products data: {e}")

    # Load deals data
    try:
        logger.info("Initializing deals data...")
        from .init_deals import initialize_deals_data
        success = await initialize_deals_data()
        if success:
            logger.info("Deals data initialized successfully")
        else:
            logger.warning("Deals initialization failed or not needed")
    except Exception as e:
        logger.error(f"Failed to initialize deals data: {e}")

    # Load features and benefits data
    try:
        logger.info("Initializing features and benefits data...")
        from .init_features_benefits import initialize_features_benefits_data
        
        # Run the async initialization directly
        success = await initialize_features_benefits_data()
        
        if success:
            logger.info("Features and benefits data initialized successfully")
        else:
            logger.warning("Features and benefits initialization failed or not needed")
    except Exception as e:
        logger.error(f"Failed to initialize features and benefits data: {e}")
        # Don't fail the entire startup if features and benefits loading fails

    # Load CTC attributes data
    try:
        logger.info("Initializing CTC attributes data...")
        from .init_ctc_attributes import initialize_ctc_attributes_data
        
        # Run the async initialization directly
        success = await initialize_ctc_attributes_data()
        
        if success:
            logger.info("CTC attributes data initialized successfully")
        else:
            logger.warning("CTC attributes initialization failed or not needed")
    except Exception as e:
        logger.error(f"Failed to initialize CTC attributes data: {e}")
        # Don't fail the entire startup if CTC attributes loading fails

def get_async_session():
    """Get the async session factory. Raises an error if not initialized."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return AsyncSessionLocal()

def get_database_url():
    """Get the database URL for synchronous operations."""
    from .config import settings
    return settings.database_url
