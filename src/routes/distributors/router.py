from fastapi import APIRouter, HTTPException, Response
from typing import List
from ...models import DistributorCreate, DistributorRead, DistributorUpdate
from ...storage import storage
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/distributors")

@router.get("", response_model=List[DistributorRead])
async def list_distributors():
    """Get all distributors"""
    return await storage.get_distributors()

@router.get("/search", response_model=List[DistributorRead])
async def search_distributors(q: str):
    """Search distributors by name, code, or store"""
    if len(q) < 2:
        return []
    return await storage.search_distributors(q)

@router.get("/{distributor_uuid}", response_model=DistributorRead)
async def get_distributor(distributor_uuid: str):
    """Get a distributor by UUID"""
    distributor = await storage.get_distributor_by_uuid(distributor_uuid)
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return distributor

@router.post("", response_model=DistributorRead, status_code=201)
async def create_distributor(data: DistributorCreate):
    """Create a new distributor"""
    # Check if distributor code already exists
    existing = await storage.get_distributor_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Distributor code already exists")
    
    return await storage.create_distributor(data)

@router.put("/{distributor_uuid}", response_model=DistributorRead)
async def update_distributor(distributor_uuid: str, data: DistributorUpdate):
    """Update a distributor by UUID"""
    # First get the distributor to get its ID
    distributor = await storage.get_distributor_by_uuid(distributor_uuid)
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    
    # If code is being updated, check if new code already exists
    if data.code and data.code != distributor.code:
        existing = await storage.get_distributor_by_code(data.code)
        if existing:
            raise HTTPException(status_code=400, detail="Distributor code already exists")
    
    updated_distributor = await storage.update_distributor(distributor.id, data)
    if not updated_distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return updated_distributor

@router.delete("/{distributor_uuid}", status_code=204)
async def delete_distributor(distributor_uuid: str):
    """Delete a distributor by UUID"""
    # First get the distributor to get its ID
    distributor = await storage.get_distributor_by_uuid(distributor_uuid)
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    
    deleted = await storage.delete_distributor(distributor.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return Response(status_code=204) 