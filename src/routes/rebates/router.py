from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from ...models import (
    RebateAgreementCreate, 
    RebateAgreementRead,
    DealSourceCreate,
    DealSourceRead,
    DealSourceUpdate,
    DealTypeCreate,
    DealTypeRead,
    DealTypeUpdate,
    # NEW DEAL MODELS
    DealValueTypeCreate,
    DealValueTypeRead,
    DealValueTypeUpdate,
    DealCalculationCreate,
    DealCalculationRead,
    DealCalculationUpdate
)
from ...storage import storage
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/rebates")

@router.post("/agreements", response_model=RebateAgreementRead, status_code=201)
async def create_rebate_agreement(data: RebateAgreementCreate):
    """
    Create a new rebate agreement (vendor or customer rebate program).
    
    This endpoint validates the input and creates a new rebate agreement with:
    - Agreement terms and tier structures
    - Product and category associations
    - Validation for overlapping ranges and business rules
    
    Returns the newly created agreement data.
    """
    try:
        return await storage.create_rebate_agreement(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating rebate agreement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/agreements", response_model=List[RebateAgreementRead])
async def list_rebate_agreements(
    agreement_type: Optional[str] = None,
    distributor_id: Optional[int] = None,
    status: Optional[str] = None,
    deal_type_id: Optional[int] = None,
    deal_source_id: Optional[int] = None,
    store: Optional[str] = None,
    active_only: bool = True
):
    """
    List rebate agreements with optional filtering.
    
    Enhanced filtering options:
    - agreement_type: Filter by agreement type (vendor/customer)
    - distributor_id: Filter by distributor
    - status: Filter by agreement status
    - deal_type_id: Filter by deal type
    - deal_source_id: Filter by deal source
    - store: Filter by store
    - active_only: Show only active agreements
    """
    return await storage.get_rebate_agreements(
        agreement_type=agreement_type,
        distributor_id=distributor_id,
        status=status,
        deal_type_id=deal_type_id,
        deal_source_id=deal_source_id,
        store=store
    )

@router.get("/agreements/search", response_model=List[RebateAgreementRead])
async def search_rebate_agreements(
    brand_id: Optional[int] = None,
    distributor_id: Optional[int] = None,
    deal_type_id: Optional[int] = None,
    status: Optional[str] = None,
    agreement_type: Optional[str] = None,
    deal_source_id: Optional[int] = None,
    store: Optional[str] = None
):
    """
    Search rebate agreements by brand, distributor, deal type, and status.
    If brand_id is provided, will filter by agreements linked to products of that brand.
    """
    if brand_id is not None:
        return await storage.get_rebate_agreements_by_brand(
            brand_id=brand_id,
            agreement_type=agreement_type,
            distributor_id=distributor_id,
            status=status,
            deal_type_id=deal_type_id,
            deal_source_id=deal_source_id,
            store=store
        )
    else:
        return await storage.get_rebate_agreements(
            agreement_type=agreement_type,
            distributor_id=distributor_id,
            status=status,
            deal_type_id=deal_type_id,
            deal_source_id=deal_source_id,
            store=store
        )

@router.get("/agreements/{agreement_id}", response_model=RebateAgreementRead)
async def get_rebate_agreement(agreement_id: int):
    """Get a specific rebate agreement by ID."""
    agreement = await storage.get_rebate_agreement(agreement_id)
    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rebate agreement not found"
        )
    return agreement

@router.put("/agreements/{agreement_id}", response_model=RebateAgreementRead)
async def update_rebate_agreement(agreement_id: int, data: RebateAgreementCreate):
    """Update an existing rebate agreement."""
    try:
        agreement = await storage.update_rebate_agreement(agreement_id, data)
        if not agreement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rebate agreement not found"
            )
        return agreement
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/agreements/{agreement_id}", status_code=204)
async def delete_rebate_agreement(agreement_id: int):
    """Delete a rebate agreement."""
    success = await storage.delete_rebate_agreement(agreement_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rebate agreement not found"
        )


### DEAL VALUE TYPES ENDPOINTS ###

@router.get("/deal-value-types", response_model=List[DealValueTypeRead])
async def list_deal_value_types(active_only: bool = True):
    """List all deal value types with optional filtering for active only"""
    return await storage.get_deal_value_types(active_only)

@router.get("/deal-value-types/{value_type_id}", response_model=DealValueTypeRead)
async def get_deal_value_type(value_type_id: int):
    """Get a specific deal value type by ID"""
    value_type = await storage.get_deal_value_type(value_type_id)
    if not value_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal value type not found"
        )
    return value_type

@router.get("/deal-value-types/code/{code}", response_model=DealValueTypeRead)
async def get_deal_value_type_by_code(code: str):
    """Get a deal value type by code"""
    value_type = await storage.get_deal_value_type_by_code(code)
    if not value_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal value type not found"
        )
    return value_type

@router.post("/deal-value-types", response_model=DealValueTypeRead, status_code=201)
async def create_deal_value_type(data: DealValueTypeCreate):
    """Create a new deal value type"""
    try:
        return await storage.create_deal_value_type(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating deal value type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/deal-value-types/{value_type_id}", response_model=DealValueTypeRead)
async def update_deal_value_type(value_type_id: int, data: DealValueTypeUpdate):
    """Update an existing deal value type"""
    try:
        value_type = await storage.update_deal_value_type(value_type_id, data)
        if not value_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal value type not found"
            )
        return value_type
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/deal-value-types/{value_type_id}", status_code=204)
async def delete_deal_value_type(value_type_id: int, soft_delete: bool = True):
    """Delete a deal value type"""
    success = await storage.delete_deal_value_type(value_type_id, soft_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal value type not found"
        )


### DEAL CALCULATIONS ENDPOINTS ###

@router.get("/deal-calculations", response_model=List[DealCalculationRead])
async def list_deal_calculations(
    rebate_agreement_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    active_only: bool = True
):
    """
    List deal calculations with optional filtering.
    
    Filtering options:
    - rebate_agreement_id: Filter by rebate agreement
    - product_id: Filter by product
    - status: Filter by calculation status (pending/approved/rejected/paid)
    - active_only: Show only active calculations
    """
    return await storage.get_deal_calculations(
        rebate_agreement_id=rebate_agreement_id,
        product_id=product_id,
        status=status,
        active_only=active_only
    )

@router.get("/deal-calculations/{calculation_id}", response_model=DealCalculationRead)
async def get_deal_calculation(calculation_id: int):
    """Get a specific deal calculation by ID"""
    calculation = await storage.get_deal_calculation(calculation_id)
    if not calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal calculation not found"
        )
    return calculation

@router.post("/deal-calculations", response_model=DealCalculationRead, status_code=201)
async def create_deal_calculation(data: DealCalculationCreate):
    """Create a new deal calculation"""
    try:
        return await storage.create_deal_calculation(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating deal calculation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/deal-calculations/{calculation_id}", response_model=DealCalculationRead)
async def update_deal_calculation(calculation_id: int, data: DealCalculationUpdate):
    """Update an existing deal calculation"""
    try:
        calculation = await storage.update_deal_calculation(calculation_id, data)
        if not calculation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal calculation not found"
            )
        return calculation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/deal-calculations/{calculation_id}", status_code=204)
async def delete_deal_calculation(calculation_id: int, soft_delete: bool = True):
    """Delete a deal calculation"""
    success = await storage.delete_deal_calculation(calculation_id, soft_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal calculation not found"
        )


### DEAL SOURCES ENDPOINTS ###

@router.get("/deal-sources", response_model=List[DealSourceRead])
async def list_deal_sources(active_only: bool = True):
    """List all deal sources with optional filtering for active only"""
    return await storage.get_deal_sources(active_only)

@router.get("/deal-sources/{source_id}", response_model=DealSourceRead)
async def get_deal_source(source_id: int):
    """Get a specific deal source by ID"""
    deal_source = await storage.get_deal_source(source_id)
    if not deal_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal source not found"
        )
    return deal_source

@router.get("/deal-sources/code/{code}", response_model=DealSourceRead)
async def get_deal_source_by_code(code: str):
    """Get a deal source by code"""
    deal_source = await storage.get_deal_source_by_code(code)
    if not deal_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal source not found"
        )
    return deal_source

@router.post("/deal-sources", response_model=DealSourceRead, status_code=201)
async def create_deal_source(data: DealSourceCreate):
    """Create a new deal source"""
    try:
        return await storage.create_deal_source(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating deal source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/deal-sources/{source_id}", response_model=DealSourceRead)
async def update_deal_source(source_id: int, data: DealSourceUpdate):
    """Update an existing deal source"""
    try:
        deal_source = await storage.update_deal_source(source_id, data)
        if not deal_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal source not found"
            )
        return deal_source
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/deal-sources/{source_id}", status_code=204)
async def delete_deal_source(source_id: int, soft_delete: bool = True):
    """Delete a deal source"""
    success = await storage.delete_deal_source(source_id, soft_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal source not found"
        )


### DEAL TYPES ENDPOINTS ###

@router.get("/deal-types", response_model=List[DealTypeRead])
async def list_deal_types(active_only: bool = True):
    """List all deal types with optional filtering for active only"""
    return await storage.get_deal_types(active_only)

@router.get("/deal-types/{type_id}", response_model=DealTypeRead)
async def get_deal_type(type_id: int):
    """Get a specific deal type by ID"""
    deal_type = await storage.get_deal_type(type_id)
    if not deal_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal type not found"
        )
    return deal_type

@router.get("/deal-types/code/{code}", response_model=DealTypeRead)
async def get_deal_type_by_code(code: str):
    """Get a deal type by code"""
    deal_type = await storage.get_deal_type_by_code(code)
    if not deal_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal type not found"
        )
    return deal_type

@router.post("/deal-types", response_model=DealTypeRead, status_code=201)
async def create_deal_type(data: DealTypeCreate):
    """Create a new deal type"""
    try:
        return await storage.create_deal_type(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating deal type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/deal-types/{type_id}", response_model=DealTypeRead)
async def update_deal_type(type_id: int, data: DealTypeUpdate):
    """Update an existing deal type"""
    try:
        deal_type = await storage.update_deal_type(type_id, data)
        if not deal_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal type not found"
            )
        return deal_type
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/deal-types/{type_id}", status_code=204)
async def delete_deal_type(type_id: int, soft_delete: bool = True):
    """Delete a deal type"""
    success = await storage.delete_deal_type(type_id, soft_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal type not found"
        ) 