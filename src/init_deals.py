import os
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .db_models import (
    RebateAgreement, DealType, DealSource, PriceLevelType, DealValueType, Brand, Distributor, RebateAgreementProduct
)
from .database import get_async_session

logger = logging.getLogger(__name__)

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
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None

async def get_or_create(session: AsyncSession, model, unique_field: str, data: Dict[str, Any], defaults: Dict[str, Any] = None):
    stmt = select(model).where(getattr(model, unique_field) == data[unique_field])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = model(**{**data, **(defaults or {})})
    session.add(obj)
    await session.flush()
    return obj

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
    stmt = select(DealSource).where(DealSource.code == data["code"])
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
    stmt = select(PriceLevelType).where(PriceLevelType.code == data["code"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
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
    stmt = select(DealValueType).where(DealValueType.code == data["code"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = DealValueType(
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        symbol=data.get("symbol"),
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

async def get_or_create_brand(session: AsyncSession, data: Dict[str, Any], distributor: Distributor) -> Brand:
    stmt = select(Brand).where(Brand.code == data["code"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = Brand(
        id=data["id"],
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        is_hof_pref=data.get("is_hof_pref", True),
        comments=data.get("comments"),
        narta_rept=data.get("narta_rept", True),
        distributor_id=distributor.id
    )
    session.add(obj)
    await session.flush()
    return obj

async def get_or_create_distributor(session: AsyncSession, data: Dict[str, Any]) -> Distributor:
    stmt = select(Distributor).where(Distributor.code == data["code"])
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj
    obj = Distributor(
        id=data["id"],
        code=data["code"],
        name=data.get("name", data["code"]),
        store=data.get("store", "QHOF"),
        active=data.get("active", True),
        modified_by=data.get("modified_by", "import"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by", "import"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        edi=data.get("edi", False),
        auto_claim_over_charge=data.get("auto_claim_over_charge", False),
        is_central=data.get("is_central", True),
        icon_owner=data.get("icon_owner"),
        gln=data.get("GLN"),
        business_number=data.get("business_number"),
        accounting_date=data.get("accounting_date"),
        web_portal_url=data.get("web_portal_url"),
        pp_claim_from=None,
        fis_minimum_order=data.get("FIS_minimum_order"),
        default_extended_credits_code=data.get("default_extended_credits", {}).get("code"),
        default_extended_credits_name=data.get("default_extended_credits", {}).get("name")
    )
    session.add(obj)
    await session.flush()
    return obj

async def initialize_deals_data() -> bool:
    logger.info("Starting deals data initialization...")
    deal_data_dir = os.path.join("data_management", "data", "deal_data")
    files = [f for f in os.listdir(deal_data_dir) if f.endswith(".json")]
    total_deals = 0
    errors = 0
    async with get_async_session() as session:
        for fname in files:
            path = os.path.join(deal_data_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                try:
                    deals = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load {fname}: {e}")
                    errors += 1
                    continue
            for deal in deals:
                try:
                    # --- Ensure referenced objects exist ---
                    # DealSource
                    provider = deal.get("provider_source")
                    if provider:
                        provider_obj = await get_or_create_dealsource(session, provider)
                    else:
                        provider_obj = None
                    # DealType
                    bonus_type = deal.get("bonus_type")
                    if bonus_type:
                        dealtype_obj = await get_or_create_dealtype(session, bonus_type)
                    else:
                        dealtype_obj = None
                    # PriceLevelType
                    price_level = deal.get("price_level")
                    if price_level:
                        pricelevel_obj = await get_or_create_priceleveltype(session, price_level)
                    else:
                        pricelevel_obj = None
                    # ValueType
                    value_type = deal.get("value_type")
                    if value_type:
                        valuetype_obj = await get_or_create_valuetype(session, value_type)
                    else:
                        valuetype_obj = None
                    # Brand/Distributor
                    brand = deal.get("brand")
                    if brand:
                        distributor = brand.get("distributor")
                        if distributor:
                            distributor_obj = await get_or_create_distributor(session, distributor)
                        else:
                            distributor_obj = None
                        brand_obj = await get_or_create_brand(session, brand, distributor_obj) if distributor else None
                    else:
                        brand_obj = None
                        distributor_obj = None
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
                        status=deal.get("bonus_status", {}).get("name", "active"),
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
                        bonus_status_code=deal.get("bonus_status", {}).get("code"),
                        bonus_status_name=deal.get("bonus_status", {}).get("name"),
                        deal_code=str(deal.get("code")),
                        store=deal.get("store"),
                        created_at=parse_dt(deal.get("created")),
                        created_by=deal.get("created_by", "import"),
                        modified_at=parse_dt(deal.get("modified")),
                        modified_by=deal.get("modified_by", "import"),
                        deleted_at=parse_dt(deal.get("deleted")),
                        deleted_by=deal.get("deleted_by")
                    )
                    session.add(agreement)
                    await session.flush()
                    # Optionally, link to product/category via RebateAgreementProduct
                    # (not implemented here, but can be added if product/category info is present)
                    total_deals += 1
                except Exception as e:
                    logger.error(f"Error processing deal in {fname}: {e}")
                    errors += 1
                    await session.rollback()
        await session.commit()
    logger.info(f"Deals initialization completed: {total_deals} deals imported, {errors} errors.")
    return errors == 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_deals_data())

