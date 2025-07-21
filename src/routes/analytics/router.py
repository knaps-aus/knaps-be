from fastapi import APIRouter
from typing import List, Optional, Dict, Any
from ...models import ProductAnalytics, OverallAnalytics
from ...storage import storage

router = APIRouter(prefix="/analytics")

@router.get("/products", response_model=List[ProductAnalytics])
async def product_analytics(product_code: Optional[int] = None):
    return await storage.get_product_analytics(product_code)

@router.get("/overall", response_model=OverallAnalytics)
async def overall_analytics():
    return await storage.get_overall_analytics()

@router.get("/deals", response_model=Dict[str, Any])
async def deal_analytics():
    """
    Get comprehensive analytics for deals and rebate agreements.
    
    Returns:
    - Total rebate agreements by type
    - Deal calculations by status
    - Deal value types distribution
    - Deal sources and types statistics
    - Recent deal activity
    """
    return await storage.get_deal_analytics()

@router.get("/deals/calculations", response_model=Dict[str, Any])
async def deal_calculations_analytics(
    rebate_agreement_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None
):
    """
    Get analytics for deal calculations.
    
    Returns:
    - Calculations by status
    - Total values processed
    - Average deal values
    - Calculation trends
    """
    return await storage.get_deal_calculations_analytics(
        rebate_agreement_id=rebate_agreement_id,
        product_id=product_id,
        status=status
    )
