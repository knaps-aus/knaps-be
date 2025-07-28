import asyncio
from typing import List, Optional, Literal, Dict, Any, Union, Tuple, get_args, get_origin
from sqlalchemy import select, text, and_, or_, func, desc, asc
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime
from .database import get_async_session
from .db_models import (
    ProductModel, User, PriceLevel as PriceLevelModel, MyPrice as MyPriceModel, RebateAgreement, RebateAgreementProduct, 
    RebateTier, RebateClaim,
    # New CTC models
    CTCClass, CTCType, CTCCategory, CTCAttributeGroup, CTCDataType, 
    CTCUnitOfMeasure, CTCAttribute, CategoryAttribute,
    # Distributor and Brand models
    Distributor, Brand,
    # Features and Benefits models
    ClassFeaturesBenefits, TypeFeaturesBenefits, CategoryFeaturesBenefits,
    PriceLevelType, DealSource, DealType,
    # Additional Models For Brand / Distributor 
    Purchaser, Contact, Address,
    # CTC Link-Types models
    CTCTypeLink, CTCTypeOption,
    # NEW DEAL MODELS
    DealValueType, DealCalculation
)
from .models import (
    Product,
    InsertProduct,
    ProductAnalytics,
    OverallAnalytics,
    RebateAgreementCreate,
    RebateAgreementRead,
    RebateTierCreate,
    DistributorCreate,
    DistributorRead,
    DistributorUpdate,
    BrandCreate,
    BrandRead,
    BrandUpdate,
    ProductCreateResult,
    FuzzyMatchInfo,
    BulkProductCreateResult,
    # Pricing models
    PriceLevel,
    InsertPriceLevel,
    MyPrice,
    # Features and Benefits models
    ClassFeaturesBenefitsCreate,
    ClassFeaturesBenefitsRead,
    ClassFeaturesBenefitsUpdate,
    TypeFeaturesBenefitsCreate,
    TypeFeaturesBenefitsRead,
    TypeFeaturesBenefitsUpdate,
    CategoryFeaturesBenefitsCreate,
    CategoryFeaturesBenefitsRead,
    CategoryFeaturesBenefitsUpdate,
    PriceLevelTypeCreate,
    PriceLevelTypeRead,
    PriceLevelTypeUpdate,
    DealSourceRead,
    DealSourceCreate,
    DealSourceUpdate,
    DealTypeRead,
    DealTypeCreate,
    DealTypeUpdate,
    # New models
    PurchaserRead,
    PurchaserCreate,
    PurchaserUpdate,
    ContactRead,
    ContactCreate,
    ContactUpdate,
    AddressRead,
    AddressCreate,
    AddressUpdate,
    # CTC Link-Types models
    CTCTypeLinkCreate,
    CTCTypeLinkRead,
    CTCTypeOptionCreate,
    CTCTypeOptionRead,
    CTCTypeLinkQuery,
    CTCTypeOptionQuery,
    CTCTypeLinkResponse,
    CTCTypeLinksResponse,
    CTCTypeOptionResponse,
    CTCTypeOptionsResponse,
    CTCTypeLinkStatistics,
    CTCTypeOptionStatistics,
    # NEW DEAL MODELS
    DealValueTypeCreate,
    DealValueTypeRead,
    DealValueTypeUpdate,
    DealCalculationCreate,
    DealCalculationRead,
    DealCalculationUpdate
)
import logging 
import uuid
import json
import pandas as pd
from decimal import Decimal
from difflib import SequenceMatcher
import re
from datetime import datetime, timedelta


logger = logging.getLogger('uvicorn.error')


def convert_product_model(query):
    output = query.all()
    return [to_schema(i, Product) for i in output]



def to_schema(obj, schema):
    """Convert SQLAlchemy object to Pydantic schema using built-in model_validate"""
    if obj is None:
        return None
    return schema.model_validate(obj, from_attributes=True)

def normalize_name(name: str) -> str:
    """Normalize a name for comparison by removing extra spaces and converting to lowercase"""
    if not name:
        return ""
    # Remove extra whitespace and convert to lowercase
    return re.sub(r'\s+', ' ', name.strip().lower())


def calculate_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names using SequenceMatcher"""
    if not name1 or not name2:
        return 0.0
    
    # Normalize both names
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    # Use SequenceMatcher for similarity calculation
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_best_match(input_name: str, candidates: List[Tuple[str, Any]], threshold: float = 0.8) -> Tuple[Optional[Any], float, List[str]]:
    """
    Find the best match for an input name among candidates.
    
    Args:
        input_name: The name to match
        candidates: List of tuples (name, object) to search through
        threshold: Minimum similarity score to consider a match (0.0 to 1.0)
    
    Returns:
        Tuple of (best_match_object, similarity_score, suggestions)
    """
    if not candidates:
        return None, 0.0, []
    
    # Calculate similarity for all candidates
    similarities = []
    for candidate_name, candidate_obj in candidates:
        similarity = calculate_similarity(input_name, candidate_name)
        similarities.append((similarity, candidate_name, candidate_obj))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[0], reverse=True)
    
    best_similarity, best_name, best_obj = similarities[0]
    
    # If best match is above threshold, return it
    if best_similarity >= threshold:
        # Generate suggestions (other close matches)
        suggestions = [name for sim, name, _ in similarities[1:4] if sim >= 0.6]
        return best_obj, best_similarity, suggestions
    
    # If no good match, return suggestions
    suggestions = [name for sim, name, _ in similarities[:3] if sim >= 0.3]
    return None, best_similarity, suggestions





class SQLStorage:
    # Product operations
    async def get_products(self) -> List[Product]:
        async with get_async_session() as session:
            result = await session.execute(select(ProductModel))
            return [to_schema(row, Product) for row in result.scalars().all()]

    async def get_product(self, pid: int) -> Optional[Product]:
        async with get_async_session() as session:
            result = await session.execute(
                select(ProductModel)
                .options(
                    selectinload(ProductModel.distributor).selectinload(Distributor.purchaser),
                    selectinload(ProductModel.distributor).selectinload(Distributor.default_contact)
                )
                .where(ProductModel.id == pid)
            )
            product = result.scalar_one_or_none()
            
            # TODO: Uncomment this when we have a way to handle the relationship fields
            # return to_schema(result, Product) if result else None 

            # Log the raw SQLAlchemy ORM object as a dict before to_schema
            if product:
                def safe_serialize(obj):
                    try:
                        return str(obj)
                    except Exception:
                        return None
                logger.info("Raw ORM row: " + json.dumps({k: safe_serialize(v) for k, v in product.__dict__.items() if not k.startswith('_')}, indent=2, default=str))
            product_obj = to_schema(product, Product) if product else None
            if product_obj:
                logger.info("Product JSON: " + json.dumps(product_obj.model_dump(), indent=2, default=str))
            return product_obj

    async def get_product_by_code(self, code: str) -> Optional[Product]:
        async with get_async_session() as session:
            stmt = (
                select(ProductModel)
                .options(
                    selectinload(ProductModel.price_levels),
                    selectinload(ProductModel.my_price),
                    selectinload(ProductModel.brand),
                    selectinload(ProductModel.distributor).selectinload(Distributor.purchaser),
                    selectinload(ProductModel.distributor).selectinload(Distributor.default_contact)
                )
                .where(ProductModel.product_code == code)
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                logger.info(f"Found product with ID: {row.id}")
                logger.info(f"Product UUID: {row.uuid}")
                logger.info(f"Product Code: {row.product_code}")
                return to_schema(row, Product)
            return None
    
    async def get_product_by_uuid(self, uuid: str) -> Optional[Product]:
        async with get_async_session() as session:
            stmt = (
                select(ProductModel)
                .options(
                    selectinload(ProductModel.distributor).selectinload(Distributor.purchaser),
                    selectinload(ProductModel.distributor).selectinload(Distributor.default_contact)
                )
                .where(ProductModel.uuid == uuid)
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, Product) if row else None

    async def search_products(self, query: str) -> List[Product]:
        q = f"%{query.lower()}%"
        logger.info(f"Printing query {q}")
        async with get_async_session() as session:
            stmt = (
                select(ProductModel)
                .options(
                    selectinload(ProductModel.price_levels),
                    selectinload(ProductModel.my_price),
                    selectinload(ProductModel.brand),
                    selectinload(ProductModel.distributor).selectinload(Distributor.purchaser),
                    selectinload(ProductModel.distributor).selectinload(Distributor.default_contact)
                )
                .where(
                    (ProductModel.product_name.ilike(q))
                    | (ProductModel.product_code.ilike(q))
                    | (ProductModel.brand_name.ilike(q))
                    | (ProductModel.category_name.ilike(q))
                )
            )
            result = await session.execute(stmt)
            return [to_schema(p, Product) for p in result.scalars().all()]

    async def get_products_by_core_range(
        self,
        distributor_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        core_groups: Optional[List[str]] = None,
        class_id: Optional[int] = None,
        type_id: Optional[int] = None,
        category_id: Optional[int] = None
    ) -> List[Product]:
        """
        Get products filtered by core range parameters.
        
        Args:
            distributor_id: Filter by distributor ID
            brand_id: Filter by brand ID
            core_groups: List of core group codes to filter by (e.g., ["A", "B", "C"])
            class_id: Filter by CTC class ID
            type_id: Filter by CTC type ID
            category_id: Filter by CTC category ID
            
        Returns:
            List of products matching the criteria
        """
        async with get_async_session() as session:
            # Start with base query
            stmt = (
                select(ProductModel)
                .options(
                    selectinload(ProductModel.price_levels),
                    selectinload(ProductModel.my_price),
                    selectinload(ProductModel.brand),
                    selectinload(ProductModel.distributor).selectinload(Distributor.purchaser),
                    selectinload(ProductModel.distributor).selectinload(Distributor.default_contact)
                )
            )
            
            # Build conditions
            conditions = []
            
            # Filter by distributor
            if distributor_id is not None:
                conditions.append(ProductModel.distributor_id == distributor_id)
            
            # Filter by brand
            if brand_id is not None:
                conditions.append(ProductModel.brand_id == brand_id)
            
            # Filter by core groups
            if core_groups and len(core_groups) > 0:
                conditions.append(ProductModel.core_group.in_(core_groups))
            else:
                # If no core_groups specified, default to A,B,C,D,E
                conditions.append(ProductModel.core_group.in_(['A', 'B', 'C', 'D', 'E']))
            
            # Filter by CTC hierarchy (class, type, category)
            if class_id is not None or type_id is not None or category_id is not None:
                # Join with CTC categories table
                stmt = stmt.join(CTCCategory, ProductModel.id == CTCCategory.product_id)
                
                if class_id is not None:
                    # Join with types and classes to filter by class
                    stmt = stmt.join(CTCType, CTCCategory.type_id == CTCType.id)
                    conditions.append(CTCType.class_id == class_id)
                
                if type_id is not None:
                    # If we haven't already joined with types, do it now
                    if class_id is None:
                        stmt = stmt.join(CTCType, CTCCategory.type_id == CTCType.id)
                    conditions.append(CTCCategory.type_id == type_id)
                
                if category_id is not None:
                    conditions.append(CTCCategory.id == category_id)
            
            # Apply conditions if any
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Execute query
            result = await session.execute(stmt)
            products = result.scalars().all()
            
            # Convert to Product models
            return [to_schema(p, Product) for p in products]

    async def get_brand_by_name(self, name: str) -> Optional[BrandRead]:
        """Find brand by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.name.ilike(name))
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_distributor_by_name(self, name: str) -> Optional[DistributorRead]:
        """Find distributor by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
                .where(Distributor.name.ilike(name))
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def find_brand_with_fuzzy_matching(self, brand_name: str, threshold: float = 0.8) -> Tuple[Optional[BrandRead], float, List[str]]:
        """
        Find brand using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (brand_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all brands
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
            
            # Convert to list of (name, brand_object) tuples
            candidates = [(brand.name, brand) for brand in brands]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(brand_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, BrandRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def find_distributor_with_fuzzy_matching(self, distributor_name: str, threshold: float = 0.8) -> Tuple[Optional[DistributorRead], float, List[str]]:
        """
        Find distributor using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (distributor_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all distributors
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
            )
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            
            # Convert to list of (name, distributor_object) tuples
            candidates = [(distributor.name, distributor) for distributor in distributors]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(distributor_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, DistributorRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def get_brand_by_name(self, name: str) -> Optional[BrandRead]:
        """Find brand by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.name.ilike(name))
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_distributor_by_name(self, name: str) -> Optional[DistributorRead]:
        """Find distributor by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
                .where(Distributor.name.ilike(name))
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def find_brand_with_fuzzy_matching(self, brand_name: str, threshold: float = 0.8) -> Tuple[Optional[BrandRead], float, List[str]]:
        """
        Find brand using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (brand_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all brands
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
            
            # Convert to list of (name, brand_object) tuples
            candidates = [(brand.name, brand) for brand in brands]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(brand_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, BrandRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def find_distributor_with_fuzzy_matching(self, distributor_name: str, threshold: float = 0.8) -> Tuple[Optional[DistributorRead], float, List[str]]:
        """
        Find distributor using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (distributor_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all distributors
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
            )
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            
            # Convert to list of (name, distributor_object) tuples
            candidates = [(distributor.name, distributor) for distributor in distributors]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(distributor_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, DistributorRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def create_product(self, data: InsertProduct) -> ProductCreateResult:
        fuzzy_matches = []
        async with get_async_session() as session:
            # Distributor matching
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
            )
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            distributor = None
            normalized_input = normalize_name(data.distributor_name)
            for d in distributors:
                if normalize_name(d.name) == normalized_input:
                    distributor = d
                    break
            if not distributor:
                # Fuzzy match
                candidates = [(d.name, d) for d in distributors]
                best, sim, _ = find_best_match(data.distributor_name, candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for distributor: '{data.distributor_name}' -> '{best.name}' (sim={sim:.2f})")
                    distributor = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='distributor',
                        input_value=data.distributor_name,
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    return ProductCreateResult(product=None, fuzzy_matches=[], error=f"Distributor '{data.distributor_name}' not found")

            # Brand matching
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
            brand = None
            normalized_input = normalize_name(data.brand_name)
            for b in brands:
                if normalize_name(b.name) == normalized_input:
                    brand = b
                    break
            if not brand:
                candidates = [(b.name, b) for b in brands]
                best, sim, _ = find_best_match(data.brand_name, candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for brand: '{data.brand_name}' -> '{best.name}' (sim={sim:.2f})")
                    brand = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='brand',
                        input_value=data.brand_name,
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    return ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{data.brand_name}' not found")

            # Verify brand belongs to distributor
            if brand.distributor_id != distributor.id:
                return ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{data.brand_name}' does not belong to distributor '{data.distributor_name}'")

            product_data = data.model_dump()
            price_levels_data = product_data.pop('price_levels', [])
            product_data['uuid'] = str(uuid.uuid4())
            product_data['distributor_id'] = distributor.id
            product_data['brand_id'] = brand.id
            product_data.pop('distributor_name', None)
            product_data.pop('brand_name', None)
            obj = ProductModel(**product_data)
            session.add(obj)
            await session.flush()
            for price_level_data in price_levels_data:
                price_level = PriceLevel(product_id=obj.id, **price_level_data)
                session.add(price_level)
            await session.commit()
            await session.refresh(obj)
            return ProductCreateResult(product=to_schema(obj, Product), fuzzy_matches=fuzzy_matches)

    async def update_product(self, pid: int, data: dict) -> Optional[Product]:
        async with get_async_session() as session:
            obj = await session.get(ProductModel, pid)
            if not obj:
                return None
            for k, v in data.items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, Product)

    async def delete_product(self, pid: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(ProductModel, pid)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # Price Level operations
    async def get_product_price_levels(self, product_id: int) -> List[PriceLevel]:
        async with get_async_session() as session:
            stmt = select(PriceLevelModel).where(PriceLevelModel.product_id == product_id)
            result = await session.execute(stmt)
            price_levels = result.scalars().all()
            return [to_schema(pl, PriceLevel) for pl in price_levels]

    async def get_price_level(self, price_id: int) -> Optional[PriceLevel]:
        async with get_async_session() as session:
            result = await session.get(PriceLevelModel, price_id)
            return to_schema(result, PriceLevel) if result else None

    async def create_price_level(self, product_id: int, data: InsertPriceLevel) -> PriceLevel:
        """Create a new price level for a product"""
        async with get_async_session() as session:
            # Verify product exists
            product = await session.get(ProductModel, product_id)
            if not product:
                raise ValueError(f"Product with ID {product_id} not found")
            
            price_data = data.model_dump()
            price_data['product_id'] = product_id
            # Remove fields that don't exist in the database model
            price_data.pop('uuid', None)  # PriceLevel doesn't have uuid field
            price_data.pop('created_at', None)  # Let SQLAlchemy handle this
            price_data.pop('updated_at', None)  # Let SQLAlchemy handle this
            
            obj = PriceLevelModel(**price_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, PriceLevel)

    async def update_price_level(self, price_id: int, data: dict) -> Optional[PriceLevel]:
        """Update a specific price level"""
        async with get_async_session() as session:
            obj = await session.get(PriceLevelModel, price_id)
            if not obj:
                return None
            
            # Update only provided fields
            for k, v in data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            
            # Let SQLAlchemy handle the updated_at field automatically
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, PriceLevel)

    async def delete_price_level(self, price_id: int) -> bool:
        """Delete a specific price level"""
        async with get_async_session() as session:
            obj = await session.get(PriceLevelModel, price_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # MyPrice operations
    async def get_product_my_price(self, product_id: int) -> Optional[MyPrice]:
        """Get MyPrice for a product"""
        async with get_async_session() as session:
            stmt = select(MyPriceModel).where(MyPriceModel.product_id == product_id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            return to_schema(obj, MyPrice) if obj else None

    async def create_or_update_my_price(self, product_id: int, data: dict) -> MyPrice:
        """Create or update MyPrice for a product"""
        async with get_async_session() as session:
            # Verify product exists
            product = await session.get(ProductModel, product_id)
            if not product:
                raise ValueError(f"Product with ID {product_id} not found")
            
            # Check if MyPrice already exists
            stmt = select(MyPriceModel).where(MyPriceModel.product_id == product_id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            
            if obj:
                # Update existing MyPrice
                for k, v in data.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
                # Let SQLAlchemy handle the modified_at field automatically
            else:
                # Create new MyPrice
                price_data = data.copy()
                price_data['product_id'] = product_id
                # Remove fields that don't exist in the database model
                price_data.pop('uuid', None)  # MyPrice has uuid but let SQLAlchemy handle it
                price_data.pop('created_at', None)  # Let SQLAlchemy handle this
                price_data.pop('modified_at', None)  # Let SQLAlchemy handle this
                
                obj = MyPriceModel(**price_data)
                session.add(obj)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, MyPrice)

    async def delete_my_price(self, product_id: int) -> bool:
        """Delete MyPrice for a product"""
        async with get_async_session() as session:
            stmt = select(MyPriceModel).where(MyPriceModel.product_id == product_id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True


    # Distributor operations
    async def get_distributors(self) -> List[DistributorRead]:
        async with get_async_session() as session:
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
            )
            result = await session.execute(stmt)
            return [to_schema(row, DistributorRead) for row in result.scalars().all()]

    async def get_distributor(self, distributor_id: int) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            result = await session.execute(
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
                .where(Distributor.id == distributor_id)
            )
            distributor = result.scalar_one_or_none()
            return to_schema(distributor, DistributorRead) if distributor else None

    async def get_distributor_by_uuid(self, uuid: str) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
                .where(Distributor.uuid == uuid)
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def get_distributor_by_code(self, code: str) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
                .where(Distributor.code == code)
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def create_distributor(self, data: DistributorCreate) -> DistributorRead:
        async with get_async_session() as session:
            distributor_data = data.model_dump()
            distributor_data['uuid'] = str(uuid.uuid4())
            distributor_data['modified'] = datetime.utcnow()
            distributor_data['created'] = datetime.utcnow()
            
            obj = Distributor(**distributor_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, DistributorRead)

    async def update_distributor(self, distributor_id: int, data: DistributorUpdate) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            obj = await session.get(Distributor, distributor_id)
            if not obj:
                return None
            
            update_data = data.model_dump(exclude_unset=True)
            update_data['modified'] = datetime.utcnow()
            
            for k, v in update_data.items():
                setattr(obj, k, v)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, DistributorRead)

    async def delete_distributor(self, distributor_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(Distributor, distributor_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    async def search_distributors(self, query: str) -> List[DistributorRead]:
        """Search distributors by name, code, or store"""
        q = f"%{query.lower()}%"
        async with get_async_session() as session:
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
                .where(
                    (Distributor.name.ilike(q))
                    | (Distributor.code.ilike(q))
                    | (Distributor.store.ilike(q))
                )
            )
            result = await session.execute(stmt)
            return [to_schema(row, DistributorRead) for row in result.scalars().all()]

    # Purchaser operations
    async def get_purchasers(self) -> List[PurchaserRead]:
        async with get_async_session() as session:
            result = await session.execute(select(Purchaser))
            return [to_schema(row, PurchaserRead) for row in result.scalars().all()]

    async def get_purchaser(self, purchaser_id: int) -> Optional[PurchaserRead]:
        async with get_async_session() as session:
            result = await session.get(Purchaser, purchaser_id)
            return to_schema(result, PurchaserRead) if result else None

    async def get_purchaser_by_uuid(self, uuid: str) -> Optional[PurchaserRead]:
        async with get_async_session() as session:
            stmt = select(Purchaser).where(Purchaser.uuid == uuid)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, PurchaserRead) if row else None

    async def get_purchaser_by_code(self, code: str) -> Optional[PurchaserRead]:
        async with get_async_session() as session:
            stmt = select(Purchaser).where(Purchaser.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, PurchaserRead) if row else None

    async def create_purchaser(self, data: PurchaserCreate) -> PurchaserRead:
        async with get_async_session() as session:
            purchaser_data = data.model_dump()
            purchaser_data['uuid'] = str(uuid.uuid4())
            purchaser_data['modified'] = datetime.utcnow()
            purchaser_data['created'] = datetime.utcnow()
            
            obj = Purchaser(**purchaser_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, PurchaserRead)

    async def update_purchaser(self, purchaser_id: int, data: PurchaserUpdate) -> Optional[PurchaserRead]:
        async with get_async_session() as session:
            obj = await session.get(Purchaser, purchaser_id)
            if not obj:
                return None
            
            update_data = data.model_dump(exclude_unset=True)
            update_data['modified'] = datetime.utcnow()
            
            for k, v in update_data.items():
                setattr(obj, k, v)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, PurchaserRead)

    async def delete_purchaser(self, purchaser_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(Purchaser, purchaser_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # Contact operations
    async def get_contacts(self) -> List[ContactRead]:
        async with get_async_session() as session:
            result = await session.execute(select(Contact))
            return [to_schema(row, ContactRead) for row in result.scalars().all()]

    async def get_contact(self, contact_id: int) -> Optional[ContactRead]:
        async with get_async_session() as session:
            result = await session.get(Contact, contact_id)
            return to_schema(result, ContactRead) if result else None

    async def get_contact_by_uuid(self, uuid: str) -> Optional[ContactRead]:
        async with get_async_session() as session:
            stmt = select(Contact).where(Contact.uuid == uuid)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, ContactRead) if row else None

    async def get_contact_by_code(self, code: str) -> Optional[ContactRead]:
        async with get_async_session() as session:
            stmt = select(Contact).where(Contact.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, ContactRead) if row else None

    async def get_contacts_by_distributor(self, distributor_id: int) -> List[ContactRead]:
        async with get_async_session() as session:
            stmt = select(Contact).where(Contact.distributor_id == distributor_id)
            result = await session.execute(stmt)
            return [to_schema(row, ContactRead) for row in result.scalars().all()]

    async def create_contact(self, data: ContactCreate) -> ContactRead:
        async with get_async_session() as session:
            contact_data = data.model_dump()
            contact_data['uuid'] = str(uuid.uuid4())
            contact_data['modified'] = datetime.utcnow()
            contact_data['created'] = datetime.utcnow()
            
            obj = Contact(**contact_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, ContactRead)

    async def update_contact(self, contact_id: int, data: ContactUpdate) -> Optional[ContactRead]:
        async with get_async_session() as session:
            obj = await session.get(Contact, contact_id)
            if not obj:
                return None
            
            update_data = data.model_dump(exclude_unset=True)
            update_data['modified'] = datetime.utcnow()
            
            for k, v in update_data.items():
                setattr(obj, k, v)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, ContactRead)

    async def delete_contact(self, contact_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(Contact, contact_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # Address operations
    async def get_addresses(self) -> List[AddressRead]:
        async with get_async_session() as session:
            result = await session.execute(select(Address))
            return [to_schema(row, AddressRead) for row in result.scalars().all()]

    async def get_address(self, address_id: int) -> Optional[AddressRead]:
        async with get_async_session() as session:
            result = await session.get(Address, address_id)
            return to_schema(result, AddressRead) if result else None

    async def get_address_by_uuid(self, uuid: str) -> Optional[AddressRead]:
        async with get_async_session() as session:
            stmt = select(Address).where(Address.uuid == uuid)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, AddressRead) if row else None

    async def get_address_by_code(self, code: str) -> Optional[AddressRead]:
        async with get_async_session() as session:
            stmt = select(Address).where(Address.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, AddressRead) if row else None

    async def get_addresses_by_distributor(self, distributor_id: int) -> List[AddressRead]:
        async with get_async_session() as session:
            stmt = select(Address).where(Address.distributor_id == distributor_id)
            result = await session.execute(stmt)
            return [to_schema(row, AddressRead) for row in result.scalars().all()]

    async def get_addresses_by_contact(self, contact_id: int) -> List[AddressRead]:
        async with get_async_session() as session:
            stmt = select(Address).where(Address.contact_id == contact_id)
            result = await session.execute(stmt)
            return [to_schema(row, AddressRead) for row in result.scalars().all()]

    async def create_address(self, data: AddressCreate) -> AddressRead:
        async with get_async_session() as session:
            address_data = data.model_dump()
            address_data['uuid'] = str(uuid.uuid4())
            address_data['modified'] = datetime.utcnow()
            address_data['created'] = datetime.utcnow()
            
            obj = Address(**address_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, AddressRead)

    async def update_address(self, address_id: int, data: AddressUpdate) -> Optional[AddressRead]:
        async with get_async_session() as session:
            obj = await session.get(Address, address_id)
            if not obj:
                return None
            
            update_data = data.model_dump(exclude_unset=True)
            update_data['modified'] = datetime.utcnow()
            
            for k, v in update_data.items():
                setattr(obj, k, v)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, AddressRead)

    async def delete_address(self, address_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(Address, address_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # Brand operations
    async def get_brands(self) -> List[BrandRead]:
        async with get_async_session() as session:
            result = await session.execute(select(Brand))
            return [to_schema(row, BrandRead) for row in result.scalars().all()]

    async def get_brand(self, brand_id: int) -> Optional[BrandRead]:
        async with get_async_session() as session:
            result = await session.get(Brand, brand_id)
            return to_schema(result, BrandRead) if result else None

    async def get_brand_by_uuid(self, uuid: str) -> Optional[BrandRead]:
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.uuid == uuid)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_brand_by_code(self, code: str) -> Optional[BrandRead]:
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_brands_by_distributor(self, distributor_id: int) -> List[BrandRead]:
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.distributor_id == distributor_id)
            result = await session.execute(stmt)
            return [to_schema(row, BrandRead) for row in result.scalars().all()]

    async def create_brand(self, data: BrandCreate) -> BrandRead:
        async with get_async_session() as session:
            brand_data = data.model_dump()
            brand_data['uuid'] = str(uuid.uuid4())
            brand_data['modified'] = datetime.utcnow()
            brand_data['created'] = datetime.utcnow()
            
            obj = Brand(**brand_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, BrandRead)

    async def update_brand(self, brand_id: int, data: BrandUpdate) -> Optional[BrandRead]:
        async with get_async_session() as session:
            obj = await session.get(Brand, brand_id)
            if not obj:
                return None
            
            update_data = data.model_dump(exclude_unset=True)
            update_data['modified'] = datetime.utcnow()
            
            for k, v in update_data.items():
                setattr(obj, k, v)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, BrandRead)

    async def delete_brand(self, brand_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(Brand, brand_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    async def search_brands(self, query: str) -> List[BrandRead]:
        """Search brands by name, code, or store"""
        q = f"%{query.lower()}%"
        async with get_async_session() as session:
            stmt = select(Brand).where(
                (Brand.name.ilike(q))
                | (Brand.code.ilike(q))
                | (Brand.store.ilike(q))
            )
            result = await session.execute(stmt)
            return [to_schema(row, BrandRead) for row in result.scalars().all()]

    # Deal operations




    # Analytics operations
    async def get_product_analytics(
        self, product_code: Optional[int] = None
    ) -> List[ProductAnalytics]:
        async with get_async_session() as session:
            prod_stmt = select(ProductModel)
            if product_code is not None:
                prod_stmt = prod_stmt.where(ProductModel.id == product_code)
            products = (await session.execute(prod_stmt)).scalars().all()
            analytics: List[ProductAnalytics] = []
            for p in products:
                # Calculate total revenue from price levels (using Trade price level if available)
                total_revenue = Decimal('0.0')
                for price_level in p.price_levels:
                    if price_level.price_level == "Trade":
                        total_revenue = price_level.value_excl
                        break
                
                analytics.append(
                    ProductAnalytics(
                        product_id=p.id,
                        product_name=p.product_name,
                        product_code=p.product_code,
                        brand_name=p.brand_name,
                        turnover_rate=0.0,  # TODO: Calculate from deals data
                        total_revenue=total_revenue,  # Calculate from price levels
                        current_stock=0,  # TODO: Get from inventory data
                    )
                )
            analytics.sort(key=lambda a: a.product_name)
            return analytics

    async def get_overall_analytics(self) -> OverallAnalytics:
        async with get_async_session() as session:
            products = (await session.execute(select(ProductModel))).scalars().all()
            total_products = len(products)
            active_products = len([p for p in products if p.status == 'Active'])
            total_brands = len(set(p.brand_name for p in products))
            total_categories = len(set(p.category_name for p in products))
            total_distributors = len(set(p.distributor_name for p in products))
            
            # Calculate total revenue from price levels
            total_revenue = Decimal('0.0')
            for p in products:
                for price_level in p.price_levels:
                    if price_level.price_level == "Trade":
                        total_revenue += price_level.value_excl
                        break
            
            return OverallAnalytics(
                average_turnover_rate=0.0,  # TODO: Calculate from deals data
                total_revenue=total_revenue,  # Calculate from price levels
                total_products=total_products,
                active_products=active_products,
                total_brands=total_brands,
                total_categories=total_categories,
                total_distributors=total_distributors,
            )

    # User operations
    async def get_user(self, keycloak_id: str) -> User:
        async with get_async_session() as session:
            result = await session.get(User, keycloak_id)
            return to_schema(result, User) if result else None
    
    async def create_user(self, data: User) -> User:
        async with get_async_session() as session:
            obj = User(**data.model_dump())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, User)

    # Rebate operations
    async def create_rebate_agreement(self, data: RebateAgreementCreate) -> RebateAgreementRead:
        """Create a new rebate agreement with validation and business rules."""
        async with get_async_session() as session:
            # Validate input
            if not data.products and not data.product_category_ids:
                raise ValueError("At least one product or product category must be specified")
            
            if data.start_date >= data.end_date:
                raise ValueError("Start date must be before end date")
            
            # Validate tier ranges if provided
            if data.tiers:
                self._validate_tier_ranges(data.tiers, data.basis)
            
            # Check for overlapping agreements (same distributor, products, and date range)
            await self._check_overlapping_agreements(session, data)
            
            # Create the rebate agreement
            agreement_data = data.model_dump()
            products = agreement_data.pop('products', [])
            product_category_ids = agreement_data.pop('product_category_ids', [])
            tiers = agreement_data.pop('tiers', [])
            
            # Generate UUID for agreement
            agreement_data['uuid'] = str(uuid.uuid4())
            agreement = RebateAgreement(**agreement_data)
            session.add(agreement)
            await session.flush()  # Get the agreement ID and UUID
            
            # Create product associations
            for product_id in products:
                product_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    product_id=product_id
                )
                session.add(product_assoc)
            
            # Create category associations
            for category_id in product_category_ids:
                category_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    category_id=category_id
                )
                session.add(category_assoc)
            
            # Create tiers with UUIDs and parent agreement UUID
            for tier_data in tiers:
                tier = self._create_tier_from_data(tier_data, agreement.id, agreement.uuid, data.basis)
                session.add(tier)
            
            await session.commit()
            await session.refresh(agreement)
            
            # Return the created agreement with all related data
            return await self._build_rebate_agreement_response(session, agreement)
    
    async def get_rebate_agreements(
        self, 
        agreement_type: Optional[str] = None,
        distributor_id: Optional[int] = None,
        status: Optional[str] = None,
        deal_type_id: Optional[int] = None,
        deal_source_id: Optional[int] = None,
        store: Optional[str] = None,
        product_class_id: Optional[int] = None,
        product_type_id: Optional[int] = None,
        product_category_id: Optional[int] = None
    ) -> List[RebateAgreementRead]:
        """Get rebate agreements with optional filtering."""
        async with get_async_session() as session:
            stmt = select(RebateAgreement).options(
                selectinload(RebateAgreement.products),
                selectinload(RebateAgreement.tiers)
            )
            
            if agreement_type:
                stmt = stmt.where(RebateAgreement.agreement_type == agreement_type)
            if distributor_id:
                stmt = stmt.where(RebateAgreement.distributor_id == distributor_id)
            if status:
                stmt = stmt.where(RebateAgreement.status == status)
            if deal_type_id:
                stmt = stmt.where(RebateAgreement.deal_type_id == deal_type_id)
            if deal_source_id:
                stmt = stmt.where(RebateAgreement.deal_source_id == deal_source_id)
            if store:
                stmt = stmt.where(RebateAgreement.store == store)
            if product_class_id:
                stmt = stmt.where(RebateAgreement.product_class_id == product_class_id)
            if product_type_id:
                stmt = stmt.where(RebateAgreement.product_type_id == product_type_id)
            if product_category_id:
                stmt = stmt.where(RebateAgreement.product_category_id == product_category_id)
            agreements = (await session.execute(stmt)).scalars().all()
            return [await self._build_rebate_agreement_response(session, agreement) for agreement in agreements]
    
    async def get_rebate_agreement(self, agreement_id: int) -> Optional[RebateAgreementRead]:
        """Get a specific rebate agreement by ID."""
        async with get_async_session() as session:
            stmt = select(RebateAgreement).options(
                selectinload(RebateAgreement.products),
                selectinload(RebateAgreement.tiers)
            ).where(RebateAgreement.id == agreement_id)
            
            result = await session.execute(stmt)
            agreement = result.scalar_one_or_none()
            if not agreement:
                return None
            return await self._build_rebate_agreement_response(session, agreement)
    
    async def update_rebate_agreement(self, agreement_id: int, data: RebateAgreementCreate) -> Optional[RebateAgreementRead]:
        """Update an existing rebate agreement."""
        async with get_async_session() as session:
            agreement = await session.get(RebateAgreement, agreement_id)
            if not agreement:
                return None
            
            # Validate input
            if not data.products and not data.product_category_ids:
                raise ValueError("At least one product or product category must be specified")
            
            if data.start_date >= data.end_date:
                raise ValueError("Start date must be before end date")
            
            # Validate tier ranges if provided
            if data.tiers:
                self._validate_tier_ranges(data.tiers, data.basis)
            
            # Update agreement fields
            agreement_data = data.model_dump()
            products = agreement_data.pop('products', [])
            product_category_ids = agreement_data.pop('product_category_ids', [])
            tiers = agreement_data.pop('tiers', [])
            
            for key, value in agreement_data.items():
                setattr(agreement, key, value)
            
            # Clear existing associations and tiers
            await session.execute(
                text("DELETE FROM rebate_agreement_products WHERE rebate_agreement_id = :id"),
                {"id": agreement_id}
            )
            await session.execute(
                text("DELETE FROM rebate_tiers WHERE rebate_agreement_id = :id"),
                {"id": agreement_id}
            )
            
            # Create new product associations
            for product_id in products:
                product_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    product_id=product_id
                )
                session.add(product_assoc)
            
            # Create new category associations
            for category_id in product_category_ids:
                category_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    category_id=category_id
                )
                session.add(category_assoc)
            
            # Create new tiers with UUIDs and parent agreement UUID
            for tier_data in tiers:
                tier = self._create_tier_from_data(tier_data, agreement.id, agreement.uuid, data.basis)
                session.add(tier)
            
            await session.commit()
            await session.refresh(agreement)
            
            return await self._build_rebate_agreement_response(session, agreement)
    
    async def delete_rebate_agreement(self, agreement_id: int) -> bool:
        """Delete a rebate agreement."""
        async with get_async_session() as session:
            agreement = await session.get(RebateAgreement, agreement_id)
            if not agreement:
                return False
            await session.delete(agreement)
            await session.commit()
            return True
    
    def _validate_tier_ranges(self, tiers: List[RebateTierCreate], basis: str):
        """Validate that tier ranges don't overlap and are properly ordered."""
        if not tiers:
            return
        
        # Sort tiers by from_value
        sorted_tiers = sorted(tiers, key=lambda t: t.from_quantity or t.from_amount or 0)
        
        for i, tier in enumerate(sorted_tiers):
            # Check that from_value is less than to_value
            from_val = tier.from_quantity if basis == "quantity" else tier.from_amount
            to_val = tier.to_quantity if basis == "quantity" else tier.to_amount
            
            if from_val is not None and to_val is not None and from_val >= to_val:
                raise ValueError(f"Tier {i+1}: from_value must be less than to_value")
            
            # Check for overlaps with previous tier
            if i > 0:
                prev_tier = sorted_tiers[i-1]
                prev_to_val = prev_tier.to_quantity if basis == "quantity" else prev_tier.to_amount
                
                if prev_to_val is not None and from_val is not None and prev_to_val > from_val:
                    raise ValueError(f"Tier {i+1} overlaps with previous tier")
    
    def _create_tier_from_data(self, tier_data: RebateTierCreate, agreement_id: int, agreement_uuid: str, basis: str) -> RebateTier:
        """Create a RebateTier database object from tier data, including UUIDs."""
        tier_dict = tier_data.model_dump()
        tier_dict['uuid'] = str(uuid.uuid4())
        tier_dict['rebate_agreement_uuid'] = agreement_uuid
        # Map rebate_value and rebate_unit to database fields
        tier_dict['rebate_value'] = tier_dict.pop('rebate_value')
        tier_dict['rebate_unit'] = tier_dict.pop('rebate_unit')
        # Set the appropriate from/to fields based on basis
        if basis == "quantity":
            tier_dict['from_quantity'] = tier_dict.pop('from_quantity')
            tier_dict['to_quantity'] = tier_dict.pop('to_quantity')
            tier_dict['from_amount'] = None
            tier_dict['to_amount'] = None
        else:  # amount
            tier_dict['from_amount'] = tier_dict.pop('from_amount')
            tier_dict['to_amount'] = tier_dict.pop('to_amount')
            tier_dict['from_quantity'] = None
            tier_dict['to_quantity'] = None
        tier_dict['rebate_agreement_id'] = agreement_id
        
        # Handle new deal-specific fields
        # These fields are optional, so we only set them if they exist
        deal_fields = ['value_type_id', 'calculated_on_price_level_id', 'value_stor', 
                      'value_stor_incl', 'value_hoff', 'value_hoff_incl']
        for field in deal_fields:
            if field in tier_dict:
                tier_dict[field] = tier_dict.pop(field)
        
        return RebateTier(**tier_dict)
    
    async def _check_overlapping_agreements(self, session, data: RebateAgreementCreate):
        """Check for overlapping agreements for the same distributor and products."""
        # This is a simplified check - in a real implementation, you might want more sophisticated logic
        stmt = select(RebateAgreement).options(
            selectinload(RebateAgreement.products)
        ).where(
            RebateAgreement.distributor_id == data.distributor_id,  # Fixed: use distributor_id
            RebateAgreement.agreement_type == data.agreement_type,
            RebateAgreement.status == "active"
        )
        
        existing_agreements = (await session.execute(stmt)).scalars().all()
        
        for existing in existing_agreements:
            # Check if date ranges overlap
            if (data.start_date <= existing.end_date and data.end_date >= existing.start_date):
                # Check if products overlap
                existing_products = [p.product_id for p in existing.products if p.product_id]
                existing_categories = [p.category_id for p in existing.products if p.category_id]
                
                if (set(data.products) & set(existing_products) or 
                    set(data.product_category_ids) & set(existing_categories)):
                    raise ValueError(f"Overlapping agreement found: {existing.description}")
    
    async def _build_rebate_agreement_response(self, session, agreement: RebateAgreement) -> RebateAgreementRead:
        """Build a complete RebateAgreementRead response with all related data."""
        # Get product IDs
        product_ids = []
        category_ids = []
        for product_assoc in agreement.products:
            if product_assoc.product_id:
                product_ids.append(product_assoc.product_id)
            if product_assoc.category_id:
                category_ids.append(product_assoc.category_id)
        
        # Build tier responses
        tiers = []
        for tier in agreement.tiers:
            tier_response = RebateTierRead(
                id=tier.id,
                uuid=tier.uuid,
                agreement_id=tier.rebate_agreement_id,
                rebate_agreement_uuid=tier.rebate_agreement_uuid,
                rebate_value=float(tier.rebate_value),
                rebate_unit=tier.rebate_unit,
                from_quantity=float(tier.from_quantity) if tier.from_quantity else None,
                to_quantity=float(tier.to_quantity) if tier.to_quantity else None,
                from_amount=float(tier.from_amount) if tier.from_amount else None,
                to_amount=float(tier.to_amount) if tier.to_amount else None,
            )
            tiers.append(tier_response)
        
        # Query database using brand details to get distributor_id and distributor_name
        async with get_async_session() as session:
            stmt = select(Distributor).where(Distributor.id == agreement.brand.distributor_id)
            result = await session.execute(stmt)
            distributor = result.scalar_one_or_none()
            queried_distributor_id = distributor.id if distributor else None
            queried_distributor_name = distributor.name if distributor else None
        
        
        return RebateAgreementRead(
            id=agreement.id,
            uuid=agreement.uuid,
            agreement_type=agreement.agreement_type,
            distributor_id=agreement.distributor_id,  # Fixed: use distributor_id instead of party_id
            description=agreement.description,
            start_date=agreement.start_date,
            end_date=agreement.end_date,
            calc_frequency=agreement.calc_frequency,
            basis=agreement.basis,
            rate_type=agreement.rate_type,
            approval_required=agreement.approval_required,
            products=product_ids,
            product_category_ids=category_ids,
            tiers=tiers,
            status=agreement.status,
            # NEW DEAL-SPECIFIC FIELDS
            deal_type_id=agreement.deal_type_id,
            deal_source_id=agreement.deal_source_id,
            price_level_type_id=agreement.price_level_type_id,
            value_stor=agreement.value_stor,
            value_stor_incl=agreement.value_stor_incl,
            value_hoff=agreement.value_hoff,
            value_hoff_incl=agreement.value_hoff_incl,
            valid_start=agreement.valid_start,
            valid_end=agreement.valid_end,
            claim_start=agreement.claim_start,
            claim_end=agreement.claim_end,
            bonus_status_code=agreement.bonus_status_code,
            bonus_status_name=agreement.bonus_status_name,
            deal_code=agreement.deal_code,
            store=agreement.store,
            # Deal Specific Fields 
            deal_value_type_id=agreement.deal_value_type_id,
            calculated_on_price_level_id=agreement.calculated_on_price_level_id,
            
            # CTC Based Relationship Filters 
            product_class_id=agreement.product_class_id,
            product_class_name=agreement.product_class.name if agreement.product_class else None,
            product_type_id=agreement.product_type_id,
            product_type_name=agreement.product_type.name if agreement.product_type else None,
            product_category_id=agreement.product_category_id,
            product_category_name=agreement.product_category.name if agreement.product_category else None,

            # Brand / Distributor Filters 
            brand_id=agreement.brand_id,
            brand_name=agreement.brand.name if agreement.brand else None,
            distributor_name=queried_distributor_name,
            
            # Product Filters
            product_id=agreement.product_id,
            product_name=agreement.product.name if agreement.product else None,
        )

    async def bulk_create_products(self, products: List[InsertProduct]) -> BulkProductCreateResult:
        # Use pandas for fast filtering
        import numpy as np
        import pandas as pd
        df = pd.DataFrame([p.model_dump() for p in products])
        # Preload all brands and distributors
        async with get_async_session() as session:
            stmt = (
                select(Distributor)
                .options(
                    selectinload(Distributor.purchaser),
                    selectinload(Distributor.default_contact)
                )
            )
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
        # Build lookup tables
        distributor_lookup = {normalize_name(d.name): d for d in distributors}
        brand_lookup = {normalize_name(b.name): b for b in brands}
        # Fast vectorized normalization
        df['normalized_distributor'] = df['distributor_name'].apply(normalize_name)
        df['normalized_brand'] = df['brand_name'].apply(normalize_name)
        # Find exact matches
        df['distributor_obj'] = df['normalized_distributor'].map(distributor_lookup)
        df['brand_obj'] = df['normalized_brand'].map(brand_lookup)
        created = []
        failed = []
        for idx, row in df.iterrows():
            data = InsertProduct(**{k: row[k] for k in InsertProduct.model_fields.keys() if k in row})
            fuzzy_matches = []
            distributor = row['distributor_obj']
            brand = row['brand_obj']
            # Fallback to fuzzy if not found
            if distributor is None:
                candidates = [(d.name, d) for d in distributors]
                best, sim, _ = find_best_match(row['distributor_name'], candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for distributor: '{row['distributor_name']}' -> '{best.name}' (sim={sim:.2f})")
                    distributor = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='distributor',
                        input_value=row['distributor_name'],
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    failed.append(ProductCreateResult(product=None, fuzzy_matches=[], error=f"Distributor '{row['distributor_name']}' not found"))
                    continue
            if brand is None:
                candidates = [(b.name, b) for b in brands]
                best, sim, _ = find_best_match(row['brand_name'], candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for brand: '{row['brand_name']}' -> '{best.name}' (sim={sim:.2f})")
                    brand = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='brand',
                        input_value=row['brand_name'],
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    failed.append(ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{row['brand_name']}' not found"))
                    continue
            if brand.distributor_id != distributor.id:
                failed.append(ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{row['brand_name']}' does not belong to distributor '{row['distributor_name']}'"))
                continue
            # Create product
            product_data = data.model_dump()
            price_levels_data = product_data.pop('price_levels', [])
            product_data['uuid'] = str(uuid.uuid4())
            product_data['distributor_id'] = distributor.id
            product_data['brand_id'] = brand.id
            product_data.pop('distributor_name', None)
            product_data.pop('brand_name', None)
            obj = ProductModel(**product_data)
            async with get_async_session() as session:
                session.add(obj)
                await session.flush()
                for price_level_data in price_levels_data:
                    price_level = PriceLevel(product_id=obj.id, **price_level_data)
                    session.add(price_level)
                await session.commit()
                await session.refresh(obj)
            created.append(ProductCreateResult(product=to_schema(obj, Product), fuzzy_matches=fuzzy_matches))
        return BulkProductCreateResult(created=created, failed=failed)

    # === FEATURES & BENEFITS CRUD ===
    # --- Class Level ---
    async def get_class_features_benefits(self, class_id: int) -> list:
        async with get_async_session() as session:
            stmt = select(ClassFeaturesBenefits).where(ClassFeaturesBenefits.class_id == class_id)
            result = await session.execute(stmt)
            return [to_schema(row, ClassFeaturesBenefitsRead) for row in result.scalars().all()]

    async def create_class_features_benefit(self, data: ClassFeaturesBenefitsCreate) -> ClassFeaturesBenefitsRead:
        async with get_async_session() as session:
            obj = ClassFeaturesBenefits(**data.model_dump())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, ClassFeaturesBenefitsRead)

    async def update_class_features_benefit(self, fb_id: int, data: ClassFeaturesBenefitsUpdate) -> ClassFeaturesBenefitsRead:
        async with get_async_session() as session:
            obj = await session.get(ClassFeaturesBenefits, fb_id)
            if not obj:
                return None
            for k, v in data.model_dump(exclude_unset=True).items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, ClassFeaturesBenefitsRead)

    async def delete_class_features_benefit(self, fb_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(ClassFeaturesBenefits, fb_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # --- Type Level ---
    async def get_type_features_benefits(self, type_id: int) -> list:
        async with get_async_session() as session:
            stmt = select(TypeFeaturesBenefits).where(TypeFeaturesBenefits.type_id == type_id)
            result = await session.execute(stmt)
            return [to_schema(row, TypeFeaturesBenefitsRead) for row in result.scalars().all()]

    async def create_type_features_benefit(self, data: TypeFeaturesBenefitsCreate) -> TypeFeaturesBenefitsRead:
        async with get_async_session() as session:
            obj = TypeFeaturesBenefits(**data.model_dump())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, TypeFeaturesBenefitsRead)

    async def update_type_features_benefit(self, fb_id: int, data: TypeFeaturesBenefitsUpdate) -> TypeFeaturesBenefitsRead:
        async with get_async_session() as session:
            obj = await session.get(TypeFeaturesBenefits, fb_id)
            if not obj:
                return None
            for k, v in data.model_dump(exclude_unset=True).items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, TypeFeaturesBenefitsRead)

    async def delete_type_features_benefit(self, fb_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(TypeFeaturesBenefits, fb_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # --- Category Level ---
    async def get_category_features_benefits(self, category_id: int) -> list:
        async with get_async_session() as session:
            stmt = select(CategoryFeaturesBenefits).where(CategoryFeaturesBenefits.category_id == category_id)
            result = await session.execute(stmt)
            return [to_schema(row, CategoryFeaturesBenefitsRead) for row in result.scalars().all()]

    async def create_category_features_benefit(self, data: CategoryFeaturesBenefitsCreate) -> CategoryFeaturesBenefitsRead:
        async with get_async_session() as session:
            obj = CategoryFeaturesBenefits(**data.model_dump())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, CategoryFeaturesBenefitsRead)

    async def update_category_features_benefit(self, fb_id: int, data: CategoryFeaturesBenefitsUpdate) -> CategoryFeaturesBenefitsRead:
        async with get_async_session() as session:
            obj = await session.get(CategoryFeaturesBenefits, fb_id)
            if not obj:
                return None
            for k, v in data.model_dump(exclude_unset=True).items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, CategoryFeaturesBenefitsRead)

    async def delete_category_features_benefit(self, fb_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(CategoryFeaturesBenefits, fb_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # --- Category Attribute CRUD ---
    async def get_category_attributes(self, category_id: int) -> list:
        from .models import CategoryAttributeRead
        async with get_async_session() as session:
            stmt = select(CategoryAttribute).where(CategoryAttribute.category_id == category_id)
            result = await session.execute(stmt)
            return [to_schema(row, CategoryAttributeRead) for row in result.scalars().all()]

    async def create_category_attribute(self, data):
        from .models import CategoryAttributeRead, CategoryAttributeCreate
        async with get_async_session() as session:
            obj = CategoryAttribute(**data.model_dump())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, CategoryAttributeRead)

    async def update_category_attribute(self, attr_id: int, data):
        from .models import CategoryAttributeRead, CategoryAttributeUpdate
        async with get_async_session() as session:
            obj = await session.get(CategoryAttribute, attr_id)
            if not obj:
                return None
            for k, v in data.model_dump(exclude_unset=True).items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, CategoryAttributeRead)

    async def delete_category_attribute(self, attr_id: int) -> bool:
        """Delete a category attribute"""
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CategoryAttribute).where(CategoryAttribute.id == attr_id)
                )
                attr = result.scalar_one_or_none()
                if not attr:
                    return False
                await session.delete(attr)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting category attribute: {e}")
                return False

    # ==================== CTC Methods ====================

    async def get_all_classes(self, active_only: bool = True) -> List[CTCClass]:
        async with get_async_session() as session:
            query = select(CTCClass)
            if active_only:
                query = query.where(CTCClass.active == True, CTCClass.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_class_by_id(self, class_id: int) -> Optional[CTCClass]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCClass).where(CTCClass.id == class_id)
            )
            return result.scalar_one_or_none()

    async def get_class_by_uuid(self, class_uuid: str) -> Optional[CTCClass]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCClass).where(CTCClass.uuid == class_uuid)
            )
            return result.scalar_one_or_none()

    async def get_class_by_code(self, code: str) -> Optional[CTCClass]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCClass).where(CTCClass.code == code)
            )
            return result.scalar_one_or_none()

    async def create_class(self, data: dict) -> CTCClass:
        async with get_async_session() as session:
            try:
                new_class = CTCClass(**data)
                session.add(new_class)
                await session.commit()
                await session.refresh(new_class)
                return new_class
            except Exception as e:
                await session.rollback()
                raise e

    async def update_class(self, class_id: int, data: dict) -> Optional[CTCClass]:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCClass).where(CTCClass.id == class_id)
                )
                class_obj = result.scalar_one_or_none()
                if not class_obj:
                    return None
                
                for key, value in data.items():
                    setattr(class_obj, key, value)
                
                await session.commit()
                await session.refresh(class_obj)
                return class_obj
            except Exception as e:
                await session.rollback()
                raise e

    async def delete_class(self, class_id: int, soft_delete: bool = True) -> bool:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCClass).where(CTCClass.id == class_id)
                )
                class_obj = result.scalar_one_or_none()
                if not class_obj:
                    return False
                
                if soft_delete:
                    class_obj.deleted = datetime.utcnow()
                    class_obj.deleted_by = "system"
                    class_obj.active = False
                else:
                    await session.delete(class_obj)
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    async def get_types_by_class(self, class_id: int, active_only: bool = True) -> List[CTCType]:
        async with get_async_session() as session:
            query = select(CTCType).where(CTCType.class_id == class_id)
            if active_only:
                query = query.where(CTCType.active == True, CTCType.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_types_by_class_uuid(self, class_uuid: str, active_only: bool = True) -> List[CTCType]:
        async with get_async_session() as session:
            query = (
                select(CTCType)
                .join(CTCClass, CTCType.class_id == CTCClass.id)
                .where(CTCClass.uuid == class_uuid)
            )
            if active_only:
                query = query.where(CTCType.active == True, CTCType.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_type_by_id(self, type_id: int) -> Optional[CTCType]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCType).where(CTCType.id == type_id)
            )
            return result.scalar_one_or_none()

    async def get_type_by_uuid(self, type_uuid: str) -> Optional[CTCType]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCType).where(CTCType.uuid == type_uuid)
            )
            return result.scalar_one_or_none()

    async def create_type(self, data: dict) -> CTCType:
        async with get_async_session() as session:
            try:
                new_type = CTCType(**data)
                session.add(new_type)
                await session.commit()
                await session.refresh(new_type)
                return new_type
            except Exception as e:
                await session.rollback()
                raise e

    async def update_type(self, type_id: int, data: dict) -> Optional[CTCType]:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCType).where(CTCType.id == type_id)
                )
                type_obj = result.scalar_one_or_none()
                if not type_obj:
                    return None
                
                for key, value in data.items():
                    setattr(type_obj, key, value)
                
                await session.commit()
                await session.refresh(type_obj)
                return type_obj
            except Exception as e:
                await session.rollback()
                raise e

    async def delete_type(self, type_id: int, soft_delete: bool = True) -> bool:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCType).where(CTCType.id == type_id)
                )
                type_obj = result.scalar_one_or_none()
                if not type_obj:
                    return False
                
                if soft_delete:
                    type_obj.deleted = datetime.utcnow()
                    type_obj.deleted_by = "system"
                    type_obj.active = False
                else:
                    await session.delete(type_obj)
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    async def get_categories_by_type(self, type_id: int, active_only: bool = True) -> List[CTCCategory]:
        async with get_async_session() as session:
            query = select(CTCCategory).where(CTCCategory.type_id == type_id)
            if active_only:
                query = query.where(CTCCategory.active == True, CTCCategory.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_categories_by_type_uuid(self, type_uuid: str, active_only: bool = True) -> List[CTCCategory]:
        async with get_async_session() as session:
            query = (
                select(CTCCategory)
                .join(CTCType, CTCCategory.type_id == CTCType.id)
                .where(CTCType.uuid == type_uuid)
            )
            if active_only:
                query = query.where(CTCCategory.active == True, CTCCategory.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_category_by_id(self, category_id: int) -> Optional[CTCCategory]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.id == category_id)
            )
            return result.scalar_one_or_none()

    async def get_category_by_uuid(self, category_uuid: str) -> Optional[CTCCategory]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.uuid == category_uuid)
            )
            return result.scalar_one_or_none()

    async def get_category_by_code(self, code: str) -> Optional[CTCCategory]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.code == code)
            )
            return result.scalar_one_or_none()

    async def create_category(self, data: dict) -> CTCCategory:
        async with get_async_session() as session:
            try:
                new_category = CTCCategory(**data)
                session.add(new_category)
                await session.commit()
                await session.refresh(new_category)
                return new_category
            except Exception as e:
                await session.rollback()
                raise e

    async def update_category(self, category_id: int, data: dict) -> Optional[CTCCategory]:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCCategory).where(CTCCategory.id == category_id)
                )
                category = result.scalar_one_or_none()
                if not category:
                    return None
                
                for key, value in data.items():
                    setattr(category, key, value)
                
                await session.commit()
                await session.refresh(category)
                return category
            except Exception as e:
                await session.rollback()
                raise e

    async def delete_category(self, category_id: int, soft_delete: bool = True) -> bool:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCCategory).where(CTCCategory.id == category_id)
                )
                category = result.scalar_one_or_none()
                if not category:
                    return False
                
                if soft_delete:
                    category.deleted = datetime.utcnow()
                    category.deleted_by = "system"
                    category.active = False
                else:
                    await session.delete(category)
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    async def get_attributes_by_category(self, category_id: int, active_only: bool = True) -> List[CTCAttribute]:
        logger.info(f"🔍 Getting attributes for category_id={category_id}, active_only={active_only}")
        
        async with get_async_session() as session:
            try:
                # First, let's check if the category exists
                category_query = select(CTCCategory).where(CTCCategory.id == category_id)
                category_result = await session.execute(category_query)
                category = category_result.scalar_one_or_none()
                
                if not category:
                    logger.warning(f"❌ Category with id={category_id} not found in database")
                    return []
                
                logger.info(f"✅ Found category: id={category.id}, name='{category.name}', code='{category.code}'")
                
                # Build the main query
                query = select(CTCAttribute).where(CTCAttribute.category_id == category_id)
                
                if active_only:
                    query = query.where(CTCAttribute.active == True, CTCAttribute.deleted == None)
                    logger.info(f"🔍 Query includes active_only filter")
                
                # Log the SQL query for debugging
                logger.info(f"🔍 Executing query: {query}")
                
                result = await session.execute(query)
                attributes = result.scalars().all()
                
                logger.info(f"📊 Found {len(attributes)} attributes for category_id={category_id}")
                
                # Log details of each attribute found
                for i, attr in enumerate(attributes):
                    logger.info(f"  📋 Attribute {i+1}: id={attr.id}, name='{attr.name}', active={attr.active}, deleted={attr.deleted}")
                
                return attributes
                
            except Exception as e:
                logger.error(f"❌ Error getting attributes for category_id={category_id}: {str(e)}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                raise e

    async def get_attribute_by_id(self, attribute_id: int) -> Optional[CTCAttribute]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCAttribute).where(CTCAttribute.id == attribute_id)
            )
            return result.scalar_one_or_none()

    async def get_attribute_by_uuid(self, attribute_uuid: str) -> Optional[CTCAttribute]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCAttribute).where(CTCAttribute.uuid == attribute_uuid)
            )
            return result.scalar_one_or_none()

    async def create_attribute(self, data: dict) -> CTCAttribute:
        async with get_async_session() as session:
            try:
                new_attribute = CTCAttribute(**data)
                session.add(new_attribute)
                await session.commit()
                await session.refresh(new_attribute)
                return new_attribute
            except Exception as e:
                await session.rollback()
                raise e

    async def update_attribute(self, attribute_id: int, data: dict) -> Optional[CTCAttribute]:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCAttribute).where(CTCAttribute.id == attribute_id)
                )
                attribute = result.scalar_one_or_none()
                if not attribute:
                    return None
                
                for key, value in data.items():
                    setattr(attribute, key, value)
                
                await session.commit()
                await session.refresh(attribute)
                return attribute
            except Exception as e:
                await session.rollback()
                raise e

    async def delete_attribute(self, attribute_id: int, soft_delete: bool = True) -> bool:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCAttribute).where(CTCAttribute.id == attribute_id)
                )
                attribute = result.scalar_one_or_none()
                if not attribute:
                    return False
                
                if soft_delete:
                    attribute.deleted = datetime.utcnow()
                    attribute.deleted_by = "system"
                    attribute.active = False
                else:
                    await session.delete(attribute)
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    async def get_all_attribute_groups(self, active_only: bool = True) -> List[CTCAttributeGroup]:
        async with get_async_session() as session:
            query = select(CTCAttributeGroup)
            if active_only:
                query = query.where(CTCAttributeGroup.active == True, CTCAttributeGroup.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_attribute_group_by_id(self, group_id: int) -> Optional[CTCAttributeGroup]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCAttributeGroup).where(CTCAttributeGroup.id == group_id)
            )
            return result.scalar_one_or_none()

    async def create_attribute_group(self, data: dict) -> CTCAttributeGroup:
        async with get_async_session() as session:
            try:
                new_group = CTCAttributeGroup(**data)
                session.add(new_group)
                await session.commit()
                await session.refresh(new_group)
                return new_group
            except Exception as e:
                await session.rollback()
                raise e

    async def get_all_data_types(self, active_only: bool = True) -> List[CTCDataType]:
        async with get_async_session() as session:
            query = select(CTCDataType)
            if active_only:
                query = query.where(CTCDataType.active == True, CTCDataType.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_data_type_by_id(self, data_type_id: int) -> Optional[CTCDataType]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCDataType).where(CTCDataType.id == data_type_id)
            )
            return result.scalar_one_or_none()

    async def create_data_type(self, data: dict) -> CTCDataType:
        async with get_async_session() as session:
            try:
                new_data_type = CTCDataType(**data)
                session.add(new_data_type)
                await session.commit()
                await session.refresh(new_data_type)
                return new_data_type
            except Exception as e:
                await session.rollback()
                raise e

    async def get_all_units_of_measure(self, active_only: bool = True) -> List[CTCUnitOfMeasure]:
        async with get_async_session() as session:
            query = select(CTCUnitOfMeasure)
            if active_only:
                query = query.where(CTCUnitOfMeasure.active == True, CTCUnitOfMeasure.deleted == None)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_unit_of_measure_by_id(self, uom_id: int) -> Optional[CTCUnitOfMeasure]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCUnitOfMeasure).where(CTCUnitOfMeasure.id == uom_id)
            )
            return result.scalar_one_or_none()

    async def create_unit_of_measure(self, data: dict) -> CTCUnitOfMeasure:
        async with get_async_session() as session:
            try:
                new_uom = CTCUnitOfMeasure(**data)
                session.add(new_uom)
                await session.commit()
                await session.refresh(new_uom)
                return new_uom
            except Exception as e:
                await session.rollback()
                raise e

    async def get_full_hierarchy(self, class_id: Optional[int] = None) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            try:
                if class_id:
                    # Get specific class hierarchy
                    query = (
                        select(CTCClass)
                        .options(
                            joinedload(CTCClass.types).joinedload(CTCType.categories)
                        )
                        .where(CTCClass.id == class_id)
                    )
                    result = await session.execute(query)
                    class_obj = result.unique().scalar_one_or_none()
                    
                    if not class_obj:
                        return []
                    
                    hierarchy = []
                    for type_obj in class_obj.types:
                        if type_obj.active and not type_obj.deleted:
                            type_data = {
                               "id": type_obj.id,
                                "uuid": type_obj.uuid,
                                "code": type_obj.code,
                                "name": type_obj.name,
                                "active": type_obj.active,
                                "categories": []
                            }
                            for category in type_obj.categories:
                                if category.active and not category.deleted:
                                    category_data = {
                                       "id": category.id,
                                        "uuid": category.uuid,
                                        "code": category.code,
                                        "name": category.name,
                                        "active": category.active,
                                        "product_id": category.product_id
                                    }
                                    type_data["categories"].append(category_data)
                            
                            hierarchy.append(type_data)
                    
                    return hierarchy
                else:
                    # Get all classes with their types and categories
                    query = (
                        select(CTCClass)
                        .options(
                            joinedload(CTCClass.types).joinedload(CTCType.categories)
                        )
                        .where(CTCClass.active == True, CTCClass.deleted == None)
                    )
                    result = await session.execute(query)
                    classes = result.unique().scalars().all()
                    
                    hierarchy = []
                    for class_obj in classes:
                        class_data = {
                            "id": class_obj.id,
                            "uuid": class_obj.uuid,
                            "code": class_obj.code,
                            "name": class_obj.name,
                            "active": class_obj.active,
                            "types": []
                        }
                        for type_obj in class_obj.types:
                            if type_obj.active and not type_obj.deleted:
                                type_data = {
                                   "id": type_obj.id,
                                    "uuid": type_obj.uuid,
                                    "code": type_obj.code,
                                    "name": type_obj.name,
                                    "active": type_obj.active,
                                    "categories": []
                                }
                                for category in type_obj.categories:
                                    if category.active and not category.deleted:
                                        category_data = {
                                           "id": category.id,
                                            "uuid": category.uuid,
                                            "code": category.code,
                                            "name": category.name,
                                            "active": category.active,
                                            "product_id": category.product_id
                                        }
                                        type_data["categories"].append(category_data)
                                class_data["types"].append(type_data)
                        hierarchy.append(class_data)
                    
                    return hierarchy
            except Exception as e:
                logger.error(f"Error retrieving hierarchy: {e}")
                raise e

    async def search_ctc(self, search_term: str, level: Optional[int] = None) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            try:
                results = []
                
                if level is None or level == 1:
                    # Search classes
                    query = (
                        select(CTCClass)
                        .where(
                            and_(
                                CTCClass.active == True,
                                CTCClass.deleted == None,
                                or_(
                                    CTCClass.name.ilike(f"%{search_term}%"),
                                    CTCClass.code.ilike(f"%{search_term}%")
                                )
                            )
                        )
                    )
                    result = await session.execute(query)
                    classes = result.unique().scalars().all()
                    
                    for cls in classes:
                        results.append({
                      "level": "class",
                            "id": cls.id,
                            "uuid": cls.uuid,
                            "code": cls.code,
                            "name": cls.name,
                            "active": cls.active
                        })
                
                if level is None or level == 2:
                    # Search types
                    query = (
                        select(CTCType)
                        .where(
                            and_(
                                CTCType.active == True,
                                CTCType.deleted == None,
                                or_(
                                    CTCType.name.ilike(f"%{search_term}%"),
                                    CTCType.code.ilike(f"%{search_term}%")
                                )
                            )
                        )
                    )
                    result = await session.execute(query)
                    types = result.unique().scalars().all()
                    
                    for type_obj in types:
                        results.append({
                      "level": "type",
                            "id": type_obj.id,
                            "uuid": type_obj.uuid,
                            "code": type_obj.code,
                            "name": type_obj.name,
                            "active": type_obj.active,
                          "class_id": type_obj.class_id
                        })
                
                if level is None or level == 3:
                    # Search categories
                    query = (
                        select(CTCCategory)
                        .where(
                            and_(
                                CTCCategory.active == True,
                                CTCCategory.deleted == None,
                                or_(
                                    CTCCategory.name.ilike(f"%{search_term}%"),
                                    CTCCategory.code.ilike(f"%{search_term}%")
                                )
                            )
                        )
                    )
                    result = await session.execute(query)
                    categories = result.unique().scalars().all()
                    
                    for category in categories:
                        results.append({
                      "level": "category",
                            "id": category.id,
                            "uuid": category.uuid,
                            "code": category.code,
                            "name": category.name,
                            "active": category.active,
                    "type_id": category.type_id,
                       "product_id": category.product_id
                        })
                
                return results
            except Exception as e:
                logger.error(f"Error searching CTC data: {e}")
                raise e

    async def get_category_with_attributes(self, category_id: int) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            try:
                query = (
                    select(CTCCategory)
                    .options(
                        joinedload(CTCCategory.ctc_attributes).joinedload(CTCAttribute.attribute_group),
                        joinedload(CTCCategory.ctc_attributes).joinedload(CTCAttribute.data_type),
                        joinedload(CTCCategory.ctc_attributes).joinedload(CTCAttribute.uom),
                        joinedload(CTCCategory.attributes)
                    )
                    .where(CTCCategory.id == category_id)
                )
                result = await session.execute(query)
                category = result.scalar_one_or_none()
                
                if not category:
                    return None
                
                # Build response
                category_data = {
                   "id": category.id,
                    "uuid": category.uuid,
                    "code": category.code,
                    "name": category.name,
                    "active": category.active,
                    "type_id": category.type_id,
                    "product_id": category.product_id,
                    "ctc_attributes": [],
                    "simple_attributes": []
                }
                
                # Add CTC attributes
                for attr in category.ctc_attributes:
                    if attr.active and not attr.deleted:
                        attr_data = {
                         "id": attr.id,
                           "uuid": attr.uuid,
                           "name": attr.name,
                           "rank": attr.rank,
                           "as_filter": attr.as_filter,
                        "active": attr.active,
                            "attribute_group": {
                         "id": attr.attribute_group.id,
                           "name": attr.attribute_group.name,
                           "code": attr.attribute_group.code
                            },
                         "data_type": {
                               "id": attr.data_type.id,
                               "name": attr.data_type.name,
                               "code": attr.data_type.code
                            }
                        }
                        
                        if attr.uom:
                            attr_data["unit_of_measure"] = {
                               "id": attr.uom.id,
                              "name": attr.uom.name,
                              "code": attr.uom.code
                            }
                        
                        category_data["ctc_attributes"].append(attr_data)
                
                # Add simple attributes
                for attr in category.attributes:
                    attr_data = {
                     "id": attr.id,
                   "name": attr.name,
                   "value": attr.value
                    }
                    category_data["simple_attributes"].append(attr_data)
                
                return category_data
            except Exception as e:
                logger.error(f"Error retrieving category with attributes: {e}")
                raise e

    async def get_statistics(self) -> Dict[str, Dict[str, int]]:
        async with get_async_session() as session:
            try:
                # Count classes
                class_result = await session.execute(
                    select(func.count(CTCClass.id)).where(CTCClass.active == True, CTCClass.deleted == None)
                )
                total_classes = class_result.scalar()
                
                class_result_inactive = await session.execute(
                    select(func.count(CTCClass.id)).where(CTCClass.active == False)
                )
                inactive_classes = class_result_inactive.scalar()
                
                # Count types
                type_result = await session.execute(
                    select(func.count(CTCType.id)).where(CTCType.active == True, CTCType.deleted == None)
                )
                total_types = type_result.scalar()
                
                type_result_inactive = await session.execute(
                    select(func.count(CTCType.id)).where(CTCType.active == False)
                )
                inactive_types = type_result_inactive.scalar()
                
                # Count categories
                category_result = await session.execute(
                    select(func.count(CTCCategory.id)).where(CTCCategory.active == True, CTCCategory.deleted == None)
                )
                total_categories = category_result.scalar()
                
                category_result_inactive = await session.execute(
                    select(func.count(CTCCategory.id)).where(CTCCategory.active == False)
                )
                inactive_categories = category_result_inactive.scalar()
                
                # Count attributes
                attr_result = await session.execute(
                    select(func.count(CTCAttribute.id)).where(CTCAttribute.active == True, CTCAttribute.deleted == None)
                )
                total_attributes = attr_result.scalar()
                
                attr_result_inactive = await session.execute(
                    select(func.count(CTCAttribute.id)).where(CTCAttribute.active == False)
                )
                inactive_attributes = attr_result_inactive.scalar()
                
                return {
               "classes": {
                    "total": total_classes,
                    "active": total_classes,
                    "inactive": inactive_classes
                },
             "types": {
                    "total": total_types,
                    "active": total_types,
                    "inactive": inactive_types
                },
                  "categories": {
                    "total": total_categories,
                    "active": total_categories,
                    "inactive": inactive_categories
                },
                  "attributes": {
                    "total": total_attributes,
                    "active": total_attributes,
                    "inactive": inactive_attributes
                }
            }
            except Exception as e:
                logger.error(f"Error retrieving statistics: {e}")
                raise e

    async def assign_product_to_category(self, category_id: int, product_id: int) -> bool:
        async with get_async_session() as session:
            try:
                # Check if category exists
                category_result = await session.execute(
                    select(CTCCategory).where(CTCCategory.id == category_id)
                )
                category = category_result.scalar_one_or_none()
                if not category:
                    return False
                
                # Check if product exists
                product_result = await session.execute(
                    select(ProductModel).where(ProductModel.id == product_id)
                )
                product = product_result.scalar_one_or_none()
                if not product:
                    return False
                
                # Assign product to category
                category.product_id = product_id
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Error assigning product to category: {e}")
                return False

    async def remove_product_from_category(self, category_id: int) -> bool:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(CTCCategory).where(CTCCategory.id == category_id)
                )
                category = result.scalar_one_or_none()
                if not category:
                    return False
                
                category.product_id = None
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Error removing product from category: {e}")
                return False

    async def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            try:
                query = (
                    select(ProductModel)
                    .join(CTCCategory, ProductModel.id == CTCCategory.product_id)
                    .where(CTCCategory.id == category_id)
                )
                result = await session.execute(query)
                products = result.scalars().all()
                
                return [
    {
                     "id": product.id,
                     "uuid": product.uuid,
                     "product_code": product.product_code,
                     "product_name": product.product_name,
                   "brand_name": product.brand_name,
                       "distributor_name": product.distributor_name
                    }
                    for product in products
                ]
            except Exception as e:
                logger.error(f"Error retrieving products for category: {e}")
                raise e

    async def get_categories_by_product(self, product_id: int) -> List[CTCCategory]:
        async with get_async_session() as session:
            stmt = (
                select(CTCCategory)
                .where(CTCCategory.product_id == product_id)
                .where(CTCCategory.active == True)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    ### PRICE LEVEL TYPE OPERATIONS ###

    async def get_price_level_types(self, active_only: bool = True) -> List[PriceLevelTypeRead]:
        """Get all price level types"""
        async with get_async_session() as session:
            stmt = select(PriceLevelType)
            if active_only:
                stmt = stmt.where(PriceLevelType.active == True)
            stmt = stmt.order_by(PriceLevelType.code)
            result = await session.execute(stmt)
            return [to_schema(row, PriceLevelTypeRead) for row in result.scalars().all()]

    async def get_price_level_type(self, type_id: int) -> Optional[PriceLevelTypeRead]:
        """Get a specific price level type by ID"""
        async with get_async_session() as session:
            result = await session.get(PriceLevelType, type_id)
            return to_schema(result, PriceLevelTypeRead) if result else None

    async def get_price_level_type_by_code(self, code: str) -> Optional[PriceLevelTypeRead]:
        """Get a price level type by code"""
        async with get_async_session() as session:
            stmt = select(PriceLevelType).where(PriceLevelType.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, PriceLevelTypeRead) if row else None

    async def create_price_level_type(self, data: PriceLevelTypeCreate) -> PriceLevelTypeRead:
        """Create a new price level type"""
        async with get_async_session() as session:
            # Check if code already exists
            existing = await session.execute(
                select(PriceLevelType).where(PriceLevelType.code == data.code)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Price level type with code '{data.code}' already exists")

            price_level_type = PriceLevelType(
                code=data.code,
                name=data.name,
                store=data.store,
                is_incl=data.is_incl,
                apply_to_db=data.apply_to_db,
                price_type_code=data.price_type_code,
                price_type_name=data.price_type_name,
                parent_code=data.parent_code,
                active=data.active,
                modified_by=data.modified_by,
                created_by=data.created_by,
                modified=datetime.utcnow(),
                created=datetime.utcnow()
            )
            session.add(price_level_type)
            await session.commit()
            await session.refresh(price_level_type)
            return to_schema(price_level_type, PriceLevelTypeRead)

    async def update_price_level_type(self, type_id: int, data: PriceLevelTypeUpdate) -> Optional[PriceLevelTypeRead]:
        """Update a price level type"""
        async with get_async_session() as session:
            price_level_type = await session.get(PriceLevelType, type_id)
            if not price_level_type:
                return None

            # Check if code is being changed and if it already exists
            if data.code and data.code != price_level_type.code:
                existing = await session.execute(
                    select(PriceLevelType).where(PriceLevelType.code == data.code)
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Price level type with code '{data.code}' already exists")

            # Update fields
            update_data = data.model_dump(exclude_unset=True)
            if update_data:
                update_data['modified'] = datetime.utcnow()
                for key, value in update_data.items():
                    setattr(price_level_type, key, value)
                await session.commit()
                await session.refresh(price_level_type)

            return to_schema(price_level_type, PriceLevelTypeRead)

    async def delete_price_level_type(self, type_id: int, soft_delete: bool = True) -> bool:
        """Delete a price level type"""
        async with get_async_session() as session:
            price_level_type = await session.get(PriceLevelType, type_id)
            if not price_level_type:
                return False

            if soft_delete:
                price_level_type.active = False
                price_level_type.deleted = datetime.utcnow()
                price_level_type.deleted_by = "system"
            else:
                await session.delete(price_level_type)

            await session.commit()
            return True


    ### DEAL SOURCE OPERATIONS ###

    async def get_deal_sources(self, active_only: bool = True) -> List[DealSourceRead]:
        """Get all deal sources"""
        async with get_async_session() as session:
            stmt = select(DealSource)
            if active_only:
                stmt = stmt.where(DealSource.active == True)
            stmt = stmt.order_by(DealSource.code)
            result = await session.execute(stmt)
            return [to_schema(row, DealSourceRead) for row in result.scalars().all()]

    async def get_deal_source(self, source_id: int) -> Optional[DealSourceRead]:
        """Get a specific deal source by ID"""
        async with get_async_session() as session:
            result = await session.get(DealSource, source_id)
            return to_schema(result, DealSourceRead) if result else None

    async def get_deal_source_by_code(self, code: str) -> Optional[DealSourceRead]:
        """Get a deal source by code"""
        async with get_async_session() as session:
            stmt = select(DealSource).where(DealSource.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DealSourceRead) if row else None

    async def create_deal_source(self, data: DealSourceCreate) -> DealSourceRead:
        """Create a new deal source"""
        async with get_async_session() as session:
            # Check if code already exists
            existing = await session.execute(
                select(DealSource).where(DealSource.code == data.code)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Deal source with code '{data.code}' already exists")

            deal_source = DealSource(
                code=data.code,
                name=data.name,
                store=data.store,
                for_hoff_only=data.for_hoff_only,
                active=data.active,
                modified_by=data.modified_by,
                created_by=data.created_by,
                modified=datetime.utcnow(),
                created=datetime.utcnow()
            )
            session.add(deal_source)
            await session.commit()
            await session.refresh(deal_source)
            return to_schema(deal_source, DealSourceRead)

    async def update_deal_source(self, source_id: int, data: DealSourceUpdate) -> Optional[DealSourceRead]:
        """Update a deal source"""
        async with get_async_session() as session:
            deal_source = await session.get(DealSource, source_id)
            if not deal_source:
                return None

            # Check if code is being changed and if it already exists
            if data.code and data.code != deal_source.code:
                existing = await session.execute(
                    select(DealSource).where(DealSource.code == data.code)
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Deal source with code '{data.code}' already exists")

            # Update fields
            update_data = data.model_dump(exclude_unset=True)
            if update_data:
                update_data['modified'] = datetime.utcnow()
                for key, value in update_data.items():
                    setattr(deal_source, key, value)
                await session.commit()
                await session.refresh(deal_source)

            return to_schema(deal_source, DealSourceRead)

    async def delete_deal_source(self, source_id: int, soft_delete: bool = True) -> bool:
        """Delete a deal source"""
        async with get_async_session() as session:
            deal_source = await session.get(DealSource, source_id)
            if not deal_source:
                return False

            if soft_delete:
                deal_source.active = False
                deal_source.deleted = datetime.utcnow()
                deal_source.deleted_by = "system"
            else:
                await session.delete(deal_source)

            await session.commit()
            return True


    ### DEAL TYPE OPERATIONS ###

    async def get_deal_types(self, active_only: bool = True) -> List[DealTypeRead]:
        """Get all deal types"""
        async with get_async_session() as session:
            stmt = (
                select(DealType)
                .options(selectinload(DealType.default_provider))
            )
            if active_only:
                stmt = stmt.where(DealType.active == True)
            stmt = stmt.order_by(DealType.rank, DealType.code)
            result = await session.execute(stmt)
            return [to_schema(row, DealTypeRead) for row in result.scalars().all()]

    async def get_deal_type(self, type_id: int) -> Optional[DealTypeRead]:
        """Get a specific deal type by ID"""
        async with get_async_session() as session:
            stmt = (
                select(DealType)
                .options(selectinload(DealType.default_provider))
                .where(DealType.id == type_id)
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DealTypeRead) if row else None

    async def get_deal_type_by_code(self, code: str) -> Optional[DealTypeRead]:
        """Get a deal type by code"""
        async with get_async_session() as session:
            stmt = (
                select(DealType)
                .options(selectinload(DealType.default_provider))
                .where(DealType.code == code)
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DealTypeRead) if row else None

    async def create_deal_type(self, data: DealTypeCreate) -> DealTypeRead:
        """Create a new deal type"""
        async with get_async_session() as session:
            # Check if code already exists
            existing = await session.execute(
                select(DealType).where(DealType.code == data.code)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Deal type with code '{data.code}' already exists")

            # Validate default provider if provided
            if data.default_provider_id:
                provider = await session.get(DealSource, data.default_provider_id)
                if not provider:
                    raise ValueError(f"Deal source with ID {data.default_provider_id} not found")

            deal_type = DealType(
                code=data.code,
                name=data.name,
                store=data.store,
                rank=data.rank,
                bonus_class=data.bonus_class,
                claimable=data.claimable,
                deductable=data.deductable,
                default_provider_id=data.default_provider_id,
                active=data.active,
                modified_by=data.modified_by,
                created_by=data.created_by,
                modified=datetime.utcnow(),
                created=datetime.utcnow()
            )
            session.add(deal_type)
            await session.commit()
            await session.refresh(deal_type)
            
            # Load the relationship for the response
            return to_schema(deal_type, DealTypeRead)

    async def update_deal_type(self, type_id: int, data: DealTypeUpdate) -> Optional[DealTypeRead]:
        """Update a deal type"""
        async with get_async_session() as session:
            deal_type = await session.get(DealType, type_id)
            if not deal_type:
                return None

            # Check if code is being changed and if it already exists
            if data.code and data.code != deal_type.code:
                existing = await session.execute(
                    select(DealType).where(DealType.code == data.code)
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Deal type with code '{data.code}' already exists")

            # Validate default provider if being changed
            if data.default_provider_id and data.default_provider_id != deal_type.default_provider_id:
                provider = await session.get(DealSource, data.default_provider_id)
                if not provider:
                    raise ValueError(f"Deal source with ID {data.default_provider_id} not found")

            # Update fields
            update_data = data.model_dump(exclude_unset=True)
            if update_data:
                update_data['modified'] = datetime.utcnow()
                for key, value in update_data.items():
                    setattr(deal_type, key, value)
                await session.commit()
                await session.refresh(deal_type)

            return to_schema(deal_type, DealTypeRead)

    async def delete_deal_type(self, type_id: int, soft_delete: bool = True) -> bool:
        """Delete a deal type"""
        async with get_async_session() as session:
            deal_type = await session.get(DealType, type_id)
            if not deal_type:
                return False

            if soft_delete:
                deal_type.active = False
                deal_type.deleted = datetime.utcnow()
                deal_type.deleted_by = "system"
            else:
                await session.delete(deal_type)

            await session.commit()
            return True

    # ==================== CTC Link-Types Methods ====================

    async def get_type_links(self, source_type_id: Optional[int] = None, target_type_id: Optional[int] = None, active_only: bool = True) -> List[CTCTypeLink]:
        """Get CTC type links with optional filtering"""
        try:
            async with get_async_session() as session:
                query = select(CTCTypeLink)
                
                if active_only:
                    query = query.where(CTCTypeLink.active == True)
                
                if source_type_id:
                    query = query.where(CTCTypeLink.source_type_id == source_type_id)
                
                if target_type_id:
                    query = query.where(CTCTypeLink.target_type_id == target_type_id)
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting type links: {str(e)}")
            return []

    async def get_type_link_by_id(self, link_id: int) -> Optional[CTCTypeLink]:
        """Get a specific CTC type link by ID"""
        try:
            async with get_async_session() as session:
                return await session.get(CTCTypeLink, link_id)
        except Exception as e:
            logger.error(f"Error getting type link: {str(e)}")
            return None

    async def get_type_link_by_uuid(self, link_uuid: str) -> Optional[CTCTypeLink]:
        """Get a specific CTC type link by UUID"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(CTCTypeLink).where(CTCTypeLink.uuid == link_uuid)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting type link by UUID: {str(e)}")
            return None

    async def create_type_link(self, data: dict) -> CTCTypeLink:
        """Create a new CTC type link"""
        try:
            async with get_async_session() as session:
                type_link = CTCTypeLink(**data)
                session.add(type_link)
                await session.commit()
                await session.refresh(type_link)
                return type_link
        except Exception as e:
            logger.error(f"Error creating type link: {str(e)}")
            raise

    async def update_type_link(self, link_id: int, data: dict) -> Optional[CTCTypeLink]:
        """Update an existing CTC type link"""
        try:
            async with get_async_session() as session:
                type_link = await session.get(CTCTypeLink, link_id)
                if not type_link:
                    return None
                
                for key, value in data.items():
                    if hasattr(type_link, key):
                        setattr(type_link, key, value)
                
                type_link.modified = datetime.utcnow()
                await session.commit()
                await session.refresh(type_link)
                return type_link
        except Exception as e:
            logger.error(f"Error updating type link: {str(e)}")
            return None

    async def delete_type_link(self, link_id: int, soft_delete: bool = True) -> bool:
        """Delete a CTC type link (soft delete by default)"""
        try:
            async with get_async_session() as session:
                type_link = await session.get(CTCTypeLink, link_id)
                if not type_link:
                    return False
                
                if soft_delete:
                    type_link.active = False
                    type_link.deleted_by = "system"
                    type_link.deleted = datetime.utcnow()
                else:
                    await session.delete(type_link)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting type link: {str(e)}")
            return False

    async def get_type_options(self, source_type_id: Optional[int] = None, option_type_id: Optional[int] = None, active_only: bool = True) -> List[CTCTypeOption]:
        """Get CTC type options with optional filtering"""
        try:
            async with get_async_session() as session:
                query = select(CTCTypeOption)
                
                if active_only:
                    query = query.where(CTCTypeOption.active == True)
                
                if source_type_id:
                    query = query.where(CTCTypeOption.source_type_id == source_type_id)
                
                if option_type_id:
                    query = query.where(CTCTypeOption.option_type_id == option_type_id)
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting type options: {str(e)}")
            return []

    async def get_type_option_by_id(self, option_id: int) -> Optional[CTCTypeOption]:
        """Get a specific CTC type option by ID"""
        try:
            async with get_async_session() as session:
                return await session.get(CTCTypeOption, option_id)
        except Exception as e:
            logger.error(f"Error getting type option: {str(e)}")
            return None

    async def get_type_option_by_uuid(self, option_uuid: str) -> Optional[CTCTypeOption]:
        """Get a specific CTC type option by UUID"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(CTCTypeOption).where(CTCTypeOption.uuid == option_uuid)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting type option by UUID: {str(e)}")
            return None

    async def create_type_option(self, data: dict) -> CTCTypeOption:
        """Create a new CTC type option"""
        try:
            async with get_async_session() as session:
                type_option = CTCTypeOption(**data)
                session.add(type_option)
                await session.commit()
                await session.refresh(type_option)
                return type_option
        except Exception as e:
            logger.error(f"Error creating type option: {str(e)}")
            raise

    async def update_type_option(self, option_id: int, data: dict) -> Optional[CTCTypeOption]:
        """Update an existing CTC type option"""
        try:
            async with get_async_session() as session:
                type_option = await session.get(CTCTypeOption, option_id)
                if not type_option:
                    return None
                
                for key, value in data.items():
                    if hasattr(type_option, key):
                        setattr(type_option, key, value)
                
                type_option.modified = datetime.utcnow()
                await session.commit()
                await session.refresh(type_option)
                return type_option
        except Exception as e:
            logger.error(f"Error updating type option: {str(e)}")
            return None

    async def delete_type_option(self, option_id: int, soft_delete: bool = True) -> bool:
        """Delete a CTC type option (soft delete by default)"""
        try:
            async with get_async_session() as session:
                type_option = await session.get(CTCTypeOption, option_id)
                if not type_option:
                    return False
                
                if soft_delete:
                    type_option.active = False
                    type_option.deleted_by = "system"
                    type_option.deleted = datetime.utcnow()
                else:
                    await session.delete(type_option)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting type option: {str(e)}")
            return False

    async def get_type_link_statistics(self) -> Dict[str, Any]:
        """Get statistics for CTC type links"""
        try:
            async with get_async_session() as session:
                # Total links
                total_links = await session.scalar(select(func.count(CTCTypeLink.id)))
                
                # Unique source types
                unique_sources = await session.scalar(
                    select(func.count(func.distinct(CTCTypeLink.source_type_id)))
                )
                
                # Unique target types
                unique_targets = await session.scalar(
                    select(func.count(func.distinct(CTCTypeLink.target_type_id)))
                )
                
                # Average links per source
                avg_links = await session.scalar(
                    select(func.avg(func.count(CTCTypeLink.id)))
                    .group_by(CTCTypeLink.source_type_id)
                ) or 0.0
                
                # Most linked source type
                most_linked_source = await session.execute(
                    select(CTCTypeLink.source_type_id, func.count(CTCTypeLink.id).label('count'))
                    .group_by(CTCTypeLink.source_type_id)
                    .order_by(desc('count'))
                    .limit(1)
                )
                most_linked_source_result = most_linked_source.first()
                
                # Most linked target type
                most_linked_target = await session.execute(
                    select(CTCTypeLink.target_type_id, func.count(CTCTypeLink.id).label('count'))
                    .group_by(CTCTypeLink.target_type_id)
                    .order_by(desc('count'))
                    .limit(1)
                )
                most_linked_target_result = most_linked_target.first()
                
                # Scraped at range
                scraped_range = await session.execute(
                    select(
                        func.min(CTCTypeLink.scraped_at).label('min_date'),
                        func.max(CTCTypeLink.scraped_at).label('max_date')
                    )
                )
                scraped_range_result = scraped_range.first()
                
                return {
                    "total_links": total_links or 0,
                    "unique_source_types": unique_sources or 0,
                    "unique_target_types": unique_targets or 0,
                    "average_links_per_source": float(avg_links),
                    "most_linked_source_type": {
                        "type_id": most_linked_source_result[0],
                        "count": most_linked_source_result[1]
                    } if most_linked_source_result else None,
                    "most_linked_target_type": {
                        "type_id": most_linked_target_result[0],
                        "count": most_linked_target_result[1]
                    } if most_linked_target_result else None,
                    "scraped_at_range": {
                        "min_date": scraped_range_result[0],
                        "max_date": scraped_range_result[1]
                    } if scraped_range_result else None
                }
        except Exception as e:
            logger.error(f"Error getting type link statistics: {str(e)}")
            return {}

    async def get_type_option_statistics(self) -> Dict[str, Any]:
        """Get statistics for CTC type options"""
        try:
            async with get_async_session() as session:
                # Total options
                total_options = await session.scalar(select(func.count(CTCTypeOption.id)))
                
                # Unique source types
                unique_sources = await session.scalar(
                    select(func.count(func.distinct(CTCTypeOption.source_type_id)))
                )
                
                # Unique option types
                unique_options = await session.scalar(
                    select(func.count(func.distinct(CTCTypeOption.option_type_id)))
                )
                
                # Average options per source
                avg_options = await session.scalar(
                    select(func.avg(func.count(CTCTypeOption.id)))
                    .group_by(CTCTypeOption.source_type_id)
                ) or 0.0
                
                # Most common source type
                most_common_source = await session.execute(
                    select(CTCTypeOption.source_type_id, func.count(CTCTypeOption.id).label('count'))
                    .group_by(CTCTypeOption.source_type_id)
                    .order_by(desc('count'))
                    .limit(1)
                )
                most_common_source_result = most_common_source.first()
                
                # Most common option type
                most_common_option = await session.execute(
                    select(CTCTypeOption.option_type_id, func.count(CTCTypeOption.id).label('count'))
                    .group_by(CTCTypeOption.option_type_id)
                    .order_by(desc('count'))
                    .limit(1)
                )
                most_common_option_result = most_common_option.first()
                
                # Scraped at range
                scraped_range = await session.execute(
                    select(
                        func.min(CTCTypeOption.scraped_at).label('min_date'),
                        func.max(CTCTypeOption.scraped_at).label('max_date')
                    )
                )
                scraped_range_result = scraped_range.first()
                
                return {
                    "total_options": total_options or 0,
                    "unique_source_types": unique_sources or 0,
                    "unique_option_types": unique_options or 0,
                    "average_options_per_source": float(avg_options),
                    "most_common_source_type": {
                        "type_id": most_common_source_result[0],
                        "count": most_common_source_result[1]
                    } if most_common_source_result else None,
                    "most_common_option_type": {
                        "type_id": most_common_option_result[0],
                        "count": most_common_option_result[1]
                    } if most_common_option_result else None,
                    "scraped_at_range": {
                        "min_date": scraped_range_result[0],
                        "max_date": scraped_range_result[1]
                    } if scraped_range_result else None
                }
        except Exception as e:
            logger.error(f"Error getting type option statistics: {str(e)}")
            return {}

    # NEW DEAL VALUE TYPE METHODS
    async def get_deal_value_types(self, active_only: bool = True) -> List[DealValueTypeRead]:
        """Get all deal value types"""
        try:
            async with get_async_session() as session:
                query = select(DealValueType)
                if active_only:
                    query = query.where(DealValueType.active == True)
                query = query.order_by(DealValueType.code)
                
                result = await session.execute(query)
                value_types = result.scalars().all()
                
                return [to_schema(value_type, DealValueTypeRead) for value_type in value_types]
        except Exception as e:
            logger.error(f"Error getting deal value types: {str(e)}")
            return []

    async def get_deal_value_type(self, value_type_id: int) -> Optional[DealValueTypeRead]:
        """Get a specific deal value type by ID"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DealValueType).where(DealValueType.id == value_type_id)
                )
                value_type = result.scalar_one_or_none()
                
                if value_type:
                    return DealValueTypeRead.model_validate(value_type)
                return None
        except Exception as e:
            logger.error(f"Error getting deal value type {value_type_id}: {str(e)}")
            return None

    async def get_deal_value_type_by_code(self, code: str) -> Optional[DealValueTypeRead]:
        """Get a deal value type by code"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DealValueType).where(DealValueType.code == code)
                )
                value_type = result.scalar_one_or_none()
                
                if value_type:
                    return to_schema(value_type, DealValueTypeRead)
                return None
        except Exception as e:
            logger.error(f"Error getting deal value type by code {code}: {str(e)}")
            return None

    async def create_deal_value_type(self, data: DealValueTypeCreate) -> DealValueTypeRead:
        """Create a new deal value type"""
        try:
            async with get_async_session() as session:
                value_type = DealValueType(
                    code=data.code,
                    name=data.name,
                    store=data.store,
                    symbol=data.symbol,
                    active=data.active,
                    modified_by=data.modified_by,
                    created_by=data.created_by
                )
                
                session.add(value_type)
                await session.commit()
                await session.refresh(value_type)
                
                return to_schema(value_type, DealValueTypeRead)
        except Exception as e:
            logger.error(f"Error creating deal value type: {str(e)}")
            raise

    async def update_deal_value_type(self, value_type_id: int, data: DealValueTypeUpdate) -> Optional[DealValueTypeRead]:
        """Update a deal value type"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DealValueType).where(DealValueType.id == value_type_id)
                )
                value_type = result.scalar_one_or_none()
                
                if not value_type:
                    return None
                
                # Update fields
                update_data = data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(value_type, field):
                        setattr(value_type, field, value)
                
                value_type.modified_by = data.modified_by
                value_type.modified = datetime.utcnow()
                
                await session.commit()
                await session.refresh(value_type)
                
                return to_schema(value_type, DealValueTypeRead)
        except Exception as e:
            logger.error(f"Error updating deal value type {value_type_id}: {str(e)}")
            return None

    async def delete_deal_value_type(self, value_type_id: int, soft_delete: bool = True) -> bool:
        """Delete a deal value type"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DealValueType).where(DealValueType.id == value_type_id)
                )
                value_type = result.scalar_one_or_none()
                
                if not value_type:
                    return False
                
                if soft_delete:
                    value_type.active = False
                    value_type.deleted_by = "system"
                    value_type.deleted = datetime.utcnow()
                else:
                    await session.delete(value_type)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting deal value type {value_type_id}: {str(e)}")
            return False

    # NEW DEAL CALCULATION METHODS
    async def get_deal_calculations(
        self, 
        rebate_agreement_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        active_only: bool = True
    ) -> List[DealCalculationRead]:
        """Get deal calculations with optional filtering"""
        try:
            async with get_async_session() as session:
                query = select(DealCalculation).options(
                    joinedload(DealCalculation.deal_value_type)
                )
                
                if active_only:
                    query = query.where(DealCalculation.active == True)
                if rebate_agreement_id:
                    query = query.where(DealCalculation.rebate_agreement_id == rebate_agreement_id)
                if product_id:
                    query = query.where(DealCalculation.product_id == product_id)
                if status:
                    query = query.where(DealCalculation.status == status)
                
                query = query.order_by(desc(DealCalculation.calculation_date))
                
                result = await session.execute(query)
                calculations = result.scalars().all()
                
                return [to_schema(calc, DealCalculationRead) for calc in calculations]
        except Exception as e:
            logger.error(f"Error getting deal calculations: {str(e)}")
            return []

    async def get_deal_calculation(self, calculation_id: int) -> Optional[DealCalculationRead]:
        """Get a specific deal calculation by ID"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DealCalculation)
                    .options(joinedload(DealCalculation.deal_value_type))
                    .where(DealCalculation.id == calculation_id)
                )
                calculation = result.scalar_one_or_none()
                
                if calculation:
                    return to_schema(calculation, DealCalculationRead)
                return None
        except Exception as e:
            logger.error(f"Error getting deal calculation {calculation_id}: {str(e)}")
            return None

    async def create_deal_calculation(self, data: DealCalculationCreate) -> DealCalculationRead:
        """Create a new deal calculation"""
        try:
            async with get_async_session() as session:
                calculation = DealCalculation(
                    rebate_agreement_id=data.rebate_agreement_id,
                    product_id=data.product_id,
                    calculation_date=data.calculation_date,
                    quantity_processed=data.quantity_processed,
                    amount_processed=data.amount_processed,
                    deal_value_applied=data.deal_value_applied,
                    deal_value_type_id=data.deal_value_type_id,
                    calculation_method=data.calculation_method,
                    calculation_notes=data.calculation_notes,
                    status=data.status,
                    modified_by=data.modified_by,
                    created_by=data.created_by
                )
                
                session.add(calculation)
                await session.commit()
                await session.refresh(calculation)
                
                # Load the related deal_value_type for the response
                await session.refresh(calculation, ['deal_value_type'])
                
                return to_schema(calculation, DealCalculationRead)
        except Exception as e:
            logger.error(f"Error creating deal calculation: {str(e)}")
            raise

    async def update_deal_calculation(self, calculation_id: int, data: DealCalculationUpdate) -> Optional[DealCalculationRead]:
        """Update a deal calculation"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DealCalculation).where(DealCalculation.id == calculation_id)
                )
                calculation = result.scalar_one_or_none()
                
                if not calculation:
                    return None
                
                # Update fields
                update_data = data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(calculation, field):
                        setattr(calculation, field, value)
                
                calculation.modified_by = data.modified_by
                calculation.modified = datetime.utcnow()
                
                await session.commit()
                await session.refresh(calculation)
                await session.refresh(calculation, ['deal_value_type'])
                
                return to_schema(calculation, DealCalculationRead)
        except Exception as e:
            logger.error(f"Error updating deal calculation {calculation_id}: {str(e)}")
            return None

    async def delete_deal_calculation(self, calculation_id: int, soft_delete: bool = True) -> bool:
        """Delete a deal calculation"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DealCalculation).where(DealCalculation.id == calculation_id)
                )
                calculation = result.scalar_one_or_none()
                
                if not calculation:
                    return False
                
                if soft_delete:
                    calculation.active = False
                    calculation.deleted_by = "system"
                    calculation.deleted = datetime.utcnow()
                else:
                    await session.delete(calculation)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting deal calculation {calculation_id}: {str(e)}")
            return False

    # DEAL ANALYTICS METHODS
    async def get_deal_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for deals and rebate agreements"""
        try:
            async with get_async_session() as session:
                # Total rebate agreements by type
                vendor_agreements = await session.scalar(
                    select(func.count(RebateAgreement.id))
                    .where(RebateAgreement.agreement_type == "vendor")
                ) or 0
                
                customer_agreements = await session.scalar(
                    select(func.count(RebateAgreement.id))
                    .where(RebateAgreement.agreement_type == "customer")
                ) or 0
                
                # Deal calculations by status
                pending_calculations = await session.scalar(
                    select(func.count(DealCalculation.id))
                    .where(DealCalculation.status == "pending")
                ) or 0
                
                approved_calculations = await session.scalar(
                    select(func.count(DealCalculation.id))
                    .where(DealCalculation.status == "approved")
                ) or 0
                
                paid_calculations = await session.scalar(
                    select(func.count(DealCalculation.id))
                    .where(DealCalculation.status == "paid")
                ) or 0
                
                # Deal value types distribution
                value_types_count = await session.scalar(
                    select(func.count(DealValueType.id))
                    .where(DealValueType.active == True)
                ) or 0
                
                # Deal sources and types
                deal_sources_count = await session.scalar(
                    select(func.count(DealSource.id))
                    .where(DealSource.active == True)
                ) or 0
                
                deal_types_count = await session.scalar(
                    select(func.count(DealType.id))
                    .where(DealType.active == True)
                ) or 0
                
                # Recent deal activity (last 30 days)
                recent_calculations = await session.scalar(
                    select(func.count(DealCalculation.id))
                    .where(DealCalculation.created >= datetime.utcnow() - timedelta(days=30))
                ) or 0
                
                # Total deal values
                total_deal_values = await session.scalar(
                    select(func.sum(DealCalculation.deal_value_applied))
                    .where(DealCalculation.status.in_(["approved", "paid"]))
                ) or Decimal("0")
                
                return {
                    "rebate_agreements": {
                        "total": vendor_agreements + customer_agreements,
                        "vendor": vendor_agreements,
                        "customer": customer_agreements
                    },
                    "deal_calculations": {
                        "total": pending_calculations + approved_calculations + paid_calculations,
                        "pending": pending_calculations,
                        "approved": approved_calculations,
                        "paid": paid_calculations
                    },
                    "deal_value_types": {
                        "total": value_types_count
                    },
                    "deal_sources": {
                        "total": deal_sources_count
                    },
                    "deal_types": {
                        "total": deal_types_count
                    },
                    "recent_activity": {
                        "calculations_last_30_days": recent_calculations
                    },
                    "financial_summary": {
                        "total_deal_values": float(total_deal_values)
                    }
                }
        except Exception as e:
            logger.error(f"Error getting deal analytics: {str(e)}")
            return {}

    async def get_deal_calculations_analytics(
        self,
        rebate_agreement_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get analytics for deal calculations with optional filtering"""
        try:
            async with get_async_session() as session:
                # Build base query
                query = select(DealCalculation)
                
                if rebate_agreement_id:
                    query = query.where(DealCalculation.rebate_agreement_id == rebate_agreement_id)
                if product_id:
                    query = query.where(DealCalculation.product_id == product_id)
                if status:
                    query = query.where(DealCalculation.status == status)
                
                # Get calculations by status
                status_counts = await session.execute(
                    select(DealCalculation.status, func.count(DealCalculation.id))
                    .group_by(DealCalculation.status)
                )
                status_distribution = {row[0]: row[1] for row in status_counts.all()}
                
                # Get total values processed
                total_quantity = await session.scalar(
                    select(func.sum(DealCalculation.quantity_processed))
                    .where(query.whereclause) if query.whereclause else select(func.sum(DealCalculation.quantity_processed))
                ) or Decimal("0")
                
                total_amount = await session.scalar(
                    select(func.sum(DealCalculation.amount_processed))
                    .where(query.whereclause) if query.whereclause else select(func.sum(DealCalculation.amount_processed))
                ) or Decimal("0")
                
                total_deal_value = await session.scalar(
                    select(func.sum(DealCalculation.deal_value_applied))
                    .where(query.whereclause) if query.whereclause else select(func.sum(DealCalculation.deal_value_applied))
                ) or Decimal("0")
                
                # Get average deal values
                avg_deal_value = await session.scalar(
                    select(func.avg(DealCalculation.deal_value_applied))
                    .where(query.whereclause) if query.whereclause else select(func.avg(DealCalculation.deal_value_applied))
                ) or Decimal("0")
                
                # Get calculation trends (last 7 days)
                recent_calculations = await session.scalar(
                    select(func.count(DealCalculation.id))
                    .where(DealCalculation.created >= datetime.utcnow() - timedelta(days=7))
                    .where(query.whereclause) if query.whereclause else select(func.count(DealCalculation.id))
                    .where(DealCalculation.created >= datetime.utcnow() - timedelta(days=7))
                ) or 0
                
                return {
                    "status_distribution": status_distribution,
                    "totals": {
                        "quantity_processed": float(total_quantity),
                        "amount_processed": float(total_amount),
                        "deal_value_applied": float(total_deal_value)
                    },
                    "averages": {
                        "deal_value": float(avg_deal_value)
                    },
                    "trends": {
                        "calculations_last_7_days": recent_calculations
                    }
                }
        except Exception as e:
            logger.error(f"Error getting deal calculations analytics: {str(e)}")
            return {}

    async def get_rebate_agreements_by_brand(
        self,
        brand_id: int,
        agreement_type: Optional[str] = None,
        distributor_id: Optional[int] = None,
        status: Optional[str] = None,
        deal_type_id: Optional[int] = None,
        deal_source_id: Optional[int] = None,
        store: Optional[str] = None,
        product_class_id: Optional[int] = None,
        product_type_id: Optional[int] = None,
        product_category_id: Optional[int] = None
    ) -> List[RebateAgreementRead]:
        """Get rebate agreements filtered by brand (via associated products)."""
        async with get_async_session() as session:
            # Join RebateAgreement -> RebateAgreementProduct -> ProductModel
            stmt = select(RebateAgreement).options(
                selectinload(RebateAgreement.products),
                selectinload(RebateAgreement.tiers)
            ).join(RebateAgreement.products).join(RebateAgreementProduct.product).where(ProductModel.brand_id == brand_id)
            if agreement_type:
                stmt = stmt.where(RebateAgreement.agreement_type == agreement_type)
            if distributor_id:
                stmt = stmt.where(RebateAgreement.distributor_id == distributor_id)
            if status:
                stmt = stmt.where(RebateAgreement.status == status)
            if deal_type_id:
                stmt = stmt.where(RebateAgreement.deal_type_id == deal_type_id)
            if deal_source_id:
                stmt = stmt.where(RebateAgreement.deal_source_id == deal_source_id)
            if store:
                stmt = stmt.where(RebateAgreement.store == store)
            if product_class_id:
                stmt = stmt.where(RebateAgreement.product_class_id == product_class_id)
            if product_type_id:
                stmt = stmt.where(RebateAgreement.product_type_id == product_type_id)
            if product_category_id:
                stmt = stmt.where(RebateAgreement.product_category_id == product_category_id)
            agreements = (await session.execute(stmt)).scalars().all()
            return [await self._build_rebate_agreement_response(session, agreement) for agreement in agreements]

    async def get_rebate_agreements_by_product(
        self,
        product_id: int,
        agreement_type: Optional[str] = None,
        distributor_id: Optional[int] = None,
        status: Optional[str] = None,
        deal_type_id: Optional[int] = None,
        deal_source_id: Optional[int] = None,
        store: Optional[str] = None,
        active_only: bool = True
    ) -> List[RebateAgreementRead]:
        """
        Get rebate agreements that apply to a specific product.
        
        This method finds rebates that apply to the product either:
        1. Directly through product association
        2. Through category association (if the product belongs to a category that has rebates)
        
        Args:
            product_id: The ID of the product to search for
            agreement_type: Optional filter by agreement type (vendor/customer)
            distributor_id: Optional filter by distributor
            status: Optional filter by agreement status
            deal_type_id: Optional filter by deal type
            deal_source_id: Optional filter by deal source
            store: Optional filter by store
            active_only: Show only active agreements
            
        Returns:
            List of rebate agreements that apply to the product
        """
        async with get_async_session() as session:
            # First, get the product to find its distributor and categories
            product = await session.get(ProductModel, product_id)
            if not product:
                return []
            
            # Build the base query for rebate agreements
            stmt = select(RebateAgreement).options(
                selectinload(RebateAgreement.products),
                selectinload(RebateAgreement.tiers)
            ).distinct()
            
            # Apply filters
            if agreement_type:
                stmt = stmt.where(RebateAgreement.agreement_type == agreement_type)
            if distributor_id:
                stmt = stmt.where(RebateAgreement.distributor_id == distributor_id)
            if status:
                stmt = stmt.where(RebateAgreement.status == status)
            if deal_type_id:
                stmt = stmt.where(RebateAgreement.deal_type_id == deal_type_id)
            if deal_source_id:
                stmt = stmt.where(RebateAgreement.deal_source_id == deal_source_id)
            if store:
                stmt = stmt.where(RebateAgreement.store == store)
            if active_only:
                stmt = stmt.where(RebateAgreement.status == "active")
            
            # Get product's category IDs
            product_categories = await session.execute(
                select(CTCCategory.id).where(CTCCategory.product_id == product_id)
            )
            category_ids = [cat.id for cat in product_categories.scalars().all()]
            
            # Find agreements that apply to this product either directly or through categories
            # We need to join with RebateAgreementProduct to check both product_id and category_id
            stmt = stmt.join(RebateAgreementProduct).where(
                or_(
                    # Direct product association
                    RebateAgreementProduct.product_id == product_id,
                    # Category association (if product has categories)
                    and_(
                        RebateAgreementProduct.category_id.in_(category_ids),
                        RebateAgreementProduct.category_id.isnot(None)
                    ) if category_ids else False
                )
            )
            
            agreements = (await session.execute(stmt)).scalars().all()
            return [await self._build_rebate_agreement_response(session, agreement) for agreement in agreements]

    async def apply_deals_by_brand(
        self,
        brand_id: int,
        agreement_type: Optional[str] = None,
        distributor_id: Optional[int] = None,
        status: Optional[str] = None,
        deal_type_id: Optional[int] = None,
        deal_source_id: Optional[int] = None,
        store: Optional[str] = None,
        active_only: bool = True
    ) -> List[RebateAgreementRead]:
        """
        Apply deals based on brand through distributor relationships.
        
        This method finds rebate agreements that apply to a brand by:
        1. Finding the brand's distributor
        2. Finding all rebate agreements for that distributor that are brand-type deals
        3. Optionally filtering by other criteria
        
        Args:
            brand_id: The ID of the brand to find deals for
            agreement_type: Optional filter by agreement type (vendor/customer)
            distributor_id: Optional filter by distributor (overrides brand's distributor)
            status: Optional filter by agreement status
            deal_type_id: Optional filter by deal type
            deal_source_id: Optional filter by deal source
            store: Optional filter by store
            active_only: Show only active agreements
            
        Returns:
            List of rebate agreements that apply to the brand
        """
        async with get_async_session() as session:
            # First, get the brand to find its distributor
            brand = await session.get(Brand, brand_id)
            if not brand:
                return []
            
            # Use the brand's distributor unless a specific distributor is requested
            target_distributor_id = distributor_id if distributor_id is not None else brand.distributor_id
            
            # Build the base query for rebate agreements
            stmt = select(RebateAgreement).options(
                selectinload(RebateAgreement.products),
                selectinload(RebateAgreement.tiers)
            ).distinct()
            
            # Apply filters
            if agreement_type:
                stmt = stmt.where(RebateAgreement.agreement_type == agreement_type)
            if target_distributor_id:
                stmt = stmt.where(RebateAgreement.distributor_id == target_distributor_id)
            if status:
                stmt = stmt.where(RebateAgreement.status == status)
            if deal_type_id:
                stmt = stmt.where(RebateAgreement.deal_type_id == deal_type_id)
            if deal_source_id:
                stmt = stmt.where(RebateAgreement.deal_source_id == deal_source_id)
            if store:
                stmt = stmt.where(RebateAgreement.store == store)
            if active_only:
                stmt = stmt.where(RebateAgreement.status == "Current")
            
            # For brand-based deals, we typically want brand rebate deals
            # If no specific deal_type_id is provided, default to brand rebates
            if deal_type_id is None:
                # Get the brand rebate deal type ID
                brand_deal_type = await session.execute(
                    select(DealType).where(DealType.code == "brnd")
                )
                brand_deal_type = brand_deal_type.scalar_one_or_none()
                if brand_deal_type:
                    stmt = stmt.where(RebateAgreement.deal_type_id == brand_deal_type.id)
            
            # Execute the query
            agreements = (await session.execute(stmt)).scalars().all()
            
            # Build the response with product associations
            result = []
            for agreement in agreements:
                # For brand-based deals, we need to associate all products of this brand
                # Get all products for this brand
                brand_products = await session.execute(
                    select(ProductModel.id).where(ProductModel.brand_id == brand_id)
                )
                product_ids = [p.id for p in brand_products.scalars().all()]
                
                # Build the response
                agreement_response = await self._build_rebate_agreement_response(session, agreement)
                
                # Override the products list to include all brand products
                agreement_response.products = product_ids
                
                result.append(agreement_response)
            
            return result

storage = SQLStorage()
