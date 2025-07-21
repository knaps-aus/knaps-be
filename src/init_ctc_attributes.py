#!/usr/bin/env python3
"""
Initialize CTC attributes data from JSON files.
This script imports CTC attributes data including attribute groups, data types, units of measure, and individual attributes.
"""

import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid

from .database import init_db, get_async_session
from .db_models import (
    Base, CTCAttributeGroup, CTCDataType, CTCUnitOfMeasure, 
    CTCAttribute, CTCCategory
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse datetime string to datetime object"""
    if not value:
        return None
    try:
        # Handle timezone info if present
        if '+' in value or value.endswith('Z'):
            # Remove timezone info for simplicity
            value = value.split('+')[0].split('Z')[0]
        return datetime.fromisoformat(value.replace('T', ' '))
    except ValueError:
        logger.warning(f"Could not parse datetime: {value}, using None")
        return None


async def get_or_create_attribute_group(session: AsyncSession, group_data: Dict[str, Any]) -> CTCAttributeGroup:
    """Get or create an attribute group"""
    # Check if already exists
    stmt = select(CTCAttributeGroup).filter(
        CTCAttributeGroup.store == group_data.get('store', ''),
        CTCAttributeGroup.code == group_data.get('code', ''),
        CTCAttributeGroup.name == group_data.get('name', '')
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.debug(f"Attribute group {group_data.get('name', '')} already exists")
        return existing
    
    # Create new attribute group
    new_group = CTCAttributeGroup(
        uuid=str(uuid.uuid4()),
        active=group_data.get('active', True),
        modified_by=group_data.get('modified_by', 'system'),
        modified=parse_dt(group_data.get('modified')) or datetime.utcnow(),
        created_by=group_data.get('created_by', 'system'),
        created=parse_dt(group_data.get('created')) or datetime.utcnow(),
        deleted_by=group_data.get('deleted_by'),
        deleted=parse_dt(group_data.get('deleted')),
        code=group_data.get('code', ''),
        name=group_data.get('name', ''),
        store=group_data.get('store', '')
    )
    
    session.add(new_group)
    logger.debug(f"Created attribute group: {new_group.name}")
    return new_group


async def get_or_create_data_type(session: AsyncSession, data_type_data: Dict[str, Any]) -> CTCDataType:
    """Get or create a data type"""
    # Check if already exists
    stmt = select(CTCDataType).filter(
        CTCDataType.store == data_type_data.get('store', ''),
        CTCDataType.code == data_type_data.get('code', ''),
        CTCDataType.name == data_type_data.get('name', '')
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.debug(f"Data type {data_type_data.get('name', '')} already exists")
        return existing
    
    # Create new data type
    new_data_type = CTCDataType(
        uuid=str(uuid.uuid4()),
        active=data_type_data.get('active', True),
        modified_by=data_type_data.get('modified_by', 'system'),
        modified=parse_dt(data_type_data.get('modified')) or datetime.utcnow(),
        created_by=data_type_data.get('created_by', 'system'),
        created=parse_dt(data_type_data.get('created')) or datetime.utcnow(),
        deleted_by=data_type_data.get('deleted_by'),
        deleted=parse_dt(data_type_data.get('deleted')),
        code=data_type_data.get('code', ''),
        name=data_type_data.get('name', ''),
        store=data_type_data.get('store', '')
    )
    
    session.add(new_data_type)
    logger.debug(f"Created data type: {new_data_type.name}")
    return new_data_type


async def get_or_create_unit_of_measure(session: AsyncSession, uom_data: Optional[Dict[str, Any]]) -> Optional[CTCUnitOfMeasure]:
    """Get or create a unit of measure"""
    if not uom_data:
        return None
    
    # Check if already exists
    stmt = select(CTCUnitOfMeasure).filter(
        CTCUnitOfMeasure.store == uom_data.get('store', ''),
        CTCUnitOfMeasure.code == uom_data.get('code', ''),
        CTCUnitOfMeasure.name == uom_data.get('name', '')
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.debug(f"Unit of measure {uom_data.get('name', '')} already exists")
        return existing
    
    # Create new unit of measure
    new_uom = CTCUnitOfMeasure(
        uuid=str(uuid.uuid4()),
        active=uom_data.get('active', True),
        modified_by=uom_data.get('modified_by', 'system'),
        modified=parse_dt(uom_data.get('modified')) or datetime.utcnow(),
        created_by=uom_data.get('created_by', 'system'),
        created=parse_dt(uom_data.get('created')) or datetime.utcnow(),
        deleted_by=uom_data.get('deleted_by'),
        deleted=parse_dt(uom_data.get('deleted')),
        code=uom_data.get('code', ''),
        name=uom_data.get('name', ''),
        store=uom_data.get('store', '')
    )
    
    session.add(new_uom)
    logger.debug(f"Created unit of measure: {new_uom.name}")
    return new_uom


async def get_ctc_category(session: AsyncSession, category_id: int) -> Optional[CTCCategory]:
    """Get a CTC category by its ID"""
    stmt = select(CTCCategory).filter(CTCCategory.id == category_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_or_update_ctc_attribute(
    session: AsyncSession, 
    attr_data: Dict[str, Any], 
    category: CTCCategory,
    attribute_group: CTCAttributeGroup,
    data_type: CTCDataType,
    uom: Optional[CTCUnitOfMeasure] = None
) -> CTCAttribute:
    """Create or update a CTC attribute"""
    
    # Check if already exists
    stmt = select(CTCAttribute).filter(CTCAttribute.id == attr_data.get('id'))
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.debug(f"CTC attribute {attr_data.get('id')} already exists, updating...")
        # Update existing record
        existing.name = attr_data.get('name', '')
        existing.store = attr_data.get('store', '')
        existing.rank = attr_data.get('rank', 0)
        existing.as_filter = attr_data.get('as_filter', False)
        existing.scraped_at = parse_dt(attr_data.get('scraped_at'))
        existing.attribute_group_id = attribute_group.id
        existing.data_type_id = data_type.id
        existing.uom_id = uom.id if uom else None
        existing.modified = datetime.utcnow()
        return existing
    
    # Create new record
    new_attr = CTCAttribute(
        id=attr_data.get('id'),  # Use original ID
        uuid=str(uuid.uuid4()),
        active=attr_data.get('active', True),
        modified_by=attr_data.get('modified_by', 'system'),
        modified=parse_dt(attr_data.get('modified')) or datetime.utcnow(),
        created_by=attr_data.get('created_by', 'system'),
        created=parse_dt(attr_data.get('created')) or datetime.utcnow(),
        deleted_by=attr_data.get('deleted_by'),
        deleted=parse_dt(attr_data.get('deleted')),
        name=attr_data.get('name', ''),
        store=attr_data.get('store', ''),
        rank=attr_data.get('rank', 0),
        as_filter=attr_data.get('as_filter', False),
        scraped_at=parse_dt(attr_data.get('scraped_at')),
        category_id=category.id,
        attribute_group_id=attribute_group.id,
        data_type_id=data_type.id,
        uom_id=uom.id if uom else None
    )
    
    session.add(new_attr)
    logger.debug(f"Created CTC attribute: {new_attr.name} (ID: {new_attr.id})")
    return new_attr


async def import_ctc_attributes(file_path: str):
    """Import CTC attributes from JSON file"""
    logger.debug(f"Importing CTC attributes from {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        async with get_async_session() as session:
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for category_data in data:
                try:
                    category_id = category_data.get('category_id')
                    if not category_id:
                        logger.warning(f"No category_id found for category data, skipping")
                        skipped_count += 1
                        continue
                    
                    # Get the CTC category
                    category = await get_ctc_category(session, category_id)
                    if not category:
                        logger.warning(f"CTC category {category_id} not found, skipping attributes")
                        skipped_count += 1
                        continue
                    
                    attributes = category_data.get('attributes', [])
                    logger.debug(f"Processing {len(attributes)} attributes for category {category_id}")
                    
                    for attr_data in attributes:
                        try:
                            # Get or create related entities
                            attribute_group = await get_or_create_attribute_group(session, attr_data.get('attribute_group', {}))
                            data_type = await get_or_create_data_type(session, attr_data.get('data_type', {}))
                            uom = await get_or_create_unit_of_measure(session, attr_data.get('uom'))
                            
                            # Create or update the attribute
                            attr = await create_or_update_ctc_attribute(
                                session, attr_data, category, attribute_group, data_type, uom
                            )
                            
                            if attr.id and hasattr(attr, '_sa_instance_state') and not attr._sa_instance_state.pending:
                                # Existing record (updated)
                                updated_count += 1
                            else:
                                # New record (created)
                                created_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing attribute {attr_data.get('id', 'unknown')}: {str(e)}")
                            skipped_count += 1
                            continue
                    
                except Exception as e:
                    logger.error(f"Error processing category {category_data.get('category_id', 'unknown')}: {str(e)}")
                    skipped_count += 1
                    continue
            
            await session.commit()
            logger.info(f"CTC attributes import completed: {created_count} created, {updated_count} updated, {skipped_count} skipped")
            
    except Exception as e:
        logger.error(f"Error importing CTC attributes: {str(e)}")
        raise


async def initialize_ctc_attributes_data():
    """Initialize CTC attributes data from JSON files"""
    logger.info("Starting CTC attributes data initialization...")
    
    try:
        # Import CTC attributes
        attributes_file = "data_management/data/ctc_attributes.json"
        if os.path.exists(attributes_file):
            await import_ctc_attributes(attributes_file)
        else:
            logger.warning(f"CTC attributes file not found: {attributes_file}")
        
        logger.info("CTC attributes data initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"CTC attributes data initialization failed: {str(e)}")
        return False


async def get_ctc_attributes_summary() -> Dict:
    """Get a summary of CTC attributes data"""
    logger.debug("Getting CTC attributes summary...")
    
    try:
        async with get_async_session() as session:
            # Count attribute groups
            stmt = select(CTCAttributeGroup)
            result = await session.execute(stmt)
            attribute_groups_count = len(result.scalars().all())
            
            # Count data types
            stmt = select(CTCDataType)
            result = await session.execute(stmt)
            data_types_count = len(result.scalars().all())
            
            # Count units of measure
            stmt = select(CTCUnitOfMeasure)
            result = await session.execute(stmt)
            uom_count = len(result.scalars().all())
            
            # Count attributes
            stmt = select(CTCAttribute)
            result = await session.execute(stmt)
            attributes_count = len(result.scalars().all())
            
            # Count active attributes
            stmt = select(CTCAttribute).filter(CTCAttribute.active == True)
            result = await session.execute(stmt)
            active_attributes_count = len(result.scalars().all())
            
            summary = {
                "attribute_groups": attribute_groups_count,
                "data_types": data_types_count,
                "units_of_measure": uom_count,
                "attributes": {
                    "total": attributes_count,
                    "active": active_attributes_count,
                    "inactive": attributes_count - active_attributes_count
                }
            }
            
            logger.info(f"CTC attributes summary: {summary}")
            return summary
            
    except Exception as e:
        logger.error(f"Error getting CTC attributes summary: {str(e)}")
        return {}


async def main():
    """Main function to run the initialization"""
    try:
        # Initialize database first
        logger.debug("Initializing database...")
        await init_db(drop_existing=False)
        
        # Initialize CTC attributes data
        success = await initialize_ctc_attributes_data()
        
        if success:
            # Get and display summary
            summary = await get_ctc_attributes_summary()
            logger.info("CTC attributes initialization completed successfully!")
            logger.info(f"Summary: {summary}")
        else:
            logger.error("CTC attributes initialization failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 