import asyncio
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, Union, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .database import init_db, get_async_session
from .db_models import Distributor, Brand, ProductModel, PriceLevel, MyPrice, CTCClass, CTCType, CTCCategory

import logging
logger = logging.getLogger(__name__)


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        return None


def parse_decimal(value: Any) -> Optional[Decimal]:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


async def get_or_create_distributor(session: AsyncSession, data: Dict[str, Any]) -> Distributor:
    stmt = select(Distributor).where(Distributor.id == data["id"])
    result = await session.execute(stmt)
    distributor = result.scalar_one_or_none()
    if distributor:
        return distributor
    distributor = Distributor(
        id=data["id"],
        active=data.get("active", True),
        modified_by=data.get("modified_by"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        code=data.get("code"),
        name=data.get("name"),
        store=data.get("store"),
        icon_owner=data.get("icon_owner"),
    )
    session.add(distributor)
    await session.flush()
    return distributor


async def get_or_create_brand(session: AsyncSession, data: Dict[str, Any], distributor: Distributor) -> Brand:
    # First try to find by code (which has unique constraint)
    stmt = select(Brand).where(Brand.code == data.get("code"))
    result = await session.execute(stmt)
    brand = result.scalar_one_or_none()
    if brand:
        logger.debug(f"Found existing brand by code: {data.get('code')}")
        return brand
    
    # If not found by code, try by ID
    stmt = select(Brand).where(Brand.id == data["id"])
    result = await session.execute(stmt)
    brand = result.scalar_one_or_none()
    if brand:
        logger.debug(f"Found existing brand by ID: {data['id']}")
        return brand
    brand = Brand(
        id=data["id"],
        active=data.get("active", True),
        modified_by=data.get("modified_by"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        code=data.get("code"),
        name=data.get("name"),
        store=data.get("store"),
        distributor_id=distributor.id,
    )
    session.add(brand)
    await session.flush()
    return brand


async def get_or_create_ctc_class(session: AsyncSession, data: Dict[str, Any]) -> Optional[CTCClass]:
    """Get or create CTC class from product data"""
    if not data:
        return None
    
    # Try to find by code first
    stmt = select(CTCClass).where(CTCClass.id == data.get("id"))
    result = await session.execute(stmt)
    ctc_class = result.scalar_one_or_none()
    if ctc_class:
        logger.debug(f"Found existing CTC class by code: {data.get('code')}")
        return ctc_class
    
    # If not found by code, try by ID
    if data.get("id"):
        stmt = select(CTCClass).where(CTCClass.id == data["id"])
        result = await session.execute(stmt)
        ctc_class = result.scalar_one_or_none()
        if ctc_class:
            logger.debug(f"Found existing CTC class by ID: {data['id']}")
            return ctc_class
    
    # Create new CTC class
    ctc_class = CTCClass(
        id=data.get("id"),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        code=data.get("code"),
        name=data.get("name"),
        store=data.get("store", "QHOF"),
    )
    session.add(ctc_class)
    await session.flush()
    logger.debug(f"Created new CTC class: {data.get('code')}")
    return ctc_class


async def get_or_create_ctc_type(session: AsyncSession, data: Dict[str, Any], ctc_class: CTCClass) -> Optional[CTCType]:
    """Get or create CTC type from product data"""
    if not data:
        return None
    
    # Try to find by code first
    stmt = select(CTCType).where(CTCType.code == data.get("code"))
    result = await session.execute(stmt)
    ctc_type = result.scalar_one_or_none()
    if ctc_type:
        logger.debug(f"Found existing CTC type by code: {data.get('code')}")
        return ctc_type
    
    # If not found by code, try by ID
    if data.get("id"):
        stmt = select(CTCType).where(CTCType.id == data["id"])
        result = await session.execute(stmt)
        ctc_type = result.scalar_one_or_none()
        if ctc_type:
            logger.debug(f"Found existing CTC type by ID: {data['id']}")
            return ctc_type
    
    # Create new CTC type
    ctc_type = CTCType(
        id=data.get("id"),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        code=data.get("code"),
        name=data.get("name"),
        store=data.get("store", "QHOF"),
        class_id=ctc_class.id,
    )
    session.add(ctc_type)
    await session.flush()
    logger.debug(f"Created new CTC type: {data.get('code')}")
    return ctc_type


async def get_or_create_ctc_category(session: AsyncSession, data: Dict[str, Any], ctc_type: CTCType) -> Optional[CTCCategory]:
    """Get or create CTC category from product data"""
    if not data:
        return None
    
    # Try to find by code first
    stmt = select(CTCCategory).where(CTCCategory.code == data.get("code"))
    result = await session.execute(stmt)
    ctc_category = result.scalar_one_or_none()
    if ctc_category:
        logger.debug(f"Found existing CTC category by code: {data.get('code')}")
        return ctc_category
    
    # If not found by code, try by ID
    if data.get("id"):
        stmt = select(CTCCategory).where(CTCCategory.id == data["id"])
        result = await session.execute(stmt)
        ctc_category = result.scalar_one_or_none()
        if ctc_category:
            logger.debug(f"Found existing CTC category by ID: {data['id']}")
            return ctc_category
    
    # Create new CTC category
    ctc_category = CTCCategory(
        id=data.get("id"),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        code=data.get("code"),
        name=data.get("name"),
        store=data.get("store", "QHOF"),
        type_id=ctc_type.id,
    )
    session.add(ctc_category)
    await session.flush()
    logger.debug(f"Created new CTC category: {data.get('code')}")
    return ctc_category


async def create_or_update_product(session: AsyncSession, data: Dict[str, Any], brand: Brand, distributor: Distributor, 
                                  ctc_class: Optional[CTCClass] = None, ctc_type: Optional[CTCType] = None, 
                                  ctc_category: Optional[CTCCategory] = None) -> ProductModel:
    # First try to find by product_code (which has unique constraint)
    stmt = select(ProductModel).where(ProductModel.product_code == data.get("code"))
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()
    if product:
        logger.debug(f"Found existing product by code: {data.get('code')}")
    else:
        # If not found by code, try by ID
        stmt = select(ProductModel).where(ProductModel.id == data["id"])
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()
        if product:
            logger.debug(f"Found existing product by ID: {data['id']}")

    # Handle core_group from parquet file (core_group_code) or JSON files (core_group object)
    core_group_code = None
    if "core_group_code" in data:
        # From parquet file - direct string value
        core_group_code = data.get("core_group_code")
    elif "core_group" in data:
        # From JSON files - object with code field
        core_group = data.get("core_group")
        if isinstance(core_group, dict):
            core_group_code = core_group.get("code")
        elif core_group:
            core_group_code = str(core_group)

    fields = dict(
        uuid=str(data.get("uuid", "") or data.get("id")),
        distributor_id=distributor.id,
        brand_id=brand.id,
        distributor_name=distributor.name,
        brand_name=brand.name,
        product_code=data.get("code"),
        product_secondary_code=data.get("secondary_code"),
        product_name=data.get("name"),
        description=data.get("description"),
        summary=data.get("summary"),
        shipping_class=None,
        category_name="",
        product_availability="In Stock",
        superceded_by=None,
        replaces=None,
        status="Active",
        online=data.get("online", False),
        ean=data.get("ean"),
        pack_size=data.get("pack_size") or 1,
        core_group=core_group_code,
        tax_exmt=data.get("tax_exmt", False),
        hyperlink=None,
        web_title=None,
        features_and_benefits_codes=None,
        badges_codes=None,
        stock_unmanaged=data.get("stock_unmanaged", False),
        active=data.get("active", True),
        purchaser=data.get("purchaser"),
        icon_owner=data.get("icon_owner"),
        is_gift_card=data.get("is_gift_card", False),
        gift_card_limit=parse_decimal(data.get("gift_card_limit")),
        has_promotions=data.get("has_promotions", False),
        store=data.get("store"),
        web_link=data.get("web_link"),
        edit_link=data.get("edit_link"),
        created_by=data.get("created_by"),
        modified_by=data.get("modified_by"),
        created_at=parse_dt(data.get("created")),
        modified_at=parse_dt(data.get("modified")),
        deleted_by=data.get("deleted_by"),
        deleted_at=parse_dt(data.get("deleted")),
        # CTC relationships
        ctc_class_id=ctc_class.id if ctc_class else data.get("ctc_class_id"),
        ctc_type_id=ctc_type.id if ctc_type else data.get("ctc_type_id"),
        ctc_category_id=ctc_category.id if ctc_category else data.get("ctc_category_id"),
    )

    if product:
        for k, v in fields.items():
            setattr(product, k, v)
    else:
        product = ProductModel(id=data["id"], **fields)
        session.add(product)
        await session.flush()

    return product


async def create_price_levels(session: AsyncSession, product: ProductModel, prices: Dict[str, Any]):
    for key, pdata in prices.items():
        level_code = pdata.get("price_level", {}).get("code", key)
        type_code = pdata.get("price_level", {}).get("price_type", {}).get("code")
        price = PriceLevel(
            product_id=product.id,
            price_level=level_code,
            type=type_code or "",
            value_excl=parse_decimal(pdata.get("value_stor")),
            value_incl=parse_decimal(pdata.get("value_stor_incl")),
            comments=pdata.get("comments"),
            active=pdata.get("active", True),
            external_id=pdata.get("id"),
            store=pdata.get("store"),
            value_stor=parse_decimal(pdata.get("value_stor")),
            value_stor_incl=parse_decimal(pdata.get("value_stor_incl")),
            value_hoff=parse_decimal(pdata.get("value_hoff")),
            value_hoff_incl=parse_decimal(pdata.get("value_hoff_incl")),
            valid_start=parse_dt(pdata.get("valid_start")),
            valid_end=parse_dt(pdata.get("valid_end")),
            claim_start=parse_dt(pdata.get("claim_start")),
            claim_end=parse_dt(pdata.get("claim_end")),
            bonus_status=pdata.get("bonus_status", {}).get("code"),
            initial_value_stor=parse_decimal(pdata.get("initial_value_stor")),
            initial_value_stor_incl=parse_decimal(pdata.get("initial_value_stor_incl")),
            initial_value_hoff=parse_decimal(pdata.get("initial_value_hoff")),
            initial_value_hoff_incl=parse_decimal(pdata.get("initial_value_hoff_incl")),
            has_overrides=pdata.get("has_overrides", False),
            current_override_price=parse_decimal(pdata.get("current_override_price")),
            created_by=pdata.get("created_by"),
            modified_by=pdata.get("modified_by"),
            created_at=parse_dt(pdata.get("created")),
            updated_at=parse_dt(pdata.get("modified")),
            deleted_by=pdata.get("deleted_by"),
            deleted_at=parse_dt(pdata.get("deleted")),
        )
        session.add(price)


async def create_my_price(session: AsyncSession, product: ProductModel, data: Dict[str, Any]):
    if not data:
        return
    my_price = MyPrice(
        product_id=product.id,
        active=data.get("active", True),
        go=parse_decimal(data.get("go")),
        go_special=parse_decimal(data.get("go_special")),
        rrp=parse_decimal(data.get("rrp")),
        rrp_special=parse_decimal(data.get("rrp_special")),
        trade=parse_decimal(data.get("trade")),
        off_invoice=parse_decimal(data.get("off_invoice")),
        invoice=parse_decimal(data.get("invoice")),
        vendor_percent=parse_decimal(data.get("vendor_percent")),
        vendor_dollar=parse_decimal(data.get("vendor_dollar")),
        bonus_percent=parse_decimal(data.get("bonus_percent")),
        bonus_dollar=parse_decimal(data.get("bonus_dollar")),
        brand_percent=parse_decimal(data.get("brand_percent")),
        hoff_percent=parse_decimal(data.get("hoff_percent")),
        hoff_dollar=parse_decimal(data.get("hoff_dollar")),
        net=parse_decimal(data.get("net")),
        sellthru_dollar=parse_decimal(data.get("sellthru_dollar")),
        nac=parse_decimal(data.get("nac")),
        off_invoice_hoff=parse_decimal(data.get("off_invoice_hoff")),
        invoice_hoff=parse_decimal(data.get("invoice_hoff")),
        vendor_percent_hoff=parse_decimal(data.get("vendor_percent_hoff")),
        vendor_dollar_hoff=parse_decimal(data.get("vendor_dollar_hoff")),
        bonus_percent_hoff=parse_decimal(data.get("bonus_percent_hoff")),
        bonus_dollar_hoff=parse_decimal(data.get("bonus_dollar_hoff")),
        brand_percent_hoff=parse_decimal(data.get("brand_percent_hoff")),
        net_hoff=parse_decimal(data.get("net_hoff")),
        sellthru_dollar_hoff=parse_decimal(data.get("sellthru_dollar_hoff")),
        nac_hoff=parse_decimal(data.get("nac_hoff")),
        created_at=parse_dt(data.get("created")),
        modified_at=parse_dt(data.get("modified")),
    )
    session.add(my_price)


async def import_products_from_parquet():
    """Import products from the combined parquet file."""
    try:
        # Import the parquet utilities
        import sys
        import os
        # Add the data_management directory to the Python path
        data_management_path = Path(__file__).parent.parent / "data_management"
        sys.path.insert(0, str(data_management_path))
        from parquet_utils import read_parquet_products
        
        logger.info("Starting product import from parquet file...")
        
        # Read products from parquet file
        products = read_parquet_products()
        logger.debug(f"Loaded {len(products)} products from parquet file")
        
        if not products:
            logger.error("No products found in parquet file")
            return
        
        # Log first few products for debugging
        for i, product in enumerate(products[:3]):
            logger.debug(f"Sample product {i+1}: {product.get('code', 'unknown')} - {product.get('name', 'unknown')}")
        
        async with get_async_session() as session:
            processed_count = 0
            error_count = 0
            
            for pdata in products:
                try:
                    logger.debug(f"Processing product: {pdata.get('code', 'unknown')} (ID: {pdata.get('id', 'unknown')})")
                    
                    # Reconstruct the original nested structure for compatibility
                    # Create brand data structure
                    brand_data = {
                        "id": pdata.get("brand_id"),
                        "active": pdata.get("active", True),
                        "modified_by": pdata.get("modified_by"),
                        "modified": pdata.get("modified"),
                        "created_by": pdata.get("created_by"),
                        "created": pdata.get("created"),
                        "deleted_by": pdata.get("deleted_by"),
                        "deleted": pdata.get("deleted"),
                        "code": pdata.get("brand_code"),
                        "name": pdata.get("brand_name"),
                        "store": pdata.get("brand_store"),
                        "distributor": {
                            "id": pdata.get("distributor_id"),
                            "active": pdata.get("active", True),
                            "modified_by": pdata.get("modified_by"),
                            "modified": pdata.get("modified"),
                            "created_by": pdata.get("created_by"),
                            "created": pdata.get("created"),
                            "deleted_by": pdata.get("deleted_by"),
                            "deleted": pdata.get("deleted"),
                            "code": pdata.get("distributor_code"),
                            "name": pdata.get("distributor_name"),
                            "store": pdata.get("distributor_store"),
                        }
                    }
                    
                    logger.debug(f"Brand data: {brand_data.get('code', 'unknown')} for distributor: {brand_data['distributor'].get('code', 'unknown')}")
                    
                    # Get or create distributor
                    try:
                        logger.debug(f"Getting/creating distributor: {brand_data['distributor'].get('code', 'unknown')}")
                        distributor = await get_or_create_distributor(session, brand_data["distributor"])
                        logger.debug(f"✓ Distributor processed: {brand_data['distributor'].get('code', 'unknown')} (ID: {distributor.id})")
                    except Exception as e:
                        logger.error(f"✗ Error creating distributor {brand_data['distributor'].get('code', 'unknown')}: {str(e)}")
                        error_count += 1
                        await session.rollback()
                        continue

                    # Get or create brand
                    try:
                        logger.debug(f"Getting/creating brand: {brand_data.get('code', 'unknown')}")
                        brand = await get_or_create_brand(session, brand_data, distributor)
                        logger.debug(f"✓ Brand processed: {brand_data.get('code', 'unknown')} (ID: {brand.id})")
                    except Exception as e:
                        logger.error(f"✗ Error creating brand {brand_data.get('code', 'unknown')}: {str(e)}")
                        error_count += 1
                        await session.rollback()
                        continue

                    # Create or update product
                    try:
                        logger.debug(f"Creating/updating product: {pdata.get('code', 'unknown')}")
                        
                        # Handle CTC data if present
                        ctc_class = None
                        ctc_type = None
                        ctc_category = None
                        
                        # Check for CTC data in product
                        if "product_class" in pdata and pdata["product_class"]:
                            ctc_class = await get_or_create_ctc_class(session, pdata["product_class"])
                            logger.debug(f"✓ CTC Class processed: {pdata['product_class'].get('code', 'unknown')}")
                        
                        if "product_type" in pdata and pdata["product_type"]:
                            if ctc_class:
                                ctc_type = await get_or_create_ctc_type(session, pdata["product_type"], ctc_class)
                                logger.debug(f"✓ CTC Type processed: {pdata['product_type'].get('code', 'unknown')}")
                        
                        if "product_category" in pdata and pdata["product_category"]:
                            if ctc_type:
                                ctc_category = await get_or_create_ctc_category(session, pdata["product_category"], ctc_type)
                                logger.debug(f"✓ CTC Category processed: {pdata['product_category'].get('code', 'unknown')}")
                        
                        product = await create_or_update_product(session, pdata, brand, distributor, ctc_class, ctc_type, ctc_category)
                        logger.debug(f"✓ Product processed: {pdata.get('code', 'unknown')} (ID: {product.id})")
                        
                        # Log core group information for debugging
                        if product.core_group:
                            logger.debug(f"  - Core group: {product.core_group}")
                    except Exception as e:
                        logger.error(f"✗ Error creating product {pdata.get('code', 'unknown')}: {str(e)}")
                        error_count += 1
                        await session.rollback()
                        continue

                    # Create price levels
                    try:
                        all_prices = pdata.get("all_prices", {})
                        if isinstance(all_prices, str):
                            all_prices = json.loads(all_prices)
                        logger.debug(f"Creating price levels for product: {pdata.get('code', 'unknown')} ({len(all_prices)} price levels)")
                        await create_price_levels(session, product, all_prices)
                        logger.debug(f"✓ Price levels processed for product: {pdata.get('code', 'unknown')}")
                    except Exception as e:
                        logger.error(f"✗ Error creating price levels for product {pdata.get('code', 'unknown')}: {str(e)}")
                        error_count += 1
                        await session.rollback()
                        continue

                    # Create my price
                    try:
                        my_prices = pdata.get("my_prices", {})
                        if isinstance(my_prices, str):
                            my_prices = json.loads(my_prices)
                        logger.debug(f"Creating my price for product: {pdata.get('code', 'unknown')}")
                        await create_my_price(session, product, my_prices)
                        logger.debug(f"✓ My price processed for product: {pdata.get('code', 'unknown')}")
                    except Exception as e:
                        logger.error(f"✗ Error creating my price for product {pdata.get('code', 'unknown')}: {str(e)}")
                        error_count += 1
                        await session.rollback()
                        continue

                except Exception as e:
                    print(f"✗ Unexpected error processing product {pdata.get('code', 'unknown')}: {str(e)}")
                    await session.rollback()
                    continue

            await session.commit()
            
            # Log summary of imported products with core groups
            core_group_summary = await session.execute(
                select(ProductModel.core_group, func.count(ProductModel.id))
                .where(ProductModel.core_group.in_(['A', 'B', 'C', 'D', 'E']))
                .group_by(ProductModel.core_group)
                .order_by(ProductModel.core_group)
            )
            core_group_counts = core_group_summary.all()
            
            logger.info("Core group import summary:")
            for core_group, count in core_group_counts:
                logger.info(f"  Core Group {core_group}: {count} products")
            
    except Exception as e:
        logger.error(f"Failed to import products from parquet: {e}")
        raise


async def initialize_products_data():
    """Initialize products data from parquet file."""
    try:
        logger.info("Starting product data initialization from parquet file...")
        await import_products_from_parquet()
        logger.info("Product data initialization completed successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize products data: {e}")
        raise


async def main():
    await init_db(drop_existing=True, load_ctc_data=True, load_brands_data=True)
    await initialize_products_data()
    print("Import completed")


if __name__ == "__main__":
    asyncio.run(main())
