#!/usr/bin/env python3
"""
Initialize features and benefits data from JSON files.
This script imports features and benefits data for CTC classes and types.
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

from .database import init_db, get_async_session
from .db_models import (
    Base, ClassFeaturesBenefits, TypeFeaturesBenefits, 
    CTCClass, CTCType
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


async def get_or_create_ctc_class(session: AsyncSession, class_id: int) -> Optional[CTCClass]:
    """Get a CTC class by its ID"""
    stmt = select(CTCClass).filter(CTCClass.id == class_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_ctc_type(session: AsyncSession, type_id: int) -> Optional[CTCType]:
    """Get a CTC type by its ID"""
    stmt = select(CTCType).filter(CTCType.id == type_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_or_update_class_features_benefits(
    session: AsyncSession, 
    data: Dict[str, Any], 
    ctc_class: CTCClass
) -> ClassFeaturesBenefits:
    """Create or update class features and benefits"""
    
    # Check if already exists
    stmt = select(ClassFeaturesBenefits).filter(
        ClassFeaturesBenefits.external_id == str(data['id'])
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.debug(f"Class feature/benefit {data['id']} already exists, updating...")
        # Update existing record
        existing.feature_name = data.get('name', '')
        existing.feature_description = data.get('description', '')
        existing.benefit_name = data.get('name', '')
        existing.benefit_description = data.get('description', '')
        existing.external_code = data.get('code', '')
        existing.priority = data.get('rank', 0)
        existing.scraped_at = parse_dt(data.get('scraped_at'))
        existing.updated_at = datetime.utcnow()
        return existing
    
    # Create new record
    new_fb = ClassFeaturesBenefits(
        feature_name=data.get('name', ''),
        feature_description=data.get('description', ''),
        benefit_name=data.get('name', ''),
        benefit_description=data.get('description', ''),
        external_id=str(data['id']),
        external_code=data.get('code', ''),
        priority=data.get('rank', 0),
        source_level=data.get('level', 'class'),
        source_level_id=data.get('level_id'),
        scraped_at=parse_dt(data.get('scraped_at')),
        class_id=ctc_class.id,
        is_active=True
    )
    
    session.add(new_fb)
    logger.debug(f"Created class feature/benefit: {new_fb.feature_name} (ID: {new_fb.external_id})")
    return new_fb


async def create_or_update_type_features_benefits(
    session: AsyncSession, 
    data: Dict[str, Any], 
    ctc_type: CTCType
) -> TypeFeaturesBenefits:
    """Create or update type features and benefits"""
    
    # Check if already exists
    stmt = select(TypeFeaturesBenefits).filter(
        TypeFeaturesBenefits.external_id == str(data['id'])
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.debug(f"Type feature/benefit {data['id']} already exists, updating...")
        # Update existing record
        existing.feature_name = data.get('name', '')
        existing.feature_description = data.get('description', '')
        existing.benefit_name = data.get('name', '')
        existing.benefit_description = data.get('description', '')
        existing.external_code = data.get('code', '')
        existing.priority = data.get('rank', 0)
        existing.scraped_at = parse_dt(data.get('scraped_at'))
        existing.updated_at = datetime.utcnow()
        return existing
    
    # Create new record
    new_fb = TypeFeaturesBenefits(
        feature_name=data.get('name', ''),
        feature_description=data.get('description', ''),
        benefit_name=data.get('name', ''),
        benefit_description=data.get('description', ''),
        external_id=str(data['id']),
        external_code=data.get('code', ''),
        priority=data.get('rank', 0),
        source_level=data.get('level', 'type'),
        source_level_id=data.get('level_id'),
        scraped_at=parse_dt(data.get('scraped_at')),
        type_id=ctc_type.id,
        class_id=ctc_type.class_id,
        is_active=True
    )
    
    session.add(new_fb)
    logger.debug(f"Created type feature/benefit: {new_fb.feature_name} (ID: {new_fb.external_id})")
    return new_fb


async def import_class_features_benefits(file_path: str):
    """Import class features and benefits from JSON file"""
    logger.debug(f"Importing class features and benefits from {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        async with get_async_session() as session:
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for item in data:
                try:
                    class_id = item.get('level_id')
                    if not class_id:
                        logger.warning(f"No level_id found for item {item.get('id', 'unknown')}, skipping")
                        skipped_count += 1
                        continue
                    
                    # Get the CTC class
                    ctc_class = await get_or_create_ctc_class(session, class_id)
                    if not ctc_class:
                        logger.warning(f"CTC class {class_id} not found, skipping feature/benefit {item.get('id', 'unknown')}")
                        skipped_count += 1
                        continue
                    
                    # Create or update the feature/benefit
                    fb = await create_or_update_class_features_benefits(session, item, ctc_class)
                    
                    if fb.id:  # Existing record (updated)
                        updated_count += 1
                    else:  # New record (created)
                        created_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing class feature/benefit {item.get('id', 'unknown')}: {str(e)}")
                    skipped_count += 1
                    continue
            
            await session.commit()
            logger.info(f"Class features and benefits import completed: {created_count} created, {updated_count} updated, {skipped_count} skipped")
            
    except Exception as e:
        logger.error(f"Error importing class features and benefits: {str(e)}")
        raise


async def import_type_features_benefits(file_path: str):
    """Import type features and benefits from JSON file"""
    logger.debug(f"Importing type features and benefits from {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        async with get_async_session() as session:
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for item in data:
                try:
                    type_id = item.get('level_id')
                    if not type_id:
                        logger.warning(f"No level_id found for item {item.get('id', 'unknown')}, skipping")
                        skipped_count += 1
                        continue
                    
                    # Get the CTC type
                    ctc_type = await get_or_create_ctc_type(session, type_id)
                    if not ctc_type:
                        logger.warning(f"CTC type {type_id} not found, skipping feature/benefit {item.get('id', 'unknown')}")
                        skipped_count += 1
                        continue
                    
                    # Create or update the feature/benefit
                    fb = await create_or_update_type_features_benefits(session, item, ctc_type)
                    
                    if fb.id:  # Existing record (updated)
                        updated_count += 1
                    else:  # New record (created)
                        created_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing type feature/benefit {item.get('id', 'unknown')}: {str(e)}")
                    skipped_count += 1
                    continue
            
            await session.commit()
            logger.info(f"Type features and benefits import completed: {created_count} created, {updated_count} updated, {skipped_count} skipped")
            
    except Exception as e:
        logger.error(f"Error importing type features and benefits: {str(e)}")
        raise


async def initialize_features_benefits_data():
    """Initialize features and benefits data from JSON files"""
    logger.info("Starting features and benefits data initialization...")
    
    try:
        # Import class features and benefits
        class_file = "data_management/data/features_benefits_class.json"
        if os.path.exists(class_file):
            await import_class_features_benefits(class_file)
        else:
            logger.warning(f"Class features and benefits file not found: {class_file}")
        
        # Import type features and benefits
        type_file = "data_management/data/features_benefits_type.json"
        if os.path.exists(type_file):
            await import_type_features_benefits(type_file)
        else:
            logger.warning(f"Type features and benefits file not found: {type_file}")
        
        logger.info("Features and benefits data initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Features and benefits data initialization failed: {str(e)}")
        return False


async def get_features_benefits_summary() -> Dict:
    """Get a summary of features and benefits data"""
    logger.debug("Getting features and benefits summary...")
    
    try:
        async with get_async_session() as session:
            # Count class features and benefits
            stmt = select(ClassFeaturesBenefits)
            result = await session.execute(stmt)
            class_fb_count = len(result.scalars().all())
            
            # Count type features and benefits
            stmt = select(TypeFeaturesBenefits)
            result = await session.execute(stmt)
            type_fb_count = len(result.scalars().all())
            
            # Count active features and benefits
            stmt = select(ClassFeaturesBenefits).filter(ClassFeaturesBenefits.is_active == True)
            result = await session.execute(stmt)
            active_class_fb_count = len(result.scalars().all())
            
            stmt = select(TypeFeaturesBenefits).filter(TypeFeaturesBenefits.is_active == True)
            result = await session.execute(stmt)
            active_type_fb_count = len(result.scalars().all())
            
            summary = {
                "class_features_benefits": {
                    "total": class_fb_count,
                    "active": active_class_fb_count,
                    "inactive": class_fb_count - active_class_fb_count
                },
                "type_features_benefits": {
                    "total": type_fb_count,
                    "active": active_type_fb_count,
                    "inactive": type_fb_count - active_type_fb_count
                },
                "total_features_benefits": class_fb_count + type_fb_count,
                "total_active": active_class_fb_count + active_type_fb_count
            }
            
            logger.info(f"Features and benefits summary: {summary}")
            return summary
            
    except Exception as e:
        logger.error(f"Error getting features and benefits summary: {str(e)}")
        return {}


async def main():
    """Main function to run the initialization"""
    try:
        # Initialize database first
        logger.debug("Initializing database...")
        await init_db(drop_existing=False)
        
        # Initialize features and benefits data
        success = await initialize_features_benefits_data()
        
        if success:
            # Get and display summary
            summary = await get_features_benefits_summary()
            logger.info("Features and benefits initialization completed successfully!")
            logger.info(f"Summary: {summary}")
        else:
            logger.error("Features and benefits initialization failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 