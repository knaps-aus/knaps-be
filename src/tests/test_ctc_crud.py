import pytest
from typing import Dict, Any


class TestCTCClasses:
    """Test CTC Classes CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_class(self, client):
        """Test creating a new CTC class"""
        class_data = {
            "code": "TEST_CLASS",
            "name": "Test Class",
            "store": "test_store"
        }
        
        resp = await client.post("/ctc/classes", json=class_data)
        assert resp.status_code == 200
        created = resp.json()
        
        assert created["code"] == "TEST_CLASS"
        assert created["name"] == "Test Class"
        assert created["store"] == "test_store"
        assert created["active"] is True
        assert "uuid" in created
        assert "id" in created
        
        return created["id"]
    
    @pytest.mark.asyncio
    async def test_get_all_classes(self, client):
        """Test getting all classes"""
        resp = await client.get("/ctc/classes")
        assert resp.status_code == 200
        classes = resp.json()
        assert isinstance(classes, list)
        
        # Test with active_only filter
        resp = await client.get("/ctc/classes", params={"active_only": True})
        assert resp.status_code == 200
        
        resp = await client.get("/ctc/classes", params={"active_only": False})
        assert resp.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_class_by_id(self, client):
        """Test getting class by ID"""
        # First create a class
        class_data = {
            "code": "TEST_CLASS_ID",
            "name": "Test Class ID",
            "store": "test_store"
        }
        create_resp = await client.post("/ctc/classes", json=class_data)
        class_id = create_resp.json()["id"]
        
        # Get by ID
        resp = await client.get(f"/ctc/classes/{class_id}")
        assert resp.status_code == 200
        class_obj = resp.json()
        assert class_obj["id"] == class_id
        assert class_obj["code"] == "TEST_CLASS_ID"
    
    @pytest.mark.asyncio
    async def test_get_class_by_uuid(self, client):
        """Test getting class by UUID"""
        # First create a class
        class_data = {
            "code": "TEST_CLASS_UUID",
            "name": "Test Class UUID",
            "store": "test_store"
        }
        create_resp = await client.post("/ctc/classes", json=class_data)
        class_uuid = create_resp.json()["uuid"]
        
        # Get by UUID
        resp = await client.get(f"/ctc/classes/uuid/{class_uuid}")
        assert resp.status_code == 200
        class_obj = resp.json()
        assert class_obj["uuid"] == class_uuid
    
    @pytest.mark.asyncio
    async def test_get_class_by_code(self, client):
        """Test getting class by code"""
        # First create a class
        class_data = {
            "code": "TEST_CLASS_CODE",
            "name": "Test Class Code",
            "store": "test_store"
        }
        create_resp = await client.post("/ctc/classes", json=class_data)
        
        # Get by code
        resp = await client.get("/ctc/classes/code/TEST_CLASS_CODE")
        assert resp.status_code == 200
        class_obj = resp.json()
        assert class_obj["code"] == "TEST_CLASS_CODE"
    
    @pytest.mark.asyncio
    async def test_update_class(self, client):
        """Test updating a class"""
        # First create a class
        class_data = {
            "code": "TEST_CLASS_UPDATE",
            "name": "Test Class Update",
            "store": "test_store"
        }
        create_resp = await client.post("/ctc/classes", json=class_data)
        class_id = create_resp.json()["id"]
        
        # Update the class
        update_data = {
            "name": "Updated Class Name",
            "code": "UPDATED_CODE"
        }
        resp = await client.put(f"/ctc/classes/{class_id}", json=update_data)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == "Updated Class Name"
        assert updated["code"] == "UPDATED_CODE"
    
    @pytest.mark.asyncio
    async def test_delete_class(self, client):
        """Test deleting a class"""
        # First create a class
        class_data = {
            "code": "TEST_CLASS_DELETE",
            "name": "Test Class Delete",
            "store": "test_store"
        }
        create_resp = await client.post("/ctc/classes", json=class_data)
        class_id = create_resp.json()["id"]
        
        # Delete the class (soft delete)
        resp = await client.delete(f"/ctc/classes/{class_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "CTC class deleted successfully"
        
        # Verify it's not found when getting by ID
        resp = await client.get(f"/ctc/classes/{class_id}")
        assert resp.status_code == 404


class TestCTCTypes:
    """Test CTC Types CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_type(self, client):
        """Test creating a new CTC type"""
        # First create a class
        class_data = {
            "code": "TEST_CLASS_FOR_TYPE",
            "name": "Test Class For Type",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        # Create type
        type_data = {
            "code": "TEST_TYPE",
            "name": "Test Type",
            "store": "test_store",
            "class_id": class_id
        }
        
        resp = await client.post("/ctc/types", json=type_data)
        assert resp.status_code == 200
        created = resp.json()
        
        assert created["code"] == "TEST_TYPE"
        assert created["name"] == "Test Type"
        assert created["class_id"] == class_id
        assert created["active"] is True
        assert "uuid" in created
        assert "id" in created
        
        return created["id"]
    
    @pytest.mark.asyncio
    async def test_get_types_by_class(self, client):
        """Test getting types by class"""
        # First create a class and type
        class_data = {
            "code": "TEST_CLASS_FOR_TYPES",
            "name": "Test Class For Types",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_1",
            "name": "Test Type 1",
            "store": "test_store",
            "class_id": class_id
        }
        await client.post("/ctc/types", json=type_data)
        
        # Get types by class
        resp = await client.get(f"/ctc/types/class/{class_id}")
        assert resp.status_code == 200
        types = resp.json()
        assert isinstance(types, list)
        assert len(types) >= 1
    
    @pytest.mark.asyncio
    async def test_get_type_by_id(self, client):
        """Test getting type by ID"""
        # First create a class and type
        class_data = {
            "code": "TEST_CLASS_FOR_TYPE_ID",
            "name": "Test Class For Type ID",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_ID",
            "name": "Test Type ID",
            "store": "test_store",
            "class_id": class_id
        }
        create_resp = await client.post("/ctc/types", json=type_data)
        type_id = create_resp.json()["id"]
        
        # Get by ID
        resp = await client.get(f"/ctc/types/{type_id}")
        assert resp.status_code == 200
        type_obj = resp.json()
        assert type_obj["id"] == type_id
    
    @pytest.mark.asyncio
    async def test_get_type_by_uuid(self, client):
        """Test getting type by UUID"""
        # First create a class and type
        class_data = {
            "code": "TEST_CLASS_FOR_TYPE_UUID",
            "name": "Test Class For Type UUID",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_UUID",
            "name": "Test Type UUID",
            "store": "test_store",
            "class_id": class_id
        }
        create_resp = await client.post("/ctc/types", json=type_data)
        type_uuid = create_resp.json()["uuid"]
        
        # Get by UUID
        resp = await client.get(f"/ctc/types/uuid/{type_uuid}")
        assert resp.status_code == 200
        type_obj = resp.json()
        assert type_obj["uuid"] == type_uuid
    
    @pytest.mark.asyncio
    async def test_update_type(self, client):
        """Test updating a type"""
        # First create a class and type
        class_data = {
            "code": "TEST_CLASS_FOR_TYPE_UPDATE",
            "name": "Test Class For Type Update",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_UPDATE",
            "name": "Test Type Update",
            "store": "test_store",
            "class_id": class_id
        }
        create_resp = await client.post("/ctc/types", json=type_data)
        type_id = create_resp.json()["id"]
        
        # Update the type
        update_data = {
            "name": "Updated Type Name",
            "code": "UPDATED_TYPE_CODE"
        }
        resp = await client.put(f"/ctc/types/{type_id}", json=update_data)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == "Updated Type Name"
        assert updated["code"] == "UPDATED_TYPE_CODE"
    
    @pytest.mark.asyncio
    async def test_delete_type(self, client):
        """Test deleting a type"""
        # First create a class and type
        class_data = {
            "code": "TEST_CLASS_FOR_TYPE_DELETE",
            "name": "Test Class For Type Delete",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_DELETE",
            "name": "Test Type Delete",
            "store": "test_store",
            "class_id": class_id
        }
        create_resp = await client.post("/ctc/types", json=type_data)
        type_id = create_resp.json()["id"]
        
        # Delete the type
        resp = await client.delete(f"/ctc/types/{type_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "CTC type deleted successfully"


class TestCTCCategories:
    """Test CTC Categories CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_category(self, client):
        """Test creating a new CTC category"""
        # First create a class and type
        class_data = {
            "code": "TEST_CLASS_FOR_CATEGORY",
            "name": "Test Class For Category",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_CATEGORY",
            "name": "Test Type For Category",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        # Create category
        category_data = {
            "code": "TEST_CATEGORY",
            "name": "Test Category",
            "store": "test_store",
            "type_id": type_id
        }
        
        resp = await client.post("/ctc/categories", json=category_data)
        assert resp.status_code == 200
        created = resp.json()
        
        assert created["code"] == "TEST_CATEGORY"
        assert created["name"] == "Test Category"
        assert created["type_id"] == type_id
        assert created["active"] is True
        assert "uuid" in created
        assert "id" in created
        
        return created["id"]
    
    @pytest.mark.asyncio
    async def test_get_categories_by_type(self, client):
        """Test getting categories by type"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_CATEGORIES",
            "name": "Test Class For Categories",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_CATEGORIES",
            "name": "Test Type For Categories",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_1",
            "name": "Test Category 1",
            "store": "test_store",
            "type_id": type_id
        }
        await client.post("/ctc/categories", json=category_data)
        
        # Get categories by type
        resp = await client.get(f"/ctc/categories/type/{type_id}")
        assert resp.status_code == 200
        categories = resp.json()
        assert isinstance(categories, list)
        assert len(categories) >= 1
    
    @pytest.mark.asyncio
    async def test_get_category_by_id(self, client):
        """Test getting category by ID"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_CATEGORY_ID",
            "name": "Test Class For Category ID",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_CATEGORY_ID",
            "name": "Test Type For Category ID",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_ID",
            "name": "Test Category ID",
            "store": "test_store",
            "type_id": type_id
        }
        create_resp = await client.post("/ctc/categories", json=category_data)
        category_id = create_resp.json()["id"]
        
        # Get by ID
        resp = await client.get(f"/ctc/categories/{category_id}")
        assert resp.status_code == 200
        category_obj = resp.json()
        assert category_obj["id"] == category_id
    
    @pytest.mark.asyncio
    async def test_get_category_by_uuid(self, client):
        """Test getting category by UUID"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_CATEGORY_UUID",
            "name": "Test Class For Category UUID",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_CATEGORY_UUID",
            "name": "Test Type For Category UUID",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_UUID",
            "name": "Test Category UUID",
            "store": "test_store",
            "type_id": type_id
        }
        create_resp = await client.post("/ctc/categories", json=category_data)
        category_uuid = create_resp.json()["uuid"]
        
        # Get by UUID
        resp = await client.get(f"/ctc/categories/uuid/{category_uuid}")
        assert resp.status_code == 200
        category_obj = resp.json()
        assert category_obj["uuid"] == category_uuid
    
    @pytest.mark.asyncio
    async def test_get_category_by_code(self, client):
        """Test getting category by code"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_CATEGORY_CODE",
            "name": "Test Class For Category Code",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_CATEGORY_CODE",
            "name": "Test Type For Category Code",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_CODE",
            "name": "Test Category Code",
            "store": "test_store",
            "type_id": type_id
        }
        await client.post("/ctc/categories", json=category_data)
        
        # Get by code
        resp = await client.get("/ctc/categories/code/TEST_CATEGORY_CODE")
        assert resp.status_code == 200
        category_obj = resp.json()
        assert category_obj["code"] == "TEST_CATEGORY_CODE"
    
    @pytest.mark.asyncio
    async def test_update_category(self, client):
        """Test updating a category"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_CATEGORY_UPDATE",
            "name": "Test Class For Category Update",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_CATEGORY_UPDATE",
            "name": "Test Type For Category Update",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_UPDATE",
            "name": "Test Category Update",
            "store": "test_store",
            "type_id": type_id
        }
        create_resp = await client.post("/ctc/categories", json=category_data)
        category_id = create_resp.json()["id"]
        
        # Update the category
        update_data = {
            "name": "Updated Category Name",
            "code": "UPDATED_CATEGORY_CODE"
        }
        resp = await client.put(f"/ctc/categories/{category_id}", json=update_data)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == "Updated Category Name"
        assert updated["code"] == "UPDATED_CATEGORY_CODE"
    
    @pytest.mark.asyncio
    async def test_delete_category(self, client):
        """Test deleting a category"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_CATEGORY_DELETE",
            "name": "Test Class For Category Delete",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_CATEGORY_DELETE",
            "name": "Test Type For Category Delete",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_DELETE",
            "name": "Test Category Delete",
            "store": "test_store",
            "type_id": type_id
        }
        create_resp = await client.post("/ctc/categories", json=category_data)
        category_id = create_resp.json()["id"]
        
        # Delete the category
        resp = await client.delete(f"/ctc/categories/{category_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "CTC category deleted successfully"


class TestCTCAttributes:
    """Test CTC Attributes CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_attribute_group(self, client):
        """Test creating an attribute group"""
        group_data = {
            "code": "TEST_GROUP",
            "name": "Test Attribute Group",
            "store": "test_store"
        }
        
        resp = await client.post("/ctc/attribute-groups", json=group_data)
        assert resp.status_code == 200
        created = resp.json()
        
        assert created["code"] == "TEST_GROUP"
        assert created["name"] == "Test Attribute Group"
        assert created["active"] is True
        assert "id" in created
        
        return created["id"]
    
    @pytest.mark.asyncio
    async def test_create_data_type(self, client):
        """Test creating a data type"""
        data_type_data = {
            "code": "TEST_DATA_TYPE",
            "name": "Test Data Type",
            "store": "test_store"
        }
        
        resp = await client.post("/ctc/data-types", json=data_type_data)
        assert resp.status_code == 200
        created = resp.json()
        
        assert created["code"] == "TEST_DATA_TYPE"
        assert created["name"] == "Test Data Type"
        assert created["active"] is True
        assert "id" in created
        
        return created["id"]
    
    @pytest.mark.asyncio
    async def test_create_unit_of_measure(self, client):
        """Test creating a unit of measure"""
        uom_data = {
            "code": "TEST_UOM",
            "name": "Test Unit of Measure",
            "store": "test_store"
        }
        
        resp = await client.post("/ctc/units-of-measure", json=uom_data)
        assert resp.status_code == 200
        created = resp.json()
        
        assert created["code"] == "TEST_UOM"
        assert created["name"] == "Test Unit of Measure"
        assert created["active"] is True
        assert "id" in created
        
        return created["id"]
    
    @pytest.mark.asyncio
    async def test_create_attribute(self, client):
        """Test creating a new CTC attribute"""
        # First create required dependencies
        group_id = await self.test_create_attribute_group(client)
        data_type_id = await self.test_create_data_type(client)
        uom_id = await self.test_create_unit_of_measure(client)
        
        # Create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_ATTRIBUTE",
            "name": "Test Class For Attribute",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_ATTRIBUTE",
            "name": "Test Type For Attribute",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_FOR_ATTRIBUTE",
            "name": "Test Category For Attribute",
            "store": "test_store",
            "type_id": type_id
        }
        category_resp = await client.post("/ctc/categories", json=category_data)
        category_id = category_resp.json()["id"]
        
        # Create attribute
        attribute_data = {
            "name": "Test Attribute",
            "store": "test_store",
            "category_id": category_id,
            "attribute_group_id": group_id,
            "data_type_id": data_type_id,
            "uom_id": uom_id,
            "rank": 1,
            "as_filter": True
        }
        
        resp = await client.post("/ctc/attributes", json=attribute_data)
        assert resp.status_code == 200
        created = resp.json()
        
        assert created["name"] == "Test Attribute"
        assert created["category_id"] == category_id
        assert created["attribute_group_id"] == group_id
        assert created["data_type_id"] == data_type_id
        assert created["uom_id"] == uom_id
        assert created["rank"] == 1
        assert created["as_filter"] is True
        assert created["active"] is True
        assert "uuid" in created
        assert "id" in created
        
        return created["id"]
    
    @pytest.mark.asyncio
    async def test_get_attributes_by_category(self, client):
        """Test getting attributes by category"""
        # First create an attribute
        attribute_id = await self.test_create_attribute(client)
        
        # Get the category ID from the attribute
        resp = await client.get(f"/ctc/attributes/{attribute_id}")
        category_id = resp.json()["category_id"]
        
        # Get attributes by category
        resp = await client.get(f"/ctc/categories/{category_id}/attributes")
        assert resp.status_code == 200
        attributes = resp.json()
        assert isinstance(attributes, list)
        assert len(attributes) >= 1
    
    @pytest.mark.asyncio
    async def test_get_attribute_by_id(self, client):
        """Test getting attribute by ID"""
        # First create an attribute
        attribute_id = await self.test_create_attribute(client)
        
        # Get by ID
        resp = await client.get(f"/ctc/attributes/{attribute_id}")
        assert resp.status_code == 200
        attribute_obj = resp.json()
        assert attribute_obj["id"] == attribute_id
    
    @pytest.mark.asyncio
    async def test_get_attribute_by_uuid(self, client):
        """Test getting attribute by UUID"""
        # First create an attribute
        attribute_id = await self.test_create_attribute(client)
        
        # Get the UUID
        resp = await client.get(f"/ctc/attributes/{attribute_id}")
        attribute_uuid = resp.json()["uuid"]
        
        # Get by UUID
        resp = await client.get(f"/ctc/attributes/uuid/{attribute_uuid}")
        assert resp.status_code == 200
        attribute_obj = resp.json()
        assert attribute_obj["uuid"] == attribute_uuid
    
    @pytest.mark.asyncio
    async def test_update_attribute(self, client):
        """Test updating an attribute"""
        # First create an attribute
        attribute_id = await self.test_create_attribute(client)
        
        # Update the attribute
        update_data = {
            "name": "Updated Attribute Name",
            "rank": 2,
            "as_filter": False
        }
        resp = await client.put(f"/ctc/attributes/{attribute_id}", json=update_data)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == "Updated Attribute Name"
        assert updated["rank"] == 2
        assert updated["as_filter"] is False
    
    @pytest.mark.asyncio
    async def test_delete_attribute(self, client):
        """Test deleting an attribute"""
        # First create an attribute
        attribute_id = await self.test_create_attribute(client)
        
        # Delete the attribute
        resp = await client.delete(f"/ctc/attributes/{attribute_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "CTC attribute deleted successfully"


class TestCTCHierarchyAndSearch:
    """Test CTC Hierarchy and Search operations"""
    
    @pytest.mark.asyncio
    async def test_get_full_hierarchy(self, client):
        """Test getting full hierarchy"""
        resp = await client.get("/ctc/hierarchy")
        assert resp.status_code == 200
        hierarchy = resp.json()
        assert isinstance(hierarchy, list)
    
    @pytest.mark.asyncio
    async def test_search_ctc(self, client):
        """Test searching CTC items"""
        resp = await client.get("/ctc/search", params={"search_term": "test"})
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        
        # Test with level filter
        resp = await client.get("/ctc/search", params={"search_term": "test", "level": 1})
        assert resp.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, client):
        """Test getting CTC statistics"""
        resp = await client.get("/ctc/statistics")
        assert resp.status_code == 200
        stats = resp.json()
        assert "classes" in stats
        assert "types" in stats
        assert "categories" in stats
        assert "attributes" in stats
    
    @pytest.mark.asyncio
    async def test_get_consolidated_hierarchy(self, client):
        """Test getting consolidated hierarchy"""
        resp = await client.get("/ctc/hierarchy/consolidated")
        assert resp.status_code == 200
        hierarchy = resp.json()
        assert "level" in hierarchy
        assert "data" in hierarchy


class TestCTCProductRelationships:
    """Test CTC Product Relationship operations"""
    
    @pytest.mark.asyncio
    async def test_assign_product_to_category(self, client):
        """Test assigning product to category"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_PRODUCT",
            "name": "Test Class For Product",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_PRODUCT",
            "name": "Test Type For Product",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_FOR_PRODUCT",
            "name": "Test Category For Product",
            "store": "test_store",
            "type_id": type_id
        }
        category_resp = await client.post("/ctc/categories", json=category_data)
        category_id = category_resp.json()["id"]
        
        # Create a test product
        product_data = {
            "distributor_name": "test_dist",
            "brand_name": "test_brand",
            "product_code": "TEST_PRODUCT",
            "product_name": "Test Product",
            "category_name": "test_category",
            "price_levels": [
                {
                    "price_level": "Trade",
                    "type": "Standard",
                    "value_excl": 10.0,
                    "value_incl": 11.0
                }
            ]
        }
        product_resp = await client.post("/products", json=product_data)
        product_id = product_resp.json()["id"]
        
        # Assign product to category
        resp = await client.post(f"/ctc/categories/{category_id}/products/{product_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Product assigned to category successfully"
    
    @pytest.mark.asyncio
    async def test_get_products_by_category(self, client):
        """Test getting products by category"""
        # First create a class, type, and category
        class_data = {
            "code": "TEST_CLASS_FOR_PRODUCTS",
            "name": "Test Class For Products",
            "store": "test_store"
        }
        class_resp = await client.post("/ctc/classes", json=class_data)
        class_id = class_resp.json()["id"]
        
        type_data = {
            "code": "TEST_TYPE_FOR_PRODUCTS",
            "name": "Test Type For Products",
            "store": "test_store",
            "class_id": class_id
        }
        type_resp = await client.post("/ctc/types", json=type_data)
        type_id = type_resp.json()["id"]
        
        category_data = {
            "code": "TEST_CATEGORY_FOR_PRODUCTS",
            "name": "Test Category For Products",
            "store": "test_store",
            "type_id": type_id
        }
        category_resp = await client.post("/ctc/categories", json=category_data)
        category_id = category_resp.json()["id"]
        
        # Get products by category
        resp = await client.get(f"/ctc/categories/{category_id}/products")
        assert resp.status_code == 200
        products = resp.json()
        assert isinstance(products, list)
    
    @pytest.mark.asyncio
    async def test_get_categories_by_product(self, client):
        """Test getting categories by product"""
        # Create a test product
        product_data = {
            "distributor_name": "test_dist",
            "brand_name": "test_brand",
            "product_code": "TEST_PRODUCT_CATEGORIES",
            "product_name": "Test Product Categories",
            "category_name": "test_category",
            "price_levels": [
                {
                    "price_level": "Trade",
                    "type": "Standard",
                    "value_excl": 10.0,
                    "value_incl": 11.0
                }
            ]
        }
        product_resp = await client.post("/products", json=product_data)
        product_id = product_resp.json()["id"]
        
        # Get categories by product
        resp = await client.get(f"/ctc/products/{product_id}/categories")
        assert resp.status_code == 200
        categories = resp.json()
        assert isinstance(categories, list)


class TestCTCErrorHandling:
    """Test CTC Error Handling"""
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_class(self, client):
        """Test getting a non-existent class"""
        resp = await client.get("/ctc/classes/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_class(self, client):
        """Test updating a non-existent class"""
        update_data = {"name": "Updated Name"}
        resp = await client.put("/ctc/classes/99999", json=update_data)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_class(self, client):
        """Test deleting a non-existent class"""
        resp = await client.delete("/ctc/classes/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_type_with_invalid_class_id(self, client):
        """Test creating a type with invalid class ID"""
        type_data = {
            "code": "TEST_TYPE_INVALID",
            "name": "Test Type Invalid",
            "store": "test_store",
            "class_id": 99999  # Invalid class ID
        }
        resp = await client.post("/ctc/types", json=type_data)
        assert resp.status_code == 500  # Should fail due to foreign key constraint
    
    @pytest.mark.asyncio
    async def test_create_category_with_invalid_type_id(self, client):
        """Test creating a category with invalid type ID"""
        category_data = {
            "code": "TEST_CATEGORY_INVALID",
            "name": "Test Category Invalid",
            "store": "test_store",
            "type_id": 99999  # Invalid type ID
        }
        resp = await client.post("/ctc/categories", json=category_data)
        assert resp.status_code == 500  # Should fail due to foreign key constraint 