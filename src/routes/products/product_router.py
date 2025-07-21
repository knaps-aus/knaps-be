from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from ...models import Product, InsertProduct, ProductCTCCategoryRead, ProductCTCHierarchy, PriceLevel, InsertPriceLevel, MyPrice
from ...storage import storage
from ...models import AssignProductToCategoryRequest
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/products")

@router.get("", response_model=List[Product])
async def list_products():
    return await storage.get_products()

@router.get("/search", response_model=List[Product])
async def search_products(q: str):
    logger.info(f"Searching for product: {q}")
    if len(q) < 2:
        return []
    return await storage.search_products(q)

@router.get("/core-range", response_model=List[Product])
async def get_products_by_core_range(
    distributor_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    core_groups: Optional[str] = None,  # Comma-separated string like "A,B,C"
    class_id: Optional[int] = None,
    type_id: Optional[int] = None,
    category_id: Optional[int] = None
):
    """
    Get products filtered by core range parameters.
    
    Args:
        distributor_id: Filter by distributor ID
        brand_id: Filter by brand ID
        core_groups: Comma-separated list of core group codes (e.g., "A,B,C")
        class_id: Filter by CTC class ID
        type_id: Filter by CTC type ID
        category_id: Filter by CTC category ID
        
    Returns:
        List of products matching the criteria
    """
    # Parse core_groups string into list
    core_groups_list = None
    if core_groups:
        core_groups_list = [group.strip() for group in core_groups.split(",") if group.strip()]
    
    logger.info(f"Filtering products by core range - distributor_id: {distributor_id}, brand_id: {brand_id}, core_groups: {core_groups_list}, class_id: {class_id}, type_id: {type_id}, category_id: {category_id}")
    
    return await storage.get_products_by_core_range(
        distributor_id=distributor_id,
        brand_id=brand_id,
        core_groups=core_groups_list,
        class_id=class_id,
        type_id=type_id,
        category_id=category_id
    )

@router.get("/{product_code}", response_model=Product)
async def get_product(product_code: str):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("", response_model=Product, status_code=201)
async def create_product(data: InsertProduct):
    existing = await storage.get_product_by_code(data.product_code)
    if existing:
        raise HTTPException(status_code=400, detail="Product code already exists")
    return await storage.create_product(data)

@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: int, data: Product):
    product = await storage.update_product(product_id, data.dict(exclude_unset=True))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int):
    deleted = await storage.delete_product(product_id)
    if not deleted:        
        raise HTTPException(status_code=404, detail="Product not found")
    return Response(status_code=204)

@router.post("/bulk")
async def bulk_create(products: List[InsertProduct]):
    logger.info("Starting bulk product upload")
    results: List[Product] = []
    errors: List[str] = []
    for data in products:
        logger.info(f"Uploading {data.product_code}, product data {data}")
        try:
            if await storage.get_product_by_code(data.product_code):
                logger.info(f"Product code already exists {data.product_code}")
                #TODO add check if attributes are different then update 
                continue
            product = await storage.create_product(data)
            results.append(product)
        except Exception as e:
            logger.warning(f"Failed to create product with code {data.product_code} with error {e}")
            errors.append(data.product_code)
    return {
        "success": len(results),
        "errors": len(errors),
        "created": results,
        "failed": errors,
    }

@router.get("/{product_code}/ctc-hierarchy", response_model=ProductCTCHierarchy)
async def get_product_ctc_hierarchy(product_code: str):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Get the first CTC category for this product (if any)
    ctc_categories = await storage.get_categories_by_product(product.id)
    if not ctc_categories:
        raise HTTPException(status_code=404, detail="No CTC category assigned to this product")
    category = ctc_categories[0]
    # Get type and class
    type_ = await storage.get_type_by_id(category.type_id)
    class_ = await storage.get_class_by_id(type_.class_id)
    return ProductCTCHierarchy(
        class_id=class_.id,
        class_code=class_.code,
        class_name=class_.name,
        type_id=type_.id,
        type_code=type_.code,
        type_name=type_.name,
        category_id=category.id,
        category_code=category.code,
        category_name=category.name
    )

@router.get("/{product_code}/ctc-categories", response_model=List[ProductCTCCategoryRead])
async def get_product_ctc_categories(product_code: str):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    ctc_categories = await storage.get_categories_by_product(product.id)
    result = []
    for category in ctc_categories:
        type_ = await storage.get_type_by_id(category.type_id)
        class_ = await storage.get_class_by_id(type_.class_id)
        result.append(ProductCTCCategoryRead(
            id=category.id,
            uuid=category.uuid,
            code=category.code,
            name=category.name,
            type_id=type_.id,
            type_code=type_.code,
            type_name=type_.name,
            class_id=class_.id,
            class_code=class_.code,
            class_name=class_.name
        ))
    return result

@router.post("/{product_code}/ctc-categories/{category_id}")
async def assign_product_to_ctc_category(product_code: str, category_id: int):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    success = await storage.assign_product_to_category(category_id, product.id)
    if not success:
        raise HTTPException(status_code=400, detail="Assignment failed (category or product not found)")
    return {"message": "Product assigned to CTC category"}

@router.delete("/{product_code}/ctc-categories/{category_id}")
async def unassign_product_from_ctc_category(product_code: str, category_id: int):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Only unassign if this product is assigned to this category
    ctc_categories = await storage.get_categories_by_product(product.id)
    if not any(cat.id == category_id for cat in ctc_categories):
        raise HTTPException(status_code=404, detail="Product is not assigned to this CTC category")
    # Unassign by setting product_id to None
    await storage.remove_product_from_category(category_id)
    return {"message": "Product unassigned from CTC category"}

@router.get("/ctc/categories/{category_id}/products")
async def get_products_by_ctc_category(category_id: int):
    products = await storage
    return products

# Price Level endpoints
@router.get("/{product_code}/price-levels", response_model=List[PriceLevel])
async def get_product_price_levels(product_code: str):
    """Get all price levels for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await storage.get_product_price_levels(product.id)

@router.get("/{product_code}/price-levels/{price_id}", response_model=PriceLevel)
async def get_price_level(product_code: str, price_id: int):
    """Get a specific price level for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    price_level = await storage.get_price_level(price_id)
    if not price_level:
        raise HTTPException(status_code=404, detail="Price level not found")
    
    # Verify the price level belongs to this product
    if price_level.product_id != product.id:
        raise HTTPException(status_code=404, detail="Price level not found for this product")
    
    return price_level

@router.post("/{product_code}/price-levels", response_model=PriceLevel, status_code=201)
async def create_price_level(product_code: str, data: InsertPriceLevel):
    """Create a new price level for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        return await storage.create_price_level(product.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{product_code}/price-levels/{price_id}", response_model=PriceLevel)
async def update_price_level(product_code: str, price_id: int, data: dict):
    """Update a specific price level for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    price_level = await storage.get_price_level(price_id)
    if not price_level:
        raise HTTPException(status_code=404, detail="Price level not found")
    
    # Verify the price level belongs to this product
    if price_level.product_id != product.id:
        raise HTTPException(status_code=404, detail="Price level not found for this product")
    
    updated_price = await storage.update_price_level(price_id, data)
    if not updated_price:
        raise HTTPException(status_code=404, detail="Price level not found")
    
    return updated_price

@router.delete("/{product_code}/price-levels/{price_id}", status_code=204)
async def delete_price_level(product_code: str, price_id: int):
    """Delete a specific price level for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    price_level = await storage.get_price_level(price_id)
    if not price_level:
        raise HTTPException(status_code=404, detail="Price level not found")
    
    # Verify the price level belongs to this product
    if price_level.product_id != product.id:
        raise HTTPException(status_code=404, detail="Price level not found for this product")
    
    deleted = await storage.delete_price_level(price_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Price level not found")
    
    return Response(status_code=204)

# MyPrice endpoints
@router.get("/{product_code}/my-price", response_model=MyPrice)
async def get_product_my_price(product_code: str):
    """Get MyPrice for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    my_price = await storage.get_product_my_price(product.id)
    if not my_price:
        raise HTTPException(status_code=404, detail="MyPrice not found for this product")
    
    return my_price

@router.post("/{product_code}/my-price", response_model=MyPrice, status_code=201)
async def create_or_update_my_price(product_code: str, data: dict):
    """Create or update MyPrice for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        return await storage.create_or_update_my_price(product.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{product_code}/my-price", response_model=MyPrice)
async def update_my_price(product_code: str, data: dict):
    """Update MyPrice for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        return await storage.create_or_update_my_price(product.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{product_code}/my-price", status_code=204)
async def delete_my_price(product_code: str):
    """Delete MyPrice for a product"""
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    deleted = await storage.delete_my_price(product.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="MyPrice not found for this product")
    
    return Response(status_code=204)
