"""
Enhanced Distributors Data Import Script

This script imports enhanced distributor data from distributors_data.json into the database.
It handles the creation of purchasers, contacts, addresses, and distributors with all the new fields.
This script should be run before init_brands.py to ensure all distributor data is properly set up.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db_models import Distributor, Purchaser, Contact, Address
from .database import get_async_session

logger = logging.getLogger(__name__)


async def load_distributors_data() -> List[Dict]:
    """
    Load distributors data from the JSON file
    """
    try:
        with open('data_management/data/distributors_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        logger.debug(f"Loaded {len(data)} distributors from distributors_data.json")
        return data
    except FileNotFoundError:
        logger.error("distributors_data.json file not found in data_management/data/ directory")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing distributors_data.json: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading distributors data: {e}")
        return []


def parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """Parse datetime string to UTC naive datetime"""
    if not dt_string:
        return None
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception as e:
        logger.warning(f"Could not parse datetime {dt_string}: {e}")
        return None


def extract_nested_value(data: Dict, key: str, nested_key: str = None) -> Optional[str]:
    """Extract value from nested dictionary or return the value directly"""
    if key not in data:
        return None
    
    value = data[key]
    if isinstance(value, dict) and nested_key:
        return value.get(nested_key)
    elif isinstance(value, dict):
        return value.get('code') or value.get('name')
    else:
        return str(value) if value is not None else None


async def get_or_create_purchaser(
    session: AsyncSession, 
    purchaser_data: Dict
) -> Tuple[Optional[Purchaser], bool]:
    """
    Get existing purchaser or create new one
    Returns (purchaser, was_created)
    """
    if not purchaser_data:
        return None, False
    
    # Check if purchaser already exists
    stmt = select(Purchaser).where(Purchaser.code == purchaser_data['code'])
    result = await session.execute(stmt)
    existing_purchaser = result.scalar_one_or_none()
    
    if existing_purchaser:
        logger.debug(f"Found existing purchaser: {purchaser_data['code']}")
        return existing_purchaser, False
    
    # Create new purchaser
    try:
        purchaser = Purchaser(
            id=purchaser_data['id'],
            active=purchaser_data['active'],
            modified_by=purchaser_data['modified_by'],
            modified=parse_datetime(purchaser_data['modified']),
            created_by=purchaser_data['created_by'],
            created=parse_datetime(purchaser_data['created']),
            deleted_by=purchaser_data.get('deleted_by'),
            deleted=parse_datetime(purchaser_data.get('deleted')),
            code=purchaser_data['code'],
            name=purchaser_data['name'],
            store=purchaser_data['store'],
            icon_owner=purchaser_data.get('icon_owner')
        )
        
        session.add(purchaser)
        await session.flush()  # Flush to get the ID
        logger.debug(f"Created new purchaser: {purchaser_data['code']}")
        return purchaser, True
        
    except Exception as e:
        logger.error(f"Error creating purchaser {purchaser_data['code']}: {e}")
        return None, False


async def create_contact(
    session: AsyncSession, 
    contact_data: Dict, 
    distributor_id: int
) -> Optional[Contact]:
    """
    Create a new contact
    """
    try:
        # Extract contact type information
        contact_type = contact_data.get('type', {})
        
        contact = Contact(
            id=contact_data['id'],
            active=contact_data['active'],
            modified_by=contact_data['modified_by'],
            modified=parse_datetime(contact_data['modified']),
            created_by=contact_data['created_by'],
            created=parse_datetime(contact_data['created']),
            deleted_by=contact_data.get('deleted_by'),
            deleted=parse_datetime(contact_data.get('deleted')),
            code=contact_data['code'],
            name=contact_data['name'],
            store=contact_data['store']['code'] if isinstance(contact_data.get('store'), dict) else contact_data.get('store'),
            title_code=extract_nested_value(contact_data, 'title', 'code'),
            title_name=extract_nested_value(contact_data, 'title', 'name'),
            first_name=contact_data.get('first_name'),
            last_name=contact_data.get('last_name'),
            email=contact_data.get('email'),
            bounced_email=contact_data.get('bounced_email', False),
            no_email=contact_data.get('no_email', False),
            landline=contact_data.get('landline'),
            mobile=contact_data.get('mobile'),
            website=contact_data.get('website'),
            comment=contact_data.get('comment'),
            visible_to_all=contact_data.get('visible_to_all', True),
            visible_to_group=contact_data.get('visible_to_group', True),
            is_default=contact_data.get('is_default', False),
            contact_type_code=contact_type.get('code'),
            contact_type_name=contact_type.get('name'),
            distributor_id=distributor_id
        )
        
        session.add(contact)
        await session.flush()  # Flush to get the ID
        logger.debug(f"Created contact: {contact_data['code']} for distributor: {distributor_id}")
        return contact
        
    except Exception as e:
        logger.error(f"Error creating contact {contact_data.get('code', 'unknown')}: {e}")
        return None


async def create_address(
    session: AsyncSession, 
    address_data: Dict, 
    distributor_id: Optional[int] = None,
    contact_id: Optional[int] = None
) -> Optional[Address]:
    """
    Create a new address
    """
    try:
        # Extract nested information
        address_type = address_data.get('type', {})
        state = address_data.get('state', {})
        postcode = address_data.get('postcode', {})
        suburb = address_data.get('suburb', {})
        
        address = Address(
            id=address_data['id'],
            active=address_data['active'],
            modified_by=address_data['modified_by'],
            modified=parse_datetime(address_data['modified']),
            created_by=address_data['created_by'],
            created=parse_datetime(address_data['created']),
            deleted_by=address_data.get('deleted_by'),
            deleted=parse_datetime(address_data.get('deleted')),
            code=address_data['code'],
            name=address_data.get('name'),
            store=address_data['store'],
            address1=address_data.get('address1'),
            address2=address_data.get('address2'),
            city=address_data.get('city'),
            latitude=address_data.get('latitude'),
            longitude=address_data.get('longitude'),
            is_default=address_data.get('is_default', False),
            gln=address_data.get('GLN'),
            address_type_code=address_type.get('code'),
            address_type_name=address_type.get('name'),
            address_type_fa_icon=address_type.get('fa_icon'),
            state_code=state.get('code'),
            state_name=state.get('name'),
            postcode_code=postcode.get('code'),
            postcode_name=postcode.get('name'),
            suburb_code=suburb.get('code'),
            suburb_name=suburb.get('name'),
            distributor_id=distributor_id,
            contact_id=contact_id
        )
        
        session.add(address)
        await session.flush()  # Flush to get the ID
        logger.debug(f"Created address: {address_data['code']}")
        return address
        
    except Exception as e:
        logger.error(f"Error creating address {address_data.get('code', 'unknown')}: {e}")
        return None


async def create_or_update_distributor(
    session: AsyncSession, 
    distributor_data: Dict,
    purchaser: Optional[Purchaser] = None,
    default_contact: Optional[Contact] = None
) -> Tuple[Optional[Distributor], bool]:
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
        # Extract default extended credits info
        default_extended_credits = distributor_data.get('default_extended_credits', {})
        
        # Prepare extra fields from default_contact.store if available
        default_contact_data = distributor_data.get('default_contact')
        store_info = None
        if default_contact_data and isinstance(default_contact_data.get('store'), dict):
            store_info = default_contact_data['store']
        
        company_number = store_info.get('company_number') if store_info else None
        permit_bup = store_info.get('permit_bup', False) if store_info else False
        intranet_only = store_info.get('intranet_only', False) if store_info else False
        accounting_only = store_info.get('accounting_only', False) if store_info else False
        is_head_office = store_info.get('is_head_office', False) if store_info else False
        core_group = store_info.get('core_group', {}) if store_info else {}
        membership = store_info.get('membership', {}) if store_info else {}
        communication_settings = store_info.get('communication_settings', {}) if store_info else {}
        core_group_code = core_group.get('code') if isinstance(core_group, dict) else None
        core_group_name = core_group.get('name') if isinstance(core_group, dict) else None
        core_group_rank = core_group.get('rank') if isinstance(core_group, dict) else None
        membership_code = membership.get('code') if isinstance(membership, dict) else None
        membership_name = membership.get('name') if isinstance(membership, dict) else None
        internal_email = communication_settings.get('internal_email') if isinstance(communication_settings, dict) else None
        google_place_id = communication_settings.get('google_place_id') if isinstance(communication_settings, dict) else None
        enable_formatted_emails = communication_settings.get('enable_formatted_emails', True) if isinstance(communication_settings, dict) else True
        
        distributor = Distributor(
            id=distributor_data['id'],
            active=distributor_data['active'],
            modified_by=distributor_data['modified_by'],
            modified=parse_datetime(distributor_data['modified']),
            created_by=distributor_data['created_by'],
            created=parse_datetime(distributor_data['created']),
            deleted_by=distributor_data.get('deleted_by'),
            deleted=parse_datetime(distributor_data.get('deleted')),
            code=distributor_data['code'],
            name=distributor_data['name'],
            store=distributor_data['store'],  # Always a string at distributor level
            edi=distributor_data.get('edi', False),
            auto_claim_over_charge=distributor_data.get('auto_claim_over_charge', False),
            is_central=distributor_data.get('is_central', True),
            icon_owner=distributor_data.get('icon_owner'),
            gln=distributor_data.get('GLN'),
            business_number=distributor_data.get('business_number'),
            accounting_date=distributor_data.get('accounting_date'),
            web_portal_url=distributor_data.get('web_portal_url'),
            pp_claim_from=extract_nested_value(distributor_data, 'pp_claim_from'),
            fis_minimum_order=distributor_data.get('FIS_minimum_order'),
            default_extended_credits_code=default_extended_credits.get('code'),
            default_extended_credits_name=default_extended_credits.get('name'),
            purchaser_id=purchaser.id if purchaser else None,
            source=distributor_data.get('source'),
            default_contact_id=default_contact.id if default_contact else None,
            company_number=company_number,
            permit_bup=permit_bup,
            intranet_only=intranet_only,
            accounting_only=accounting_only,
            is_head_office=is_head_office,
            core_group_code=core_group_code,
            core_group_name=core_group_name,
            core_group_rank=core_group_rank,
            membership_code=membership_code,
            membership_name=membership_name,
            internal_email=internal_email,
            google_place_id=google_place_id,
            enable_formatted_emails=enable_formatted_emails
        )
        
        session.add(distributor)
        await session.flush()  # Flush to get the ID
        logger.debug(f"Created new distributor: {distributor_data['code']}")
        return distributor, True
        
    except Exception as e:
        logger.error(f"Error creating distributor {distributor_data['code']}: {e}")
        return None, False


async def process_distributor_data(
    session: AsyncSession, 
    distributor_data: Dict
) -> Tuple[Optional[Distributor], bool]:
    """
    Process a single distributor record with all its related data
    Returns (distributor, was_created)
    """
    try:
        # 1. Handle purchaser
        purchaser, purchaser_created = await get_or_create_purchaser(
            session, distributor_data.get('purchaser', {})
        )
        
        # 2. Create distributor first (without default_contact for now)
        distributor, distributor_created = await create_or_update_distributor(
            session, distributor_data, purchaser=purchaser
        )
        
        if not distributor:
            return None, False
        
        # 3. Handle contacts
        contacts = distributor_data.get('contacts', [])
        default_contact = None
        
        for contact_data in contacts:
            contact = await create_contact(session, contact_data, distributor.id)
            if contact and contact.is_default:
                default_contact = contact
        
        # 4. Handle default contact from distributor data
        if not default_contact and distributor_data.get('default_contact'):
            default_contact = await create_contact(
                session, distributor_data['default_contact'], distributor.id
            )
        
        # 5. Update distributor with default contact
        if default_contact:
            distributor.default_contact_id = default_contact.id
            await session.flush()
        
        # 6. Handle addresses for distributor
        distributor_addresses = distributor_data.get('addresses', [])
        for address_data in distributor_addresses:
            await create_address(session, address_data, distributor_id=distributor.id)
        
        # 7. Handle addresses for contacts
        for contact_data in contacts:
            contact_id = None
            # Find the contact we created
            stmt = select(Contact).where(Contact.code == contact_data['code'])
            result = await session.execute(stmt)
            contact = result.scalar_one_or_none()
            if contact:
                contact_id = contact.id
                
                # Handle addresses for this contact
                contact_addresses = contact_data.get('addresses', [])
                for address_data in contact_addresses:
                    await create_address(session, address_data, contact_id=contact_id)
                
                # Handle default address for this contact
                if contact_data.get('default_address'):
                    default_address = await create_address(
                        session, contact_data['default_address'], contact_id=contact_id
                    )
                    if default_address:
                        contact.default_address_id = default_address.id
                        await session.flush()
        
        return distributor, distributor_created
        
    except Exception as e:
        logger.error(f"Error processing distributor {distributor_data.get('code', 'unknown')}: {e}")
        return None, False


async def initialize_distributors_data() -> bool:
    """
    Initialize enhanced distributors data from JSON file
    """
    logger.info("Starting enhanced distributors data initialization...")
    
    # Load data from JSON
    distributors_data = await load_distributors_data()
    if not distributors_data:
        logger.error("No distributors data loaded, aborting initialization")
        return False
    
    # Track statistics
    purchasers_created = 0
    purchasers_skipped = 0
    distributors_created = 0
    distributors_skipped = 0
    contacts_created = 0
    addresses_created = 0
    errors = 0
    
    async with get_async_session() as session:
        try:
            # Process each distributor entry
            for distributor_data in distributors_data:
                try:
                    # Process distributor with all related data
                    distributor_result = await process_distributor_data(session, distributor_data)
                    if not distributor_result:
                        logger.error(f"Failed to process distributor {distributor_data.get('code', 'unknown')}")
                        errors += 1
                        continue
                    
                    distributor, was_created = distributor_result
                    if was_created:
                        distributors_created += 1
                    else:
                        distributors_skipped += 1
                        
                except Exception as e:
                    logger.error(f"Error processing distributor {distributor_data.get('code', 'unknown')}: {e}")
                    errors += 1
            
            # Commit all changes
            await session.commit()
            
            # Log statistics
            logger.info(f"Enhanced distributors initialization completed:")
            logger.info(f"  Distributors created: {distributors_created}")
            logger.info(f"  Distributors skipped (already existed): {distributors_skipped}")
            logger.info(f"  Errors: {errors}")
            
            return errors == 0
            
        except Exception as e:
            logger.error(f"Error during distributors initialization: {e}")
            await session.rollback()
            return False


async def get_distributors_summary() -> Dict:
    """
    Get a summary of distributors and related data in the database
    """
    async with get_async_session() as session:
        try:
            # Count distributors
            stmt = select(Distributor)
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            
            # Count purchasers
            stmt = select(Purchaser)
            result = await session.execute(stmt)
            purchasers = result.scalars().all()
            
            # Count contacts
            stmt = select(Contact)
            result = await session.execute(stmt)
            contacts = result.scalars().all()
            
            # Count addresses
            stmt = select(Address)
            result = await session.execute(stmt)
            addresses = result.scalars().all()
            
            # Get distributors with relationships
            stmt = select(Distributor).options(
                selectinload(Distributor.purchaser),
                selectinload(Distributor.contacts),
                selectinload(Distributor.addresses)
            )
            result = await session.execute(stmt)
            distributors_with_relations = result.scalars().all()
            
            distributors_summary = {}
            for dist in distributors_with_relations:
                distributors_summary[dist.code] = {
                    'purchaser': dist.purchaser.code if dist.purchaser else None,
                    'contacts_count': len(dist.contacts),
                    'addresses_count': len(dist.addresses),
                    'has_default_contact': dist.default_contact_id is not None
                }
            
            return {
                'total_distributors': len(distributors),
                'total_purchasers': len(purchasers),
                'total_contacts': len(contacts),
                'total_addresses': len(addresses),
                'distributors_summary': distributors_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting distributors summary: {e}")
            return {}


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize database first
        from .database import init_db
        await init_db(drop_existing=False)
        
        # Import distributors data
        success = await initialize_distributors_data()
        if success:
            print("Enhanced distributors data imported successfully!")
            
            # Get summary
            summary = await get_distributors_summary()
            print(f"Summary: {summary}")
        else:
            print("Failed to import enhanced distributors data")
    
    asyncio.run(main()) 