from fastapi import APIRouter, HTTPException, Response, status
from typing import List, Optional
from ...models import (
    PriceLevelTypeCreate, 
    PriceLevelTypeRead, 
    PriceLevelTypeUpdate
)
from ...storage import storage
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/price-level-types")

@router.get("", response_model=List[PriceLevelTypeRead])
async def list_price_level_types(active_only: bool = True):
    """List all price level types with optional filtering for active only"""
    return await storage.get_price_level_types(active_only)

@router.get("/{type_id}", response_model=PriceLevelTypeRead)
async def get_price_level_type(type_id: int):
    """Get a specific price level type by ID"""
    price_level_type = await storage.get_price_level_type(type_id)
    if not price_level_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price level type not found"
        )
    return price_level_type

@router.get("/code/{code}", response_model=PriceLevelTypeRead)
async def get_price_level_type_by_code(code: str):
    """Get a price level type by code"""
    price_level_type = await storage.get_price_level_type_by_code(code)
    if not price_level_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price level type not found"
        )
    return price_level_type

@router.post("", response_model=PriceLevelTypeRead, status_code=201)
async def create_price_level_type(data: PriceLevelTypeCreate):
    """Create a new price level type"""
    try:
        return await storage.create_price_level_type(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating price level type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{type_id}", response_model=PriceLevelTypeRead)
async def update_price_level_type(type_id: int, data: PriceLevelTypeUpdate):
    """Update an existing price level type"""
    try:
        price_level_type = await storage.update_price_level_type(type_id, data)
        if not price_level_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price level type not found"
            )
        return price_level_type
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{type_id}", status_code=204)
async def delete_price_level_type(type_id: int, soft_delete: bool = True):
    """Delete a price level type"""
    success = await storage.delete_price_level_type(type_id, soft_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price level type not found"
        )
    return Response(status_code=204) 