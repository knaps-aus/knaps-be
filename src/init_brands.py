"""
Brands and Distributors Data Import Script

This script imports brands and distributors data from brands_data.json into the database.
It handles the creation of both distributors and brands with proper relationships.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db_models import Distributor, Brand
from .database import get_async_session

logger = logging.getLogger(__name__)


async def load_brands_data() -> List[Dict]:
    """
    Load brands data from the JSON file
    """
    try:
        with open('data_management/data/brands_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        logger.debug(f"Loaded {len(data)} brands from brands_data.json")
        return data
    except FileNotFoundError:
        logger.error("brands_data.json file not found in data_management/data/ directory")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing brands_data.json: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading brands data: {e}")
        return []


async def get_or_create_distributor(
    session: AsyncSession, 
    distributor_data: Dict
) -> tuple[Optional[Distributor], bool]:
    """
    Get existing distributor or create new one
    Returns (distributor, was_created)
    """
    # Check if distributor already exists
    stmt = select(Distributor).where(Distributor.code == distributor_data['code'])
    result = await session.execute(stmt)
    existing_distributor = result.scalar_one_or_none()
    
    if existing_distributor:
        logger.debug(f"Found existing distributor: {distributor_data['code']}")
        return existing_distributor, False
    
    # Create new distributor
    try:
        # Parse datetime strings and convert to UTC naive datetime
        modified = datetime.fromisoformat(distributor_data['modified'].replace('Z', '+00:00')).replace(tzinfo=None)
        created = datetime.fromisoformat(distributor_data['created'].replace('Z', '+00:00')).replace(tzinfo=None)
        
        # Handle deleted fields
        deleted = None
        if distributor_data.get('deleted'):
            deleted = datetime.fromisoformat(distributor_data['deleted'].replace('Z', '+00:00')).replace(tzinfo=None)
        
        # Extract default extended credits info
        default_extended_credits = distributor_data.get('default_extended_credits', {})
        
        # Helper function to extract string from dict or return as is
        def extract_string_value(value):
            if value is None:
                return None
            if isinstance(value, dict):
                # For pp_claim_from, extract the 'code' field
                return value.get('code')
            return str(value) if value is not None else None
        
        distributor = Distributor(
            id=distributor_data['id'],
            active=distributor_data['active'],
            modified_by=distributor_data['modified_by'],
            modified=modified,
            created_by=distributor_data['created_by'],
            created=created,
            deleted_by=distributor_data.get('deleted_by'),
            deleted=deleted,
            code=distributor_data['code'],
            name=distributor_data['name'],
            store=distributor_data['store'],
            edi=distributor_data.get('edi', False),
            auto_claim_over_charge=distributor_data.get('auto_claim_over_charge', False),
            is_central=distributor_data.get('is_central', True),
            icon_owner=distributor_data.get('icon_owner'),
            gln=distributor_data.get('GLN'),
            business_number=distributor_data.get('business_number'),
            accounting_date=distributor_data.get('accounting_date'),
            web_portal_url=distributor_data.get('web_portal_url'),
            pp_claim_from=extract_string_value(distributor_data.get('pp_claim_from')),
            fis_minimum_order=distributor_data.get('FIS_minimum_order'),
            default_extended_credits_code=default_extended_credits.get('code'),
            default_extended_credits_name=default_extended_credits.get('name')
        )
        
        session.add(distributor)
        await session.flush()  # Flush to get the ID
        logger.debug(f"Created new distributor: {distributor_data['code']}")
        return distributor, True
        
    except Exception as e:
        logger.error(f"Error creating distributor {distributor_data['code']}: {e}")
        return None, False


async def create_brand(
    session: AsyncSession, 
    brand_data: Dict, 
    distributor: Distributor
) -> Optional[Brand]:
    """
    Create a new brand
    """
    try:
        # Parse datetime strings and convert to UTC naive datetime
        modified = datetime.fromisoformat(brand_data['modified'].replace('Z', '+00:00')).replace(tzinfo=None)
        created = datetime.fromisoformat(brand_data['created'].replace('Z', '+00:00')).replace(tzinfo=None)
        
        # Handle deleted fields
        deleted = None
        if brand_data.get('deleted'):
            deleted = datetime.fromisoformat(brand_data['deleted'].replace('Z', '+00:00')).replace(tzinfo=None)
        
        brand = Brand(
            id=brand_data['id'],
            active=brand_data['active'],
            modified_by=brand_data['modified_by'],
            modified=modified,
            created_by=brand_data['created_by'],
            created=created,
            deleted_by=brand_data.get('deleted_by'),
            deleted=deleted,
            code=brand_data['code'],
            name=brand_data['name'],
            store=brand_data['store'],
            is_hof_pref=brand_data.get('is_hof_pref', True),
            comments=brand_data.get('comments'),
            narta_rept=brand_data.get('narta_rept', True),
            distributor_id=distributor.id
        )
        
        session.add(brand)
        logger.debug(f"Created brand: {brand_data['code']} for distributor: {distributor.code}")
        return brand
        
    except Exception as e:
        logger.error(f"Error creating brand {brand_data['code']}: {e}")
        return None


async def initialize_brands_data() -> bool:
    """
    Initialize brands data from JSON file (distributors should already be initialized)
    """
    logger.info("Starting brands data initialization...")
    
    # Load data from JSON
    brands_data = await load_brands_data()
    if not brands_data:
        logger.error("No brands data loaded, aborting initialization")
        return False
    
    # Track statistics
    distributors_created = 0
    distributors_skipped = 0
    brands_created = 0
    brands_skipped = 0
    errors = 0
    
    async with get_async_session() as session:
        try:
            # Process each brand entry
            for brand_data in brands_data:
                try:
                    # Get or create distributor
                    distributor_result = await get_or_create_distributor(session, brand_data['distributor'])
                    if not distributor_result:
                        logger.error(f"Failed to get/create distributor for brand {brand_data['code']}")
                        errors += 1
                        continue
                    
                    distributor, was_created = distributor_result
                    if was_created:
                        distributors_created += 1
                    else:
                        distributors_skipped += 1
                    
                    # Check if brand already exists
                    stmt = select(Brand).where(Brand.code == brand_data['code'])
                    result = await session.execute(stmt)
                    existing_brand = result.scalar_one_or_none()
                    
                    if existing_brand:
                        logger.debug(f"Brand {brand_data['code']} already exists, skipping")
                        brands_skipped += 1
                        continue
                    
                    # Create brand
                    brand = await create_brand(session, brand_data, distributor)
                    if brand:
                        brands_created += 1
                    else:
                        errors += 1
                        
                except Exception as e:
                    logger.error(f"Error processing brand {brand_data.get('code', 'unknown')}: {e}")
                    errors += 1
            
            # Commit all changes
            await session.commit()
            
            # Log statistics
            logger.info(f"Brands initialization completed:")
            logger.info(f"  Distributors created: {distributors_created}")
            logger.info(f"  Distributors skipped (already existed): {distributors_skipped}")
            logger.info(f"  Brands created: {brands_created}")
            logger.info(f"  Brands skipped (already existed): {brands_skipped}")
            logger.info(f"  Errors: {errors}")
            
            return errors == 0
            
        except Exception as e:
            logger.error(f"Error during brands initialization: {e}")
            await session.rollback()
            return False


async def get_brands_summary() -> Dict:
    """
    Get a summary of brands and distributors in the database
    """
    async with get_async_session() as session:
        try:
            # Count distributors
            stmt = select(Distributor)
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            
            # Count brands
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
            
            # Get brands per distributor
            stmt = select(Distributor).options(selectinload(Distributor.brands))
            result = await session.execute(stmt)
            distributors_with_brands = result.scalars().all()
            
            brands_per_distributor = {}
            for dist in distributors_with_brands:
                brands_per_distributor[dist.code] = len(dist.brands)
            
            return {
                'total_distributors': len(distributors),
                'total_brands': len(brands),
                'brands_per_distributor': brands_per_distributor
            }
            
        except Exception as e:
            logger.error(f"Error getting brands summary: {e}")
            return {}


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize database first (this will include distributors initialization)
        from .database import init_db
        await init_db(drop_existing=False, load_brands_data=False)
        
        # Import brands data
        success = await initialize_brands_data()
        if success:
            print("Brands data imported successfully!")
            
            # Get summary
            summary = await get_brands_summary()
            print(f"Summary: {summary}")
        else:
            print("Failed to import brands data")
    
    asyncio.run(main()) 