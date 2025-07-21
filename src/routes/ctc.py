from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..storage import storage
from ..models import (
    CTCClassCreate, CTCClassRead, CTCClassUpdate, CTCClassHierarchy,
    CTCTypeCreate, CTCTypeRead, CTCTypeUpdate,
    CTCCategoryCreate, CTCCategoryRead, CTCCategoryUpdate, CTCCategoryWithAttributes,
    CTCAttributeGroupCreate, CTCAttributeGroupRead, CTCAttributeGroupUpdate,
    CTCDataTypeCreate, CTCDataTypeRead, CTCDataTypeUpdate,
    CTCUnitOfMeasureCreate, CTCUnitOfMeasureRead, CTCUnitOfMeasureUpdate,
    CTCAttributeCreate, CTCAttributeRead, CTCAttributeUpdate,
    CategoryAttributeCreate, CategoryAttributeRead, CategoryAttributeUpdate,
    CTCSearchResult, CTCStatistics, ConsolidatedHierarchyResponse,
    # CTC Link-Types models
    CTCTypeLinkCreate, CTCTypeLinkRead, CTCTypeOptionCreate, CTCTypeOptionRead,
    CTCTypeLinkQuery, CTCTypeOptionQuery, CTCTypeLinkResponse, CTCTypeLinksResponse,
    CTCTypeOptionResponse, CTCTypeOptionsResponse, CTCTypeLinkStatistics, CTCTypeOptionStatistics
)

router = APIRouter(prefix="/ctc", tags=["CTC"])

def to_schema(obj, schema_cls):
    """Convert SQLAlchemy object to Pydantic schema"""
    if hasattr(schema_cls, "model_validate"):
        return schema_cls.model_validate(obj, from_attributes=True)
    return schema_cls.from_orm(obj)


# ==================== CTC Classes (Level 1) ====================

@router.get("/classes", response_model=List[CTCClassRead])
async def get_all_classes(active_only: bool = Query(True, description="Only return active classes")):
    """Get all CTC classes"""
    try:
        classes = await storage.get_all_classes(active_only=active_only)
        return [to_schema(cls, CTCClassRead) for cls in classes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes: {str(e)}")


@router.get("/classes/{class_id}", response_model=CTCClassRead)
async def get_class_by_id(class_id: int):
    """Get a specific CTC class by ID"""
    try:
        class_obj = await storage.get_class_by_id(class_id)
        if not class_obj:
            raise HTTPException(status_code=404, detail="CTC class not found")
        return to_schema(class_obj, CTCClassRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving class: {str(e)}")


@router.get("/classes/uuid/{class_uuid}", response_model=CTCClassRead)
async def get_class_by_uuid(class_uuid: str):
    """Get a specific CTC class by UUID"""
    try:
        class_obj = await storage.get_class_by_uuid(class_uuid)
        if not class_obj:
            raise HTTPException(status_code=404, detail="CTC class not found")
        return to_schema(class_obj, CTCClassRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving class: {str(e)}")


@router.get("/classes/code/{code}", response_model=CTCClassRead)
async def get_class_by_code(code: str):
    """Get a specific CTC class by code"""
    try:
        class_obj = await storage.get_class_by_code(code)
        if not class_obj:
            raise HTTPException(status_code=404, detail="CTC class not found")
        return to_schema(class_obj, CTCClassRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving class: {str(e)}")


@router.post("/classes", response_model=CTCClassRead)
async def create_class(class_data: CTCClassCreate):
    """Create a new CTC class"""
    try:
        new_class = await storage.create_class(class_data.dict())
        return to_schema(new_class, CTCClassRead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating class: {str(e)}")


@router.put("/classes/{class_id}", response_model=CTCClassRead)
async def update_class(class_id: int, class_data: CTCClassUpdate):
    """Update an existing CTC class"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in class_data.dict().items() if v is not None}
        updated_class = await storage.update_class(class_id, update_data)
        if not updated_class:
            raise HTTPException(status_code=404, detail="CTC class not found")
        return to_schema(updated_class, CTCClassRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating class: {str(e)}")


@router.delete("/classes/{class_id}")
async def delete_class(class_id: int, soft_delete: bool = Query(True, description="Soft delete by default")):
    """Delete a CTC class"""
    try:
        success = await storage.delete_class(class_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="CTC class not found")
        return {"message": "CTC class deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting class: {str(e)}")


# ==================== CTC Types (Level 2) ====================

@router.get("/types/class/{class_id}", response_model=List[CTCTypeRead])
async def get_types_by_class(class_id: int, active_only: bool = Query(True, description="Only return active types")):
    """Get all types for a specific class"""
    try:
        types = await storage.get_types_by_class(class_id, active_only=active_only)
        return [to_schema(type_obj, CTCTypeRead) for type_obj in types]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving types: {str(e)}")


@router.get("/types/{type_id}", response_model=CTCTypeRead)
async def get_type_by_id(type_id: int):
    """Get a specific CTC type by ID"""
    try:
        type_obj = await storage.get_type_by_id(type_id)
        if not type_obj:
            raise HTTPException(status_code=404, detail="CTC type not found")
        return to_schema(type_obj, CTCTypeRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type: {str(e)}")


@router.get("/types/uuid/{type_uuid}", response_model=CTCTypeRead)
async def get_type_by_uuid(type_uuid: str):
    """Get a specific CTC type by UUID"""
    try:
        type_obj = await storage.get_type_by_uuid(type_uuid)
        if not type_obj:
            raise HTTPException(status_code=404, detail="CTC type not found")
        return to_schema(type_obj, CTCTypeRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type: {str(e)}")


@router.post("/types", response_model=CTCTypeRead)
async def create_type(type_data: CTCTypeCreate):
    """Create a new CTC type"""
    try:
        new_type = await storage.create_type(type_data.dict())
        return to_schema(new_type, CTCTypeRead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating type: {str(e)}")


@router.put("/types/{type_id}", response_model=CTCTypeRead)
async def update_type(type_id: int, type_data: CTCTypeUpdate):
    """Update an existing CTC type"""
    try:
        update_data = {k: v for k, v in type_data.dict().items() if v is not None}
        updated_type = await storage.update_type(type_id, update_data)
        if not updated_type:
            raise HTTPException(status_code=404, detail="CTC type not found")
        return to_schema(updated_type, CTCTypeRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating type: {str(e)}")


@router.delete("/types/{type_id}")
async def delete_type(type_id: int, soft_delete: bool = Query(True, description="Soft delete by default")):
    """Delete a CTC type"""
    try:
        success = await storage.delete_type(type_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="CTC type not found")
        return {"message": "CTC type deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting type: {str(e)}")


# ==================== CTC Categories (Level 3) ====================

@router.get("/categories/type/{type_id}", response_model=List[CTCCategoryRead])
async def get_categories_by_type(type_id: int, active_only: bool = Query(True, description="Only return active categories")):
    """Get all categories for a specific type"""
    try:
        categories = await storage.get_categories_by_type(type_id, active_only=active_only)
        return [to_schema(cat, CTCCategoryRead) for cat in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")


@router.get("/categories/{category_id}", response_model=CTCCategoryRead)
async def get_category_by_id(category_id: int):
    """Get a specific CTC category by ID"""
    try:
        category = await storage.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="CTC category not found")
        return to_schema(category, CTCCategoryRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving category: {str(e)}")


@router.get("/categories/uuid/{category_uuid}", response_model=CTCCategoryRead)
async def get_category_by_uuid(category_uuid: str):
    """Get a specific CTC category by UUID"""
    try:
        category = await storage.get_category_by_uuid(category_uuid)
        if not category:
            raise HTTPException(status_code=404, detail="CTC category not found")
        return to_schema(category, CTCCategoryRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving category: {str(e)}")


@router.get("/categories/code/{code}", response_model=CTCCategoryRead)
async def get_category_by_code(code: str):
    """Get a specific CTC category by code"""
    try:
        category = await storage.get_category_by_code(code)
        if not category:
            raise HTTPException(status_code=404, detail="CTC category not found")
        return to_schema(category, CTCCategoryRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving category: {str(e)}")


@router.post("/categories", response_model=CTCCategoryRead)
async def create_category(category_data: CTCCategoryCreate):
    """Create a new CTC category"""
    try:
        new_category = await storage.create_category(category_data.dict())
        return to_schema(new_category, CTCCategoryRead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating category: {str(e)}")


@router.put("/categories/{category_id}", response_model=CTCCategoryRead)
async def update_category(category_id: int, category_data: CTCCategoryUpdate):
    """Update an existing CTC category"""
    try:
        update_data = {k: v for k, v in category_data.dict().items() if v is not None}
        updated_category = await storage.update_category(category_id, update_data)
        if not updated_category:
            raise HTTPException(status_code=404, detail="CTC category not found")
        return to_schema(updated_category, CTCCategoryRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating category: {str(e)}")


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, soft_delete: bool = Query(True, description="Soft delete by default")):
    """Delete a CTC category"""
    try:
        success = await storage.delete_category(category_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="CTC category not found")
        return {"message": "CTC category deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting category: {str(e)}")


# ==================== CTC Attributes ====================

@router.get("/categories/{category_id}/attributes", response_model=List[CTCAttributeRead])
async def get_attributes_by_category(category_id: int, active_only: bool = Query(True, description="Only return active attributes")):
    """Get all attributes for a specific category"""
    try:
        attributes = await storage.get_attributes_by_category(category_id, active_only=active_only)
        return [to_schema(attr, CTCAttributeRead) for attr in attributes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attributes: {str(e)}")


@router.get("/attributes/{attribute_id}", response_model=CTCAttributeRead)
async def get_attribute_by_id(attribute_id: int):
    """Get a specific CTC attribute by ID"""
    try:
        attribute = await storage.get_attribute_by_id(attribute_id)
        if not attribute:
            raise HTTPException(status_code=404, detail="CTC attribute not found")
        return to_schema(attribute, CTCAttributeRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attribute: {str(e)}")


@router.get("/attributes/uuid/{attribute_uuid}", response_model=CTCAttributeRead)
async def get_attribute_by_uuid(attribute_uuid: str):
    """Get a specific CTC attribute by UUID"""
    try:
        attribute = await storage.get_attribute_by_uuid(attribute_uuid)
        if not attribute:
            raise HTTPException(status_code=404, detail="CTC attribute not found")
        return to_schema(attribute, CTCAttributeRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attribute: {str(e)}")


@router.post("/attributes", response_model=CTCAttributeRead)
async def create_attribute(attribute_data: CTCAttributeCreate):
    """Create a new CTC attribute"""
    try:
        new_attribute = await storage.create_attribute(attribute_data.dict())
        return to_schema(new_attribute, CTCAttributeRead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating attribute: {str(e)}")


@router.put("/attributes/{attribute_id}", response_model=CTCAttributeRead)
async def update_attribute(attribute_id: int, attribute_data: CTCAttributeUpdate):
    """Update an existing CTC attribute"""
    try:
        update_data = {k: v for k, v in attribute_data.dict().items() if v is not None}
        updated_attribute = await storage.update_attribute(attribute_id, update_data)
        if not updated_attribute:
            raise HTTPException(status_code=404, detail="CTC attribute not found")
        return to_schema(updated_attribute, CTCAttributeRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating attribute: {str(e)}")


@router.delete("/attributes/{attribute_id}")
async def delete_attribute(attribute_id: int, soft_delete: bool = Query(True, description="Soft delete by default")):
    """Delete a CTC attribute"""
    try:
        success = await storage.delete_attribute(attribute_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="CTC attribute not found")
        return {"message": "CTC attribute deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting attribute: {str(e)}")


# ==================== CTC Attribute Groups ====================

@router.get("/attribute-groups", response_model=List[CTCAttributeGroupRead])
async def get_all_attribute_groups(active_only: bool = Query(True, description="Only return active attribute groups")):
    """Get all attribute groups"""
    try:
        groups = await storage.get_all_attribute_groups(active_only=active_only)
        return [to_schema(group, CTCAttributeGroupRead) for group in groups]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attribute groups: {str(e)}")


@router.get("/attribute-groups/{group_id}", response_model=CTCAttributeGroupRead)
async def get_attribute_group_by_id(group_id: int):
    """Get a specific attribute group by ID"""
    try:
        group = await storage.get_attribute_group_by_id(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Attribute group not found")
        return to_schema(group, CTCAttributeGroupRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attribute group: {str(e)}")


@router.post("/attribute-groups", response_model=CTCAttributeGroupRead)
async def create_attribute_group(group_data: CTCAttributeGroupCreate):
    """Create a new attribute group"""
    try:
        new_group = await storage.create_attribute_group(group_data.dict())
        return to_schema(new_group, CTCAttributeGroupRead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating attribute group: {str(e)}")


# ==================== CTC Data Types ====================

@router.get("/data-types", response_model=List[CTCDataTypeRead])
async def get_all_data_types(active_only: bool = Query(True, description="Only return active data types")):
    """Get all data types"""
    try:
        data_types = await storage.get_all_data_types(active_only=active_only)
        return [to_schema(dt, CTCDataTypeRead) for dt in data_types]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data types: {str(e)}")


@router.get("/data-types/{data_type_id}", response_model=CTCDataTypeRead)
async def get_data_type_by_id(data_type_id: int):
    """Get a specific data type by ID"""
    try:
        data_type = await storage.get_data_type_by_id(data_type_id)
        if not data_type:
            raise HTTPException(status_code=404, detail="Data type not found")
        return to_schema(data_type, CTCDataTypeRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data type: {str(e)}")


@router.post("/data-types", response_model=CTCDataTypeRead)
async def create_data_type(data_type_data: CTCDataTypeCreate):
    """Create a new data type"""
    try:
        new_data_type = await storage.create_data_type(data_type_data.dict())
        return to_schema(new_data_type, CTCDataTypeRead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating data type: {str(e)}")


# ==================== CTC Units of Measure ====================

@router.get("/units-of-measure", response_model=List[CTCUnitOfMeasureRead])
async def get_all_units_of_measure(active_only: bool = Query(True, description="Only return active units of measure")):
    """Get all units of measure"""
    try:
        uoms = await storage.get_all_units_of_measure(active_only=active_only)
        return [to_schema(uom, CTCUnitOfMeasureRead) for uom in uoms]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving units of measure: {str(e)}")


@router.get("/units-of-measure/{uom_id}", response_model=CTCUnitOfMeasureRead)
async def get_unit_of_measure_by_id(uom_id: int):
    """Get a specific unit of measure by ID"""
    try:
        uom = await storage.get_unit_of_measure_by_id(uom_id)
        if not uom:
            raise HTTPException(status_code=404, detail="Unit of measure not found")
        return to_schema(uom, CTCUnitOfMeasureRead)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving unit of measure: {str(e)}")


@router.post("/units-of-measure", response_model=CTCUnitOfMeasureRead)
async def create_unit_of_measure(uom_data: CTCUnitOfMeasureCreate):
    """Create a new unit of measure"""
    try:
        new_uom = await storage.create_unit_of_measure(uom_data.dict())
        return to_schema(new_uom, CTCUnitOfMeasureRead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating unit of measure: {str(e)}")


# ==================== Advanced Queries ====================

@router.get("/hierarchy", response_model=List[CTCClassHierarchy])
async def get_full_hierarchy(class_id: Optional[int] = Query(None, description="Optional class ID to get specific hierarchy")):
    """Get the full CTC hierarchy with all levels"""
    try:
        hierarchy = await storage.get_full_hierarchy(class_id=class_id)
        return hierarchy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving hierarchy: {str(e)}")


@router.get("/search", response_model=List[CTCSearchResult])
async def search_ctc(
    search_term: str = Query(..., description="Search term to look for"),
    level: Optional[int] = Query(None, description="Optional level filter (1=class, 2=type, 3=category)")
):
    """Search CTC data across all levels"""
    try:
        results = await storage.search_ctc(search_term, level=level)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching CTC data: {str(e)}")


@router.get("/categories/{category_id}/with-attributes", response_model=CTCCategoryWithAttributes)
async def get_category_with_attributes(category_id: int):
    """Get a category with all its attributes and related data"""
    try:
        category_data = await storage.get_category_with_attributes(category_id)
        if not category_data:
            raise HTTPException(status_code=404, detail="CTC category not found")
        return category_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving category with attributes: {str(e)}")


@router.get("/statistics", response_model=CTCStatistics)
async def get_statistics():
    """Get CTC statistics"""
    try:
        stats = await storage.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


# ==================== Product-Category Relationships ====================

@router.post("/categories/{category_id}/products/{product_id}")
async def assign_product_to_category(category_id: int, product_id: int):
    """Assign a product to a category"""
    try:
        success = await storage.assign_product_to_category(category_id, product_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category or product not found")
        return {"message": "Product assigned to category successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning product to category: {str(e)}")


@router.delete("/categories/{category_id}/products")
async def remove_product_from_category(category_id: int):
    """Remove product assignment from a category"""
    try:
        success = await storage.remove_product_from_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"message": "Product removed from category successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing product from category: {str(e)}")


@router.get("/categories/{category_id}/products")
async def get_products_by_category(category_id: int):
    """Get all products assigned to a category"""
    try:
        products = await storage.get_products_by_category(category_id)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving products for category: {str(e)}")


@router.get("/products/{product_id}/categories")
async def get_categories_by_product(product_id: int):
    """Get all categories assigned to a product"""
    try:
        categories = await storage.get_categories_by_product(product_id)
        return [to_schema(cat, CTCCategoryRead) for cat in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories for product: {str(e)}")


# ==================== Consolidated Hierarchy Endpoint ====================

@router.get("/hierarchy/consolidated", response_model=ConsolidatedHierarchyResponse)
async def get_consolidated_hierarchy(
    class_uuid: Optional[str] = Query(None, description="Class UUID to get types for"),
    type_uuid: Optional[str] = Query(None, description="Type UUID to get categories for"),
    active_only: bool = Query(True, description="Only return active items")
):
    """
    Consolidated endpoint to get CTC hierarchy data.
    
    - If no parameters: returns all classes
    - If class_uuid provided: returns all types for that class
    - If type_uuid provided: returns all categories for that type
    """
    try:
        if type_uuid is not None:
            # Get categories for a specific type
            categories = await storage.get_categories_by_type_uuid(type_uuid, active_only=active_only)
            return ConsolidatedHierarchyResponse(
                level="categories",
                parent_type_uuid=type_uuid,
                data=[to_schema(cat, CTCCategoryRead) for cat in categories]
            )
        elif class_uuid is not None:
            # Get types for a specific class
            types = await storage.get_types_by_class_uuid(class_uuid, active_only=active_only)
            return ConsolidatedHierarchyResponse(
                level="types", 
                parent_class_uuid=class_uuid,
                data=[to_schema(type_obj, CTCTypeRead) for type_obj in types]
            )
        else:
            # Get all classes
            classes = await storage.get_all_classes(active_only=active_only)
            return ConsolidatedHierarchyResponse(
                level="classes",
                data=[to_schema(cls, CTCClassRead) for cls in classes]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving hierarchy data: {str(e)}")


# ==================== CTC Link-Types Endpoints ====================

@router.get("/type-links", response_model=CTCTypeLinksResponse)
async def get_type_links(
    source_type_id: Optional[int] = Query(None, description="Filter by source type ID"),
    target_type_id: Optional[int] = Query(None, description="Filter by target type ID"),
    active_only: bool = Query(True, description="Only return active links"),
    limit: int = Query(100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """Get CTC type links with optional filtering"""
    try:
        links = await storage.get_type_links(
            source_type_id=source_type_id,
            target_type_id=target_type_id,
            active_only=active_only
        )
        
        # Apply pagination
        total = len(links)
        paginated_links = links[offset:offset + limit]
        
        return CTCTypeLinksResponse(
            success=True,
            data=[to_schema(link, CTCTypeLinkRead) for link in paginated_links],
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type links: {str(e)}")


@router.get("/type-links/{link_id}", response_model=CTCTypeLinkResponse)
async def get_type_link_by_id(link_id: int):
    """Get a specific CTC type link by ID"""
    try:
        link = await storage.get_type_link_by_id(link_id)
        if not link:
            raise HTTPException(status_code=404, detail="CTC type link not found")
        return CTCTypeLinkResponse(
            success=True,
            data=to_schema(link, CTCTypeLinkRead)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type link: {str(e)}")


@router.get("/type-links/uuid/{link_uuid}", response_model=CTCTypeLinkResponse)
async def get_type_link_by_uuid(link_uuid: str):
    """Get a specific CTC type link by UUID"""
    try:
        link = await storage.get_type_link_by_uuid(link_uuid)
        if not link:
            raise HTTPException(status_code=404, detail="CTC type link not found")
        return CTCTypeLinkResponse(
            success=True,
            data=to_schema(link, CTCTypeLinkRead)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type link: {str(e)}")


@router.post("/type-links", response_model=CTCTypeLinkResponse)
async def create_type_link(link_data: CTCTypeLinkCreate):
    """Create a new CTC type link"""
    try:
        new_link = await storage.create_type_link(link_data.dict())
        return CTCTypeLinkResponse(
            success=True,
            data=to_schema(new_link, CTCTypeLinkRead)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating type link: {str(e)}")


@router.put("/type-links/{link_id}", response_model=CTCTypeLinkResponse)
async def update_type_link(link_id: int, link_data: CTCTypeLinkCreate):
    """Update an existing CTC type link"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in link_data.dict().items() if v is not None}
        updated_link = await storage.update_type_link(link_id, update_data)
        if not updated_link:
            raise HTTPException(status_code=404, detail="CTC type link not found")
        return CTCTypeLinkResponse(
            success=True,
            data=to_schema(updated_link, CTCTypeLinkRead)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating type link: {str(e)}")


@router.delete("/type-links/{link_id}")
async def delete_type_link(link_id: int, soft_delete: bool = Query(True, description="Soft delete by default")):
    """Delete a CTC type link"""
    try:
        deleted = await storage.delete_type_link(link_id, soft_delete=soft_delete)
        if not deleted:
            raise HTTPException(status_code=404, detail="CTC type link not found")
        return {"success": True, "message": "Type link deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting type link: {str(e)}")


@router.get("/type-options", response_model=CTCTypeOptionsResponse)
async def get_type_options(
    source_type_id: Optional[int] = Query(None, description="Filter by source type ID"),
    option_type_id: Optional[int] = Query(None, description="Filter by option type ID"),
    active_only: bool = Query(True, description="Only return active options"),
    limit: int = Query(100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """Get CTC type options with optional filtering"""
    try:
        options = await storage.get_type_options(
            source_type_id=source_type_id,
            option_type_id=option_type_id,
            active_only=active_only
        )
        
        # Apply pagination
        total = len(options)
        paginated_options = options[offset:offset + limit]
        
        return CTCTypeOptionsResponse(
            success=True,
            data=[to_schema(option, CTCTypeOptionRead) for option in paginated_options],
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type options: {str(e)}")


@router.get("/type-options/{option_id}", response_model=CTCTypeOptionResponse)
async def get_type_option_by_id(option_id: int):
    """Get a specific CTC type option by ID"""
    try:
        option = await storage.get_type_option_by_id(option_id)
        if not option:
            raise HTTPException(status_code=404, detail="CTC type option not found")
        return CTCTypeOptionResponse(
            success=True,
            data=to_schema(option, CTCTypeOptionRead)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type option: {str(e)}")


@router.get("/type-options/uuid/{option_uuid}", response_model=CTCTypeOptionResponse)
async def get_type_option_by_uuid(option_uuid: str):
    """Get a specific CTC type option by UUID"""
    try:
        option = await storage.get_type_option_by_uuid(option_uuid)
        if not option:
            raise HTTPException(status_code=404, detail="CTC type option not found")
        return CTCTypeOptionResponse(
            success=True,
            data=to_schema(option, CTCTypeOptionRead)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type option: {str(e)}")


@router.post("/type-options", response_model=CTCTypeOptionResponse)
async def create_type_option(option_data: CTCTypeOptionCreate):
    """Create a new CTC type option"""
    try:
        new_option = await storage.create_type_option(option_data.dict())
        return CTCTypeOptionResponse(
            success=True,
            data=to_schema(new_option, CTCTypeOptionRead)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating type option: {str(e)}")


@router.put("/type-options/{option_id}", response_model=CTCTypeOptionResponse)
async def update_type_option(option_id: int, option_data: CTCTypeOptionCreate):
    """Update an existing CTC type option"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in option_data.dict().items() if v is not None}
        updated_option = await storage.update_type_option(option_id, update_data)
        if not updated_option:
            raise HTTPException(status_code=404, detail="CTC type option not found")
        return CTCTypeOptionResponse(
            success=True,
            data=to_schema(updated_option, CTCTypeOptionRead)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating type option: {str(e)}")


@router.delete("/type-options/{option_id}")
async def delete_type_option(option_id: int, soft_delete: bool = Query(True, description="Soft delete by default")):
    """Delete a CTC type option"""
    try:
        deleted = await storage.delete_type_option(option_id, soft_delete=soft_delete)
        if not deleted:
            raise HTTPException(status_code=404, detail="CTC type option not found")
        return {"success": True, "message": "Type option deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting type option: {str(e)}")


@router.get("/type-links/statistics", response_model=CTCTypeLinkStatistics)
async def get_type_link_statistics():
    """Get statistics for CTC type links"""
    try:
        stats = await storage.get_type_link_statistics()
        return CTCTypeLinkStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type link statistics: {str(e)}")


@router.get("/type-options/statistics", response_model=CTCTypeOptionStatistics)
async def get_type_option_statistics():
    """Get statistics for CTC type options"""
    try:
        stats = await storage.get_type_option_statistics()
        return CTCTypeOptionStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving type option statistics: {str(e)}") 