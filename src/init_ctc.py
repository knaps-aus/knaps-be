"""
CTC Categories Initialization Module

This module automatically initializes the CTC categories tables with data from
ctc_categories.json when the application starts, if the tables are empty or don't exist.
"""

import json
import os
import uuid
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_async_session
from .db_models import CTCClass, CTCType, CTCCategory, Base

logger = logging.getLogger(__name__)

class CTCInitializer:
    """Handles automatic initialization of CTC categories data."""
    
    def __init__(self):
        self.json_file_path = "data_management/data/ctc_categories.json"
    
    async def table_exists(self) -> bool:
        """Check if the ctc_categories table exists."""
        try:
            async with get_async_session() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'ctc_categories'
                """))
                return result.scalar() > 0
        except Exception as e:
            logger.warning(f"Error checking if table exists: {e}")
            return False
    
    async def table_is_empty(self) -> bool:
        """Check if the ctc_categories table is empty."""
        try:
            async with get_async_session() as session:
                result = await session.execute(text("SELECT COUNT(*) FROM ctc_categories"))
                return result.scalar() == 0
        except Exception as e:
            logger.warning(f"Error checking if table is empty: {e}")
            return True
    
    async def needs_initialization(self) -> bool:
        """Check if the table needs to be initialized."""
        if not await self.table_exists():
            logger.debug("CTC categories table does not exist - initialization needed")
            return True
        
        # Always allow initialization to run, even if data exists
        # This allows for updating existing records with new data
        logger.debug("CTC categories table exists - proceeding with initialization (will update existing records)")
        return True
    
    def parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from the JSON format."""
        if not dt_string:
            return None
        try:
            # Remove timezone info for simplicity
            dt_string = dt_string.split('+')[0]
            return datetime.fromisoformat(dt_string)
        except Exception as e:
            logger.warning(f"Error parsing datetime '{dt_string}': {e}")
            return datetime.utcnow()
    
    def load_json_data(self) -> Optional[list]:
        """Load data from the JSON file."""
        if not os.path.exists(self.json_file_path):
            logger.error(f"CTC categories JSON file not found: {self.json_file_path}")
            return None
        
        try:
            logger.debug(f"Loading CTC categories from {self.json_file_path}...")
            with open(self.json_file_path, 'r') as f:
                data = json.load(f)
            logger.debug(f"Loaded {len(data)} product classes from JSON")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")
            return None
    
    async def import_data(self, data: list) -> bool:
        """Import the CTC categories data into the database."""
        async with get_async_session() as session:
            try:
                logger.info("Starting CTC categories data import...")
                
                # Track imported records for reporting
                imported_classes = 0
                imported_types = 0
                imported_categories = 0
                
                # Import each product class (level 1)
                for class_data in data:
                    class_uuid = str(uuid.uuid4())
                    class_id = class_data['id']
                    
                    # Check if class record already exists
                    existing_class = await session.execute(
                        text("SELECT id FROM ctc_classes WHERE id = :id"),
                        {"id": class_id}
                    )
                    existing_class = existing_class.scalar()
                    
                    if existing_class:
                        # Update existing record
                        await session.execute(
                            text("""
                                UPDATE ctc_classes 
                                SET uuid = :uuid, active = :active, modified_by = :modified_by,
                                    modified = :modified, created_by = :created_by, created = :created,
                                    deleted_by = :deleted_by, deleted = :deleted, code = :code,
                                    name = :name, store = :store
                                WHERE id = :id
                            """),
                            {
                                "id": class_id,
                                "uuid": class_uuid,
                                "active": class_data['active'],
                                "modified_by": class_data['modified_by'],
                                "modified": self.parse_datetime(class_data['modified']),
                                "created_by": class_data['created_by'],
                                "created": self.parse_datetime(class_data['created']),
                                "deleted_by": class_data['deleted_by'],
                                "deleted": self.parse_datetime(class_data['deleted']),
                                "code": class_data['code'],
                                "name": class_data['name'],
                                "store": class_data['store']
                            }
                        )
                    else:
                        # Insert new record
                        class_record = CTCClass(
                            id=class_id,
                            uuid=class_uuid,
                            active=class_data['active'],
                            modified_by=class_data['modified_by'],
                            modified=self.parse_datetime(class_data['modified']),
                            created_by=class_data['created_by'],
                            created=self.parse_datetime(class_data['created']),
                            deleted_by=class_data['deleted_by'],
                            deleted=self.parse_datetime(class_data['deleted']),
                            code=class_data['code'],
                            name=class_data['name'],
                            store=class_data['store']
                        )
                        session.add(class_record)
                        imported_classes += 1
                    
                    # Import product types (level 2) for this class
                    for type_data in class_data.get('all_product_types', []):
                        type_uuid = str(uuid.uuid4())
                        type_id = type_data['id']
                        
                        # Check if type record already exists
                        existing_type = await session.execute(
                            text("SELECT id FROM ctc_types WHERE id = :id"),
                            {"id": type_id}
                        )
                        existing_type = existing_type.scalar()
                        
                        if existing_type:
                            # Update existing record
                            await session.execute(
                                text("""
                                    UPDATE ctc_types 
                                    SET uuid = :uuid, active = :active, modified_by = :modified_by,
                                        modified = :modified, created_by = :created_by, created = :created,
                                        deleted_by = :deleted_by, deleted = :deleted, code = :code,
                                        name = :name, store = :store, class_id = :class_id
                                    WHERE id = :id
                                """),
                                {
                                    "id": type_id,
                                    "uuid": type_uuid,
                                    "active": type_data['active'],
                                    "modified_by": type_data['modified_by'],
                                    "modified": self.parse_datetime(type_data['modified']),
                                    "created_by": type_data['created_by'],
                                    "created": self.parse_datetime(type_data['created']),
                                    "deleted_by": type_data['deleted_by'],
                                    "deleted": self.parse_datetime(type_data['deleted']),
                                    "code": type_data['code'],
                                    "name": type_data['name'],
                                    "store": type_data['store'],
                                    "class_id": class_id
                                }
                            )
                        else:
                            # Insert new record
                            type_record = CTCType(
                                id=type_id,
                                uuid=type_uuid,
                                active=type_data['active'],
                                modified_by=type_data['modified_by'],
                                modified=self.parse_datetime(type_data['modified']),
                                created_by=type_data['created_by'],
                                created=self.parse_datetime(type_data['created']),
                                deleted_by=type_data['deleted_by'],
                                deleted=self.parse_datetime(type_data['deleted']),
                                code=type_data['code'],
                                name=type_data['name'],
                                store=type_data['store'],
                                class_id=class_id
                            )
                            session.add(type_record)
                            imported_types += 1
                        
                        # Import product categories (level 3) for this type
                        for category_data in type_data.get('all_product_categories', []):
                            category_uuid = str(uuid.uuid4())
                            category_id = category_data['id']
                            
                            # Check if category record already exists
                            existing_category = await session.execute(
                                text("SELECT id FROM ctc_categories WHERE id = :id"),
                                {"id": category_id}
                            )
                            existing_category = existing_category.scalar()
                            
                            if existing_category:
                                # Update existing record
                                await session.execute(
                                    text("""
                                        UPDATE ctc_categories 
                                        SET uuid = :uuid, active = :active, modified_by = :modified_by,
                                            modified = :modified, created_by = :created_by, created = :created,
                                            deleted_by = :deleted_by, deleted = :deleted, code = :code,
                                            name = :name, store = :store, type_id = :type_id, product_id = :product_id
                                        WHERE id = :id
                                    """),
                                    {
                                        "id": category_id,
                                        "uuid": category_uuid,
                                        "active": category_data['active'],
                                        "modified_by": category_data['modified_by'],
                                        "modified": self.parse_datetime(category_data['modified']),
                                        "created_by": category_data['created_by'],
                                        "created": self.parse_datetime(category_data['created']),
                                        "deleted_by": category_data['deleted_by'],
                                        "deleted": self.parse_datetime(category_data['deleted']),
                                        "code": category_data['code'],
                                        "name": category_data['name'],
                                        "store": category_data['store'],
                                        "type_id": type_id,
                                        "product_id": None
                                    }
                                )
                            else:
                                # Insert new record
                                category_record = CTCCategory(
                                    id=category_id,
                                    uuid=category_uuid,
                                    active=category_data['active'],
                                    modified_by=category_data['modified_by'],
                                    modified=self.parse_datetime(category_data['modified']),
                                    created_by=category_data['created_by'],
                                    created=self.parse_datetime(category_data['created']),
                                    deleted_by=category_data['deleted_by'],
                                    deleted=self.parse_datetime(category_data['deleted']),
                                    code=category_data['code'],
                                    name=category_data['name'],
                                    store=category_data['store'],
                                    type_id=type_id,
                                    product_id=None
                                )
                                session.add(category_record)
                                imported_categories += 1
                
                # Commit all changes
                await session.commit()
                
                logger.info(f"CTC categories import completed successfully!")
                logger.info(f"  - Product Classes (Level 1): {imported_classes} imported")
                logger.info(f"  - Product Types (Level 2): {imported_types} imported")
                logger.info(f"  - Product Categories (Level 3): {imported_categories} imported")
                
                return True
                
            except Exception as e:
                logger.error(f"Error importing CTC data: {e}")
                await session.rollback()
                return False
    
    async def verify_import(self) -> bool:
        """Verify that the import was successful."""
        try:
            async with get_async_session() as session:
                # Count records in each table
                class_result = await session.execute(text("SELECT COUNT(*) FROM ctc_classes"))
                type_result = await session.execute(text("SELECT COUNT(*) FROM ctc_types"))
                category_result = await session.execute(text("SELECT COUNT(*) FROM ctc_categories"))
                
                class_count = class_result.scalar()
                type_count = type_result.scalar()
                category_count = category_result.scalar()
                
                total_records = class_count + type_count + category_count
                logger.debug(f"Verification: Found {total_records} total records")
                logger.debug(f"  - Classes: {class_count}")
                logger.debug(f"  - Types: {type_count}")
                logger.debug(f"  - Categories: {category_count}")
                
                return total_records > 0
                
        except Exception as e:
            logger.error(f"Error verifying import: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize CTC categories if needed."""
        try:
            # Check if initialization is needed
            if not await self.needs_initialization():
                return True
            
            # Load JSON data
            data = self.load_json_data()
            if not data:
                logger.error("Failed to load JSON data")
                return False
            
            # Import the data
            success = await self.import_data(data)
            if not success:
                logger.error("Failed to import CTC data")
                return False
            
            # Verify the import
            if not await self.verify_import():
                logger.error("Import verification failed")
                return False
            
            logger.info("CTC categories initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"CTC categories initialization failed: {e}")
            return False


def get_ctc_initializer() -> CTCInitializer:
    """Get a CTC initializer instance."""
    return CTCInitializer()


async def initialize_ctc_categories() -> bool:
    """Initialize CTC categories data."""
    initializer = get_ctc_initializer()
    return await initializer.initialize()


def auto_initialize():
    """Synchronous wrapper for async initialization."""
    import asyncio
    try:
        return asyncio.run(initialize_ctc_categories())
    except Exception as e:
        logger.error(f"Auto-initialization failed: {e}")
        return False

# Auto-initialization when module is imported
def auto_initialize():
    """Automatically initialize CTC categories when this module is imported."""
    try:
        if initialize_ctc_categories():
            logger.info("CTC categories auto-initialization successful")
        else:
            logger.warning("CTC categories auto-initialization failed or not needed")
    except Exception as e:
        logger.error(f"CTC categories auto-initialization error: {e}")

# Uncomment the line below to enable auto-initialization on import
# auto_initialize() 