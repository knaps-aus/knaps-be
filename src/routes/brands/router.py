from fastapi import APIRouter, HTTPException, Response
from typing import List
from ...models import BrandCreate, BrandRead, BrandUpdate
from ...storage import storage
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/brands")

@router.get("", response_model=List[BrandRead])
async def list_brands():
    """Get all brands"""
    return await storage.get_brands()

@router.get("/search", response_model=List[BrandRead])
async def search_brands(q: str):
    """Search brands by name, code, or store"""
    if len(q) < 2:
        return []
    return await storage.search_brands(q)

@router.get("/{brand_uuid}", response_model=BrandRead)
async def get_brand(brand_uuid: str):
    """Get a brand by UUID"""
    brand = await storage.get_brand_by_uuid(brand_uuid)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.post("", response_model=BrandRead, status_code=201)
async def create_brand(data: BrandCreate):
    """Create a new brand"""
    # Check if brand code already exists
    existing = await storage.get_brand_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Brand code already exists")
    
    # Verify that the distributor exists
    distributor = await storage.get_distributor(data.distributor_id)
    if not distributor:
        raise HTTPException(status_code=400, detail="Distributor not found")
    
    return await storage.create_brand(data)

@router.put("/{brand_uuid}", response_model=BrandRead)
async def update_brand(brand_uuid: str, data: BrandUpdate):
    """Update a brand by UUID"""
    # First get the brand to get its ID
    brand = await storage.get_brand_by_uuid(brand_uuid)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # If code is being updated, check if new code already exists
    if data.code and data.code != brand.code:
        existing = await storage.get_brand_by_code(data.code)
        if existing:
            raise HTTPException(status_code=400, detail="Brand code already exists")
    
    # If distributor_id is being updated, verify the new distributor exists
    if data.distributor_id and data.distributor_id != brand.distributor_id:
        distributor = await storage.get_distributor(data.distributor_id)
        if not distributor:
            raise HTTPException(status_code=400, detail="Distributor not found")
    
    updated_brand = await storage.update_brand(brand.id, data)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return updated_brand

@router.delete("/{brand_uuid}", status_code=204)
async def delete_brand(brand_uuid: str):
    """Delete a brand by UUID"""
    # First get the brand to get its ID
    brand = await storage.get_brand_by_uuid(brand_uuid)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    deleted = await storage.delete_brand(brand.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Brand not found")
    return Response(status_code=204)

@router.get("/distributor/{distributor_id}", response_model=List[BrandRead])
async def get_brands_by_distributor(distributor_id: str):
    """Get all brands for a specific distributor"""
    # First get the distributor to get its ID
    try:
        distributor_id_int = int(distributor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid distributor ID format")
    
    distributor = await storage.get_distributor(distributor_id_int)
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    
    return await storage.get_brands_by_distributor(distributor.id) 