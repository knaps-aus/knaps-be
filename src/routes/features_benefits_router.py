from fastapi import APIRouter, HTTPException
from typing import List
from ..storage import storage
from ..models import (
    ClassFeaturesBenefitsRead, ClassFeaturesBenefitsCreate, ClassFeaturesBenefitsUpdate,
    TypeFeaturesBenefitsRead, TypeFeaturesBenefitsCreate, TypeFeaturesBenefitsUpdate,
    CategoryFeaturesBenefitsRead, CategoryFeaturesBenefitsCreate, CategoryFeaturesBenefitsUpdate,
    CategoryAttributeRead, CategoryAttributeCreate, CategoryAttributeUpdate
)

router = APIRouter(prefix="/ctc/features-benefits", tags=["CTC Features & Benefits"])

# --- Class Level ---
@router.get("/class/{class_id}", response_model=List[ClassFeaturesBenefitsRead])
async def get_class_features_benefits(class_id: int):
    return await storage.get_class_features_benefits(class_id)

@router.post("/class", response_model=ClassFeaturesBenefitsRead)
async def create_class_features_benefit(data: ClassFeaturesBenefitsCreate):
    return await storage.create_class_features_benefit(data)

@router.put("/class/{fb_id}", response_model=ClassFeaturesBenefitsRead)
async def update_class_features_benefit(fb_id: int, data: ClassFeaturesBenefitsUpdate):
    updated = await storage.update_class_features_benefit(fb_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Feature/Benefit not found")
    return updated

@router.delete("/class/{fb_id}")
async def delete_class_features_benefit(fb_id: int):
    success = await storage.delete_class_features_benefit(fb_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feature/Benefit not found")
    return {"message": "Deleted successfully"}

# --- Type Level ---
@router.get("/type/{type_id}", response_model=List[TypeFeaturesBenefitsRead])
async def get_type_features_benefits(type_id: int):
    return await storage.get_type_features_benefits(type_id)

@router.post("/type", response_model=TypeFeaturesBenefitsRead)
async def create_type_features_benefit(data: TypeFeaturesBenefitsCreate):
    return await storage.create_type_features_benefit(data)

@router.put("/type/{fb_id}", response_model=TypeFeaturesBenefitsRead)
async def update_type_features_benefit(fb_id: int, data: TypeFeaturesBenefitsUpdate):
    updated = await storage.update_type_features_benefit(fb_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Feature/Benefit not found")
    return updated

@router.delete("/type/{fb_id}")
async def delete_type_features_benefit(fb_id: int):
    success = await storage.delete_type_features_benefit(fb_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feature/Benefit not found")
    return {"message": "Deleted successfully"}

# --- Category Level ---
@router.get("/category/{category_id}", response_model=List[CategoryFeaturesBenefitsRead])
async def get_category_features_benefits(category_id: int):
    return await storage.get_category_features_benefits(category_id)

@router.post("/category", response_model=CategoryFeaturesBenefitsRead)
async def create_category_features_benefit(data: CategoryFeaturesBenefitsCreate):
    return await storage.create_category_features_benefit(data)

@router.put("/category/{fb_id}", response_model=CategoryFeaturesBenefitsRead)
async def update_category_features_benefit(fb_id: int, data: CategoryFeaturesBenefitsUpdate):
    updated = await storage.update_category_features_benefit(fb_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Feature/Benefit not found")
    return updated

@router.delete("/category/{fb_id}")
async def delete_category_features_benefit(fb_id: int):
    success = await storage.delete_category_features_benefit(fb_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feature/Benefit not found")
    return {"message": "Deleted successfully"}

# --- Category Attribute CRUD ---
# Category Attribute Endpoints
@router.get("/category/{category_id}/attributes", response_model=List[CategoryAttributeRead])
async def get_category_attributes(category_id: int):
    return await storage.get_category_attributes(category_id)

@router.post("/category/attribute", response_model=CategoryAttributeRead)
async def create_category_attribute(data: CategoryAttributeCreate):
    return await storage.create_category_attribute(data)

@router.put("/category/attribute/{attr_id}", response_model=CategoryAttributeRead)
async def update_category_attribute(attr_id: int, data: CategoryAttributeUpdate):
    updated = await storage.update_category_attribute(attr_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Category Attribute not found")
    return updated

@router.delete("/category/attribute/{attr_id}")
async def delete_category_attribute(attr_id: int):
    success = await storage.delete_category_attribute(attr_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category Attribute not found")
    return {"message": "Deleted successfully"}
