import os
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .db_models import (
    RebateAgreement, DealType, DealSource, PriceLevelType, DealValueType, Brand, Distributor, RebateAgreementProduct,
    CTCClass, CTCType, CTCCategory
)
from .database import get_async_session

logger = logging.getLogger(__name__)

def safe_get_nested(data: Dict[str, Any], *keys) -> Optional[Any]:
    """
    Safely access nested dictionary values, handling None values at any level.
    
    Args:
        data: The dictionary to search in
        *keys: Variable number of keys to traverse
        
    Returns:
        The value if found, None if any intermediate key is None or missing
        
    Example:
        safe_get_nested(deal, "product_type", "id")  # Returns None if product_type is None
    """
    current = data
    for key in keys:
        if current is None or not isinstance(current, dict):
            return None
        current = current.get(key)
    return current

def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        return None

def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
    except Exception:
        return None

def parse_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None

def validate_deal_structure(deal: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate deal data structure before processing.
    
    Returns:
        Tuple of (is_valid, list_of_validation_errors)
    """
    errors = []
    
    # Check if deal is a dictionary
    if not isinstance(deal, dict):
        errors.append(f"Deal must be a dictionary, got {type(deal)}")
        return False, errors
    
    # Check required fields
    required_fields = ['id', 'code']
    for field in required_fields:
        if field not in deal:
            errors.append(f"Missing required field: {field}")
    
    # Check for None values in nested objects that should be dictionaries
    nested_objects = ['product_class', 'product_type', 'product_category', 'brand', 'distributor', 
                     'provider_source', 'bonus_type', 'price_level', 'calculated_on', 'value_type', 'bonus_status']
    for obj_name in nested_objects:
        if obj_name in deal and deal[obj_name] is not None and not isinstance(deal[obj_name], dict):
            errors.append(f"Field {obj_name} should be a dictionary or None, got {type(deal[obj_name])}")
    
    # Validate date fields if present
    date_fields = ['valid_start', 'valid_end', 'claim_start', 'claim_end', 'created', 'modified', 'deleted']
    for field in date_fields:
        if field in deal and deal[field] is not None:
            try:
                parse_dt(deal[field])
            except Exception:
                errors.append(f"Invalid date format in field: {field}")
    
    # Validate numeric fields if present
    numeric_fields = ['value_stor', 'value_stor_incl', 'value_hoff', 'value_hoff_incl']
    for field in numeric_fields:
        if field in deal and deal[field] is not None:
            try:
                parse_decimal(deal[field])
            except Exception:
                errors.append(f"Invalid numeric format in field: {field}")
    
    return len(errors) == 0, errors

async def get_or_create(session: AsyncSession, model, unique_field: str, data: Dict[str, Any], defaults: Dict[str, Any] = None):
    stmt = select(model).where(getattr(model, unique_field) == data[unique_field])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    if defaults:
        data.update(defaults)
    obj = model(**data)
    session.add(obj)
    await session.flush()
    return obj

async def validate_ctc_references(session: AsyncSession, deal: Dict[str, Any]) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Validate CTC references in a deal and return valid IDs or None for invalid references.
    Returns (product_class_id, product_type_id, product_category_id)
    """
    product_class_id = None
    product_type_id = None
    product_category_id = None
    
    # Validate product_class_id - use safe_get_nested to handle None values
    class_id = safe_get_nested(deal, "product_class", "id")
    if class_id:
        result = await session.execute(select(CTCClass).where(CTCClass.id == class_id))
        if result.scalar_one_or_none():
            product_class_id = class_id
            logger.debug(f"Valid CTC class ID: {class_id}")
        else:
            logger.warning(f"Invalid CTC class ID: {class_id}, skipping")
    
    # Validate product_type_id - use safe_get_nested to handle None values
    type_id = safe_get_nested(deal, "product_type", "id")
    if type_id:
        result = await session.execute(select(CTCType).where(CTCType.id == type_id))
        if result.scalar_one_or_none():
            product_type_id = type_id
            logger.debug(f"Valid CTC type ID: {type_id}")
        else:
            logger.warning(f"Invalid CTC type ID: {type_id}, skipping")
    
    # Validate product_category_id - use safe_get_nested to handle None values
    category_id = safe_get_nested(deal, "product_category", "id")
    if category_id:
        result = await session.execute(select(CTCCategory).where(CTCCategory.id == category_id))
        if result.scalar_one_or_none():
            product_category_id = category_id
            logger.debug(f"Valid CTC category ID: {category_id}")
        else:
            logger.warning(f"Invalid CTC category ID: {category_id}, skipping")
    
    return product_class_id, product_type_id, product_category_id

async def get_or_create_dealtype(session: AsyncSession, data: Dict[str, Any]) -> DealType:
    stmt = select(DealType).where(DealType.code == data["code"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = DealType(
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        rank=data.get("rank", 1),
        bonus_class=data.get("bonus_class", "GenericBonus"),
        claimable=data.get("claimable", False),
        deductable=data.get("deductable", True),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        default_provider_id=None
    )
    session.add(obj)
    await session.flush()
    return obj

async def get_or_create_dealsource(session: AsyncSession, data: Dict[str, Any]) -> DealSource:
    stmt = select(DealSource).where(DealSource.id == data["id"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = DealSource(
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        for_hoff_only=data.get("for_hoff_only", False),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
    )
    session.add(obj)
    await session.flush()
    return obj

async def get_or_create_priceleveltype(session: AsyncSession, data: Dict[str, Any]) -> PriceLevelType:
    logger.debug(f"Price level type: {data['id']}") 
    stmt = select(PriceLevelType).where(PriceLevelType.id == data["id"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        logger.debug(f"Price level type already exists: {obj.id}")
        return obj
    logger.debug(f"Creating price level type: {data['id']}")
    obj = PriceLevelType(
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        is_incl=data.get("is_incl", False),
        apply_to_db=data.get("apply_to_db", False),
        price_type_code=data.get("price_type", {}).get("code", "buy"),
        price_type_name=data.get("price_type", {}).get("name", "Buy Price"),
        parent_code=data.get("parent_code"),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
    )
    session.add(obj)
    await session.flush()
    return obj

async def get_or_create_valuetype(session: AsyncSession, data: Dict[str, Any]) -> DealValueType:
    logger.debug(f"Looking for DealValueType with id: {data.get('id')}, code: {data.get('code')}")
    
    # Check by ID first
    stmt = select(DealValueType).where(DealValueType.id == data["id"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        logger.debug(f"Found DealValueType by ID {data['id']}: {obj.code} (ID: {obj.id})")
        return obj
    
    # Check by code as fallback
    stmt = select(DealValueType).where(DealValueType.code == data["code"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        logger.debug(f"Found DealValueType by code {data['code']}: {obj.code} (ID: {obj.id}) - ID mismatch, using existing")
        return obj
    
    logger.debug(f"Creating new DealValueType: {data['code']} (ID: {data.get('id')})")
    obj = DealValueType(
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        symbol=data.get("symbol", ""),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
    )
    session.add(obj)
    await session.flush()
    logger.debug(f"Successfully created DealValueType: {obj.code} (ID: {obj.id})")
    return obj

async def get_or_create_brand(session: AsyncSession, data: Dict[str, Any], distributor: Distributor) -> Brand:
    stmt = select(Brand).where(Brand.id == data["id"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = Brand(
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        is_hof_pref=data.get("is_hof_pref", False),
        comments=data.get("comments"),
        narta_rept=data.get("narta_rept"),
        distributor_id=distributor.id if distributor else None,
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
    )
    session.add(obj)
    await session.flush()
    return obj

async def get_or_create_distributor(session: AsyncSession, data: Dict[str, Any]) -> Distributor:
    stmt = select(Distributor).where(Distributor.id == data["id"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = Distributor(
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        edi=data.get("edi"),
        auto_claim_over_charge=data.get("auto_claim_over_charge", False),
        is_central=data.get("is_central", False),
        gln=data.get("gln"),
        business_number=data.get("business_number"),
        web_portal_url=data.get("web_portal_url"),
        accounting_date=data.get("accounting_date"),
        fis_minimum_order=data.get("fis_minimum_order"),
        default_extended_credits=data.get("default_extended_credits"),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
    )
    session.add(obj)
    await session.flush()
    return obj

async def initialize_deal_sources_and_types() -> bool:
    """Initialize deal sources and types from JSON data."""
    logger.debug("Starting deal sources and types initialization...")
    
    # Load deal sources data
    deal_sources_file = os.path.join("data_management", "data", "deal_sources.json")
    if not os.path.exists(deal_sources_file):
        logger.warning(f"Deal sources file not found: {deal_sources_file}")
        return False
    
    with open(deal_sources_file, 'r') as f:
        deal_sources_data = json.load(f)
    
    logger.debug(f"Loaded {len(deal_sources_data)} deal sources")
    
    # Load deal types data
    deal_types_file = os.path.join("data_management", "data", "deal_types.json")
    if not os.path.exists(deal_types_file):
        logger.warning(f"Deal types file not found: {deal_types_file}")
        return False
    
    with open(deal_types_file, 'r') as f:
        deal_types_data = json.load(f)
    
    logger.debug(f"Loaded {len(deal_types_data)} deal types")
    
    # Load price level types data
    logger.debug("Loading price level types...")
    price_level_types_file = os.path.join("data_management", "data", "price_levels.json")
    if not os.path.exists(price_level_types_file):
        logger.warning(f"Price level types file not found: {price_level_types_file}")
        return False
    
    with open(price_level_types_file, 'r') as f:
        price_level_types_data = json.load(f)
    
    logger.debug(f"Loaded {len(price_level_types_data)} price level types")
    
    # Process data
    async with get_async_session() as session:
        # Process deal sources
        for data in deal_sources_data:
            await get_or_create_dealsource(session, data)
        
        # Process deal types
        for data in deal_types_data:
            await get_or_create_dealtype(session, data)
        
        # Process price level types
        for data in price_level_types_data:
            await get_or_create_priceleveltype(session, data)
        
        await session.commit()
    
    return True

async def initialize_deals_data() -> bool:
    """Initialize deals data from JSON files."""
    logger.debug("Starting deals data initialization...")
    
    # Check if deal data directory exists
    deal_data_dir = os.path.join("data_management", "data", "deal_data")
    if not os.path.exists(deal_data_dir):
        logger.debug(f"Deal data directory not found: {deal_data_dir}, skipping scraped deals import")
        return True
    
    # Find all deal files
    deal_files = [f for f in os.listdir(deal_data_dir) if f.endswith('.json')]
    if not deal_files:
        logger.debug("No deal files found in deal_data directory")
        return True
    
    total_deals = 0
    errors = 0
    
    async with get_async_session() as session:
        for fname in sorted(deal_files):
            file_path = os.path.join(deal_data_dir, fname)
            logger.debug(f"Processing file: {fname}")
            
            with open(file_path, 'r') as f:
                deals = json.load(f)
            
            for deal in deals:
                try:
                    logger.debug(f"Processing deal ID: {deal.get('id')}, code: {deal.get('code')}")
                    
                    # --- Ensure referenced objects exist ---
                    # DealSource
                    provider = deal.get("provider_source")
                    if provider:
                        logger.debug(f"Processing provider: {safe_get_nested(provider, 'code')} (ID: {safe_get_nested(provider, 'id')})")
                        provider_obj = await get_or_create_dealsource(session, provider)
                    else:
                        provider_obj = None
                        
                    # DealType
                    bonus_type = deal.get("bonus_type")
                    if bonus_type:
                        logger.debug(f"Processing bonus_type: {safe_get_nested(bonus_type, 'code')} (ID: {safe_get_nested(bonus_type, 'id')})")
                        dealtype_obj = await get_or_create_dealtype(session, bonus_type)
                    else:
                        dealtype_obj = None
                    
                    # PriceLevelType
                    price_level = deal.get("price_level")
                    if price_level:
                        logger.debug(f"Processing price_level: {safe_get_nested(price_level, 'code')} (ID: {safe_get_nested(price_level, 'id')})")
                        pricelevel_obj = await get_or_create_priceleveltype(session, price_level)
                    else:
                        pricelevel_obj = None
                    
                    # Calculated on price level
                    calculated_on = deal.get("calculated_on")
                    if calculated_on:
                        logger.debug(f"Processing calculated_on: {safe_get_nested(calculated_on, 'code')} (ID: {safe_get_nested(calculated_on, 'id')})")
                        calculated_on_obj = await get_or_create_priceleveltype(session, calculated_on)
                    else:
                        calculated_on_obj = None
                    
                    # DealValueType
                    value_type = deal.get("value_type")
                    if value_type:
                        logger.debug(f"Processing value_type: {safe_get_nested(value_type, 'code')} (ID: {safe_get_nested(value_type, 'id')})")
                        valuetype_obj = await get_or_create_valuetype(session, value_type)
                    else:
                        valuetype_obj = None
                        
                    # Brand/Distributor
                    brand = safe_get_nested(deal, "brand")
                    brand_obj = None
                    distributor_obj = None
                    if brand:
                        distributor = safe_get_nested(brand, "distributor")
                        if distributor:
                            distributor_obj = await get_or_create_distributor(session, distributor)
                            brand_obj = await get_or_create_brand(session, brand, distributor_obj)
                        else:
                            # Brand exists but no distributor - skip brand creation
                            logger.warning(f"Brand {safe_get_nested(brand, 'code', 'unknown')} has no distributor, skipping brand creation")
                    else:
                        brand_obj = None
                        distributor_obj = None
                    
                    # Validate CTC references before creating the agreement
                    product_class_id, product_type_id, product_category_id = await validate_ctc_references(session, deal)
                    
                    # --- Create RebateAgreement ---
                    agreement = RebateAgreement(
                        agreement_type="vendor",  # or infer from data
                        distributor_id=distributor_obj.id if distributor_obj else None,
                        description=deal.get("comments", ""),
                        start_date=parse_date(deal.get("valid_start")),
                        end_date=parse_date(deal.get("valid_end")),
                        calc_frequency="invoice",  # or infer
                        basis="amount",  # or infer
                        rate_type="percentage",  # or infer
                        approval_required=False,
                        status=safe_get_nested(deal, "bonus_status", "name") or "active",
                        deal_type_id=dealtype_obj.id if dealtype_obj else None,
                        deal_source_id=provider_obj.id if provider_obj else None,
                        price_level_type_id=pricelevel_obj.id if pricelevel_obj else None,
                        value_stor=parse_decimal(deal.get("value_stor")),
                        value_stor_incl=parse_decimal(deal.get("value_stor_incl")),
                        value_hoff=parse_decimal(deal.get("value_hoff")),
                        value_hoff_incl=parse_decimal(deal.get("value_hoff_incl")),
                        valid_start=parse_dt(deal.get("valid_start")),
                        valid_end=parse_dt(deal.get("valid_end")),
                        claim_start=parse_dt(deal.get("claim_start")),
                        claim_end=parse_dt(deal.get("claim_end")),
                        bonus_status_code=safe_get_nested(deal, "bonus_status", "code"),
                        bonus_status_name=safe_get_nested(deal, "bonus_status", "name"),
                        deal_code=str(deal.get("code")),
                        store=deal.get("store"),
                        created_at=parse_dt(deal.get("created")),
                        created_by=deal.get("created_by", "import"),
                        modified_at=parse_dt(deal.get("modified")),
                        modified_by=deal.get("modified_by", "import"),
                        deleted_at=parse_dt(deal.get("deleted")),
                        deleted_by=deal.get("deleted_by"),
                        # Validated CTC references - will be None if invalid
                        product_class_id=product_class_id,
                        product_type_id=product_type_id,
                        product_category_id=product_category_id,

                        brand_id=brand_obj.id if brand_obj else None,
                        deal_value_type_id=valuetype_obj.id if valuetype_obj else None,
                        calculated_on_price_level_id=calculated_on_obj.id if calculated_on_obj else None
                    )
                    
                    session.add(agreement)
                    await session.flush()

                    # Optionally, link to product/category via RebateAgreementProduct
                    # (not implemented here, but can be added if product/category info is present)
                    total_deals += 1
                except Exception as e:
                    logger.error(f"Error processing deal in {fname}: {e}")
                    logger.error(f"Deal ID: {deal.get('id', 'unknown')}, Code: {deal.get('code', 'unknown')}")
                    logger.error(f"Provider: {safe_get_nested(deal, 'provider_source')}")
                    logger.error(f"Bonus type: {safe_get_nested(deal, 'bonus_type')}")
                    logger.error(f"Price level: {safe_get_nested(deal, 'price_level')}")
                    logger.error(f"Value type: {safe_get_nested(deal, 'value_type')}")
                    logger.error(f"Brand: {safe_get_nested(deal, 'brand')}")
                    logger.error(f"Product class: {safe_get_nested(deal, 'product_class')}")
                    logger.error(f"Product type: {safe_get_nested(deal, 'product_type')}")
                    logger.error(f"Product category: {safe_get_nested(deal, 'product_category')}")
                    errors += 1
                    await session.rollback()
                    continue  # Continue with next deal instead of stopping
        await session.commit()
    logger.debug(f"Deals initialization completed: {total_deals} deals imported, {errors} errors.")
    if errors > 0:
        logger.warning(f"Deals import completed with {errors} errors. Check logs for details.")
    else:
        logger.debug("All deals imported successfully!")
    return errors == 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_deals_data())

