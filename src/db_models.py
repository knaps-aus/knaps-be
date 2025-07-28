from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (Column, Integer, Text, Boolean, String, Numeric, DateTime, Date, ForeignKey, Enum, Index, PrimaryKeyConstraint, UniqueConstraint, JSON)
from sqlalchemy.orm import relationship
import uuid

from .database import Base

### PRODUCT MODELS ###

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String, nullable=False, unique=True)
    distributor_name = Column(Text, nullable=False)
    brand_name = Column(Text, nullable=False)
    product_code = Column(Text, nullable=False, unique=True)
    product_secondary_code = Column(Text)
    product_name = Column(Text, nullable=False)
    description = Column(Text)
    summary = Column(Text)
    shipping_class = Column(Text)
    category_name = Column(Text, nullable=False)
    product_availability = Column(Text, nullable=False, default="In Stock")
    superceded_by = Column(Text)
    replaces = Column(Text)
    status = Column(Text, nullable=False, default="Active")
    online = Column(Boolean, nullable=False, default=True)
    ean = Column(Text)
    pack_size = Column(Integer, nullable=False, default=1)
    core_group = Column(Text)
    tax_exmt = Column(Boolean, nullable=False, default=False)
    hyperlink = Column(Text)
    web_title = Column(Text)
    features_and_benefits_codes = Column(Text)
    badges_codes = Column(Text)
    stock_unmanaged = Column(Boolean, nullable=False, default=False)

    # New fields for fuller product representation
    active = Column(Boolean, nullable=False, default=True)
    purchaser = Column(String, nullable=True)
    icon_owner = Column(String, nullable=True)
    is_gift_card = Column(Boolean, nullable=False, default=False)
    gift_card_limit = Column(Numeric(12, 2), nullable=True)
    has_promotions = Column(Boolean, nullable=False, default=False)
    store = Column(String, nullable=True)
    web_link = Column(Text)
    edit_link = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_by = Column(String, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)

    
    # Relationships
    price_levels = relationship("PriceLevel", back_populates="product", cascade="all, delete-orphan")

    #Brand relationships
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    brand = relationship("Brand", back_populates="products")

    #Distributor relationships
    distributor_id = Column(Integer, ForeignKey("distributors.id", ondelete="CASCADE"), nullable=False)
    distributor = relationship("Distributor", back_populates="products")
    
    # Rebate relationships
    rebate_agreements = relationship("RebateAgreementProduct", back_populates="product")
    rebate_claims = relationship("RebateClaim", back_populates="product")

    # CTC relationships
    ctc_class_id = Column(Integer, ForeignKey("ctc_classes.id"), nullable=True)
    ctc_type_id = Column(Integer, ForeignKey("ctc_types.id"), nullable=True)
    ctc_category_id = Column(Integer, ForeignKey("ctc_categories.id"), nullable=True)
    
    # One-way relationships from CTC levels to products
    ctc_class = relationship("CTCClass", foreign_keys=[ctc_class_id], back_populates="products")
    ctc_type = relationship("CTCType", foreign_keys=[ctc_type_id], back_populates="products")
    ctc_category = relationship("CTCCategory", foreign_keys=[ctc_category_id], back_populates="products")

    
    attribute_values = relationship("ProductAttributeValue", back_populates="product")
    my_price = relationship("MyPrice", back_populates="product", uselist=False, cascade="all, delete-orphan")


class PriceLevel(Base):
    __tablename__ = "price_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price_level = Column(String, nullable=False)  # e.g., "MWP", "Trade", "GO", "RRP"
    type = Column(String, nullable=False)  # e.g., "Standard", "Promotional", "Bulk", etc.
    value_excl = Column(Numeric(12, 4), nullable=False)  # Value excluding tax
    value_incl = Column(Numeric(12, 4), nullable=True)   # Value including tax
    comments = Column(Text, nullable=True)  # Additional comments about this price level

    # Extended pricing information
    active = Column(Boolean, nullable=False, default=True)
    external_id = Column(Integer, nullable=True)
    store = Column(String, nullable=True)
    value_stor = Column(Numeric(12, 4), nullable=True)
    value_stor_incl = Column(Numeric(12, 4), nullable=True)
    value_hoff = Column(Numeric(12, 4), nullable=True)
    value_hoff_incl = Column(Numeric(12, 4), nullable=True)
    valid_start = Column(DateTime, nullable=True)
    valid_end = Column(DateTime, nullable=True)
    claim_start = Column(DateTime, nullable=True)
    claim_end = Column(DateTime, nullable=True)
    bonus_status = Column(String, nullable=True)
    initial_value_stor = Column(Numeric(12, 4), nullable=True)
    initial_value_stor_incl = Column(Numeric(12, 4), nullable=True)
    initial_value_hoff = Column(Numeric(12, 4), nullable=True)
    initial_value_hoff_incl = Column(Numeric(12, 4), nullable=True)
    has_overrides = Column(Boolean, nullable=False, default=False)
    current_override_price = Column(Numeric(12, 4), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)
    modified_by = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)

    # Relationships
    product = relationship("ProductModel", back_populates="price_levels")

    # Ensure unique combination of product, price level, and type
    __table_args__ = (
        # Add a unique constraint to prevent duplicate price levels for the same product
        # You might want to adjust this based on your business logic
    )


### USER MODELS ###

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    keycloak_id   = Column(String, unique=True, index=True)
    email         = Column(String, unique=True, index=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


### CTC MODELS ###

class CTCClass(Base):
    """
    Stores CTC product classes (level 1)
    """
    __tablename__ = "ctc_classes"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    types = relationship("CTCType", back_populates="class_", cascade="all, delete-orphan")
    features_benefits = relationship("ClassFeaturesBenefits", back_populates="class_", cascade="all, delete-orphan")
    type_features_benefits = relationship("TypeFeaturesBenefits", back_populates="class_", cascade="all, delete-orphan")
    category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="class_", cascade="all, delete-orphan")
    products = relationship("ProductModel", foreign_keys="ProductModel.ctc_class_id", back_populates="ctc_class")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_classes_uuid', 'uuid'),
        Index('idx_ctc_classes_code', 'code'),
        Index('idx_ctc_classes_store', 'store'),
    )


class CTCType(Base):
    """
    Stores CTC product types (level 2)
    """
    __tablename__ = "ctc_types"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Foreign key to class
    class_id = Column(
        Integer,
        ForeignKey("ctc_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    class_ = relationship("CTCClass", back_populates="types")
    categories = relationship("CTCCategory", back_populates="type_", cascade="all, delete-orphan")
    features_benefits = relationship("TypeFeaturesBenefits", back_populates="type_", cascade="all, delete-orphan")
    category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="type_", cascade="all, delete-orphan")
    products = relationship("ProductModel", foreign_keys="ProductModel.ctc_type_id", back_populates="ctc_type")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_types_uuid', 'uuid'),
        Index('idx_ctc_types_code', 'code'),
        Index('idx_ctc_types_store', 'store'),
        Index('idx_ctc_types_class_id', 'class_id'),
    )


class CTCCategory(Base):
    """
    Stores CTC product categories (level 3)
    """
    __tablename__ = "ctc_categories"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Foreign key to type
    type_id = Column(
        Integer,
        ForeignKey("ctc_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product association (only for categories at level 3)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True
    )

    # Relationships
    type_ = relationship("CTCType", back_populates="categories")
    products = relationship("ProductModel", foreign_keys="ProductModel.ctc_category_id", back_populates="ctc_category")

    # Attributes for categories (level 3)
    attributes = relationship(
        "CategoryAttribute",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    # CTC attributes for categories (level 3)
    ctc_attributes = relationship(
        "CTCAttribute",
        back_populates="category",
        cascade="all, delete-orphan"
    )
    
    # Features and benefits for categories (level 3)
    features_benefits = relationship(
        "CategoryFeaturesBenefits",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_ctc_categories_uuid', 'uuid'),
        Index('idx_ctc_categories_code', 'code'),
        Index('idx_ctc_categories_store', 'store'),
        Index('idx_ctc_categories_type_id', 'type_id'),
        Index('idx_ctc_categories_product_id', 'product_id'),
    )


class CategoryAttribute(Base):
    __tablename__ = "category_attribute"

    id = Column(Integer, primary_key=True)
    category_id = Column(
        Integer,
        ForeignKey("ctc_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String, nullable=False)
    value = Column(Text, nullable=False)

    category = relationship("CTCCategory", back_populates="attributes")


### CTC ATTRIBUTE MODELS ###

class CTCAttributeGroup(Base):
    """
    Stores attribute groups (e.g., "Key Specifications", "Ungrouped")
    """
    __tablename__ = "ctc_attribute_groups"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    attributes = relationship("CTCAttribute", back_populates="attribute_group")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_attribute_groups_uuid', 'uuid'),
        Index('idx_ctc_attribute_groups_store', 'store'),
    )


class CTCDataType(Base):
    """
    Stores data types (e.g., "Text", "Number", "Boolean")
    """
    __tablename__ = "ctc_data_types"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    attributes = relationship("CTCAttribute", back_populates="data_type")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_data_types_uuid', 'uuid'),
        Index('idx_ctc_data_types_store', 'store'),
    )


class CTCUnitOfMeasure(Base):
    """
    Stores units of measure (e.g., "Litres", "Kilograms", "Meters")
    """
    __tablename__ = "ctc_units_of_measure"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    attributes = relationship("CTCAttribute", back_populates="uom")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_units_of_measure_uuid', 'uuid'),
        Index('idx_ctc_units_of_measure_store', 'store'),
    )


class CTCAttribute(Base):
    """
    Stores individual CTC attributes with their metadata
    """
    __tablename__ = "ctc_attributes"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    rank = Column(Integer, nullable=False, default=0)
    as_filter = Column(Boolean, nullable=False, default=False)
    scraped_at = Column(DateTime, nullable=True)

    # Foreign keys
    category_id = Column(
        Integer,
        ForeignKey("ctc_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attribute_group_id = Column(
        Integer,
        ForeignKey("ctc_attribute_groups.id", ondelete="CASCADE"),
        nullable=False
    )
    data_type_id = Column(
        Integer,
        ForeignKey("ctc_data_types.id", ondelete="CASCADE"),
        nullable=False
    )
    uom_id = Column(
        Integer,
        ForeignKey("ctc_units_of_measure.id", ondelete="CASCADE"),
        nullable=True
    )

    # Relationships
    category = relationship("CTCCategory", back_populates="ctc_attributes")
    attribute_group = relationship("CTCAttributeGroup", back_populates="attributes")
    data_type = relationship("CTCDataType", back_populates="attributes")
    uom = relationship("CTCUnitOfMeasure", back_populates="attributes")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_attributes_uuid', 'uuid'),
        Index('idx_ctc_attributes_category_id', 'category_id'),
        Index('idx_ctc_attributes_store', 'store'),
        Index('idx_ctc_attributes_rank', 'rank'),
    )


class ProductAttributeValue(Base):
    """
    Stores actual attribute values for individual products
    This links products to their specific attribute values
    """
    __tablename__ = "product_attribute_values"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    
    # The actual value for this attribute
    value = Column(Text, nullable=False)
    
    # Foreign keys
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attribute_id = Column(
        Integer,
        ForeignKey("ctc_attributes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    product = relationship("ProductModel", back_populates="attribute_values")
    attribute = relationship("CTCAttribute", back_populates="product_values")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_attribute_values_uuid', 'uuid'),
        Index('idx_product_attribute_values_product_id', 'product_id'),
        Index('idx_product_attribute_values_attribute_id', 'attribute_id'),
        # Ensure one value per product per attribute
        UniqueConstraint('product_id', 'attribute_id', name='uq_product_attribute'),
    )


# Add relationship to ProductModel
ProductModel.attribute_values = relationship("ProductAttributeValue", back_populates="product", cascade="all, delete-orphan")

# Add relationship to CTCAttribute
CTCAttribute.product_values = relationship("ProductAttributeValue", back_populates="attribute", cascade="all, delete-orphan")

# Add relationship to CTCCategory for CTC attributes
CTCCategory.ctc_attributes = relationship("CTCAttribute", back_populates="category", cascade="all, delete-orphan")


### DISTRIBUTOR AND BRAND MODELS ###

class Purchaser(Base):
    """Stores purchaser information"""
    __tablename__ = "purchasers"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    icon_owner = Column(String, nullable=True)
    
    # Relationships
    distributors = relationship("Distributor", back_populates="purchaser")
    
    # Indexes
    __table_args__ = (
        Index('idx_purchasers_uuid', 'uuid'),
        Index('idx_purchasers_code', 'code'),
        Index('idx_purchasers_store', 'store'),
    )


class Contact(Base):
    """Stores contact information for distributors"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    
    # Contact details
    title_code = Column(String, nullable=True)
    title_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    bounced_email = Column(Boolean, nullable=False, default=False)
    no_email = Column(Boolean, nullable=False, default=False)
    landline = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    website = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    
    # Visibility settings
    visible_to_all = Column(Boolean, nullable=False, default=True)
    visible_to_group = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    
    # Denormalized contact type information
    contact_type_code = Column(String, nullable=True)
    contact_type_name = Column(String, nullable=True)
    
    # Foreign keys
    distributor_id = Column(Integer, ForeignKey("distributors.id", ondelete="CASCADE"), nullable=False)
    default_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)
    
    # Relationships
    distributor = relationship("Distributor", back_populates="contacts", foreign_keys=[distributor_id])
    default_address = relationship("Address", foreign_keys=[default_address_id])
    addresses = relationship("Address", back_populates="contact", foreign_keys="Address.contact_id")
    
    # Indexes
    __table_args__ = (
        Index('idx_contacts_distributor_id', 'distributor_id'),
        Index('idx_contacts_default_address_id', 'default_address_id'),
        Index('idx_contacts_contact_type_code', 'contact_type_code'),
    )


class Address(Base):
    """Stores denormalized address information"""
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=True)
    store = Column(String, nullable=False)
    
    # Address details
    address1 = Column(String, nullable=True)
    address2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    gln = Column(String, nullable=True)
    
    # Denormalized address type information
    address_type_code = Column(String, nullable=True)
    address_type_name = Column(String, nullable=True)
    address_type_fa_icon = Column(String, nullable=True)
    
    # Denormalized state information
    state_code = Column(String, nullable=True)
    state_name = Column(String, nullable=True)
    
    # Denormalized postcode information
    postcode_code = Column(String, nullable=True)
    postcode_name = Column(String, nullable=True)
    
    # Denormalized suburb information
    suburb_code = Column(String, nullable=True)
    suburb_name = Column(String, nullable=True)
    
    # Foreign keys
    distributor_id = Column(Integer, ForeignKey("distributors.id", ondelete="CASCADE"), nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True)
    
    # Relationships
    distributor = relationship("Distributor", back_populates="addresses", foreign_keys=[distributor_id])
    contact = relationship("Contact", back_populates="addresses", foreign_keys=[contact_id])
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_addresses_distributor_id', 'distributor_id'),
        Index('idx_addresses_contact_id', 'contact_id'),
        Index('idx_addresses_state_code', 'state_code'),
        Index('idx_addresses_postcode_code', 'postcode_code'),
        Index('idx_addresses_address_type_code', 'address_type_code'),
    )


class Distributor(Base):
    """
    Stores distributor information
    """
    __tablename__ = "distributors"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    edi = Column(Boolean, nullable=False, default=False)
    auto_claim_over_charge = Column(Boolean, nullable=False, default=False)
    is_central = Column(Boolean, nullable=False, default=True)
    icon_owner = Column(String, nullable=True)
    gln = Column(String, nullable=True)
    business_number = Column(String, nullable=True)
    accounting_date = Column(Integer, nullable=True)
    web_portal_url = Column(String, nullable=True)
    pp_claim_from = Column(String, nullable=True)
    fis_minimum_order = Column(String, nullable=True)
    default_extended_credits_code = Column(String, nullable=True)
    default_extended_credits_name = Column(String, nullable=True)
    
    # New fields from the enhanced data
    purchaser_id = Column(Integer, ForeignKey("purchasers.id"), nullable=True)
    source = Column(String, nullable=True)  # 'brands_data', 'api', etc.
    
    # Enhanced contact information
    default_contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    
    # Additional business information
    company_number = Column(String, nullable=True)
    permit_bup = Column(Boolean, nullable=False, default=False)
    intranet_only = Column(Boolean, nullable=False, default=False)
    accounting_only = Column(Boolean, nullable=False, default=False)
    is_head_office = Column(Boolean, nullable=False, default=False)
    
    # Core group information (denormalized)
    core_group_code = Column(String, nullable=True)
    core_group_name = Column(String, nullable=True)
    core_group_rank = Column(Integer, nullable=True)
    
    # Membership information
    membership_code = Column(String, nullable=True)
    membership_name = Column(String, nullable=True)
    
    # Communication settings
    internal_email = Column(String, nullable=True)
    google_place_id = Column(String, nullable=True)
    enable_formatted_emails = Column(Boolean, nullable=False, default=True)

    # Relationships
    purchaser = relationship("Purchaser", back_populates="distributors")
    default_contact = relationship("Contact", foreign_keys=[default_contact_id])
    contacts = relationship("Contact", back_populates="distributor", foreign_keys="Contact.distributor_id")
    addresses = relationship("Address", back_populates="distributor")
    brands = relationship("Brand", back_populates="distributor")
    products = relationship("ProductModel", back_populates="distributor")

    # Indexes
    __table_args__ = (
        Index('idx_distributors_uuid', 'uuid'),
        Index('idx_distributors_code', 'code'),
        Index('idx_distributors_store', 'store'),
        Index('idx_distributors_purchaser_id', 'purchaser_id'),
        Index('idx_distributors_default_contact_id', 'default_contact_id'),
    )


class Brand(Base):
    """
    Stores brand information with relationship to distributors
    """
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    is_hof_pref = Column(Boolean, nullable=False, default=True)
    comments = Column(Text, nullable=True)
    narta_rept = Column(Boolean, nullable=False, default=True)

    # Foreign key to distributor
    distributor_id = Column(
        Integer,
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    distributor = relationship("Distributor", back_populates="brands")
    products = relationship("ProductModel", back_populates="brand")

    # Indexes
    __table_args__ = (
        Index('idx_brands_uuid', 'uuid'),
        Index('idx_brands_code', 'code'),
        Index('idx_brands_store', 'store'),
        Index('idx_brands_distributor_id', 'distributor_id'),
    )


### REBATE MODELS ###

class RebateAgreement(Base):
    __tablename__ = "rebate_agreements"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Existing fields
    agreement_type = Column(Enum("vendor", "customer", name="agreement_types"), nullable=False)
    distributor_id = Column(Integer, nullable=False)
    description = Column(String, nullable=True)  # Changed to nullable=True
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)  # Changed to nullable=True
    calc_frequency = Column(Enum("invoice", "daily", "monthly", "quarterly", "yearly", name="calc_frequencies"), nullable=False)
    basis = Column(Enum("quantity", "amount", name="rebate_bases"), nullable=False)
    rate_type = Column(Enum("percent", "per_unit", "fixed", "percentage", name="rate_types"), nullable=False)
    approval_required = Column(Boolean, default=False, nullable=False)
    status = Column(Enum("active", "expired", "Current", "Expired", name="rebate_statuses"), default="active", nullable=False)

    # NEW FIELDS for scraped deals integration
    # Deal classification
    deal_type_id = Column(Integer, ForeignKey("deal_types.id"), nullable=True)
    deal_value_type_id = Column(Integer, ForeignKey("deal_value_types.id"), nullable=True)
    deal_source_id = Column(Integer, ForeignKey("deal_sources.id"), nullable=True)
    
    # Deal-specific pricing information
    price_level_type_id = Column(Integer, ForeignKey("price_level_types.id"), nullable=True)
    value_stor = Column(Numeric(12, 4), nullable=True)
    value_stor_incl = Column(Numeric(12, 4), nullable=True)
    value_hoff = Column(Numeric(12, 4), nullable=True)
    value_hoff_incl = Column(Numeric(12, 4), nullable=True)
    
    # Deal timing
    valid_start = Column(DateTime, nullable=True)
    valid_end = Column(DateTime, nullable=True)
    claim_start = Column(DateTime, nullable=True)
    claim_end = Column(DateTime, nullable=True)
    
    # Deal status and metadata
    bonus_status_code = Column(String, nullable=True)
    bonus_status_name = Column(String, nullable=True)
    deal_code = Column(String, nullable=True)  # Original deal code from scraped data
    store = Column(String, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_by = Column(String, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)

    
    # CTC Relationships 
    product_class_id = Column(Integer, ForeignKey("ctc_classes.id"), nullable=True)
    product_type_id = Column(Integer, ForeignKey("ctc_types.id"), nullable=True)
    product_category_id = Column(Integer, ForeignKey("ctc_categories.id"), nullable=True)

    # Brand and Product Relationships
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    # Deal specific relationships
    calculated_on_price_level_id = Column(Integer, ForeignKey("price_level_types.id"), nullable=True)

    # Rebate specific relationships
    tiers = relationship(
        "RebateTier", back_populates="agreement", cascade="all, delete-orphan"
    )
    claims = relationship(
        "RebateClaim", back_populates="agreement", cascade="all, delete-orphan"
    )
    products = relationship(
        "RebateAgreementProduct", back_populates="agreement", cascade="all, delete-orphan"
    )

class RebateAgreementProduct(Base):
    __tablename__ = "rebate_agreement_products"

    id = Column(Integer, primary_key=True)
    rebate_agreement_id = Column(
        Integer, ForeignKey("rebate_agreements.id"), nullable=False
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("ctc_categories.id"), nullable=True)

    # Relationships
    agreement = relationship("RebateAgreement", back_populates="products")
    product = relationship("ProductModel", back_populates="rebate_agreements")


class RebateTier(Base):
    __tablename__ = "rebate_tiers"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    rebate_agreement_id = Column(
        Integer, ForeignKey("rebate_agreements.id"), nullable=False
    )
    rebate_agreement_uuid = Column(String, nullable=False)

    # Existing threshold fields
    from_quantity = Column(Numeric, nullable=True)
    to_quantity = Column(Numeric, nullable=True)
    from_amount = Column(Numeric, nullable=True)
    to_amount = Column(Numeric, nullable=True)

    # Existing rebate value fields
    rebate_value = Column(Numeric, nullable=False)
    rebate_unit = Column(Enum("percent", "per_unit", "fixed", name="rebate_units"), nullable=False)

    # NEW FIELDS for deal-specific pricing
    value_type_id = Column(Integer, ForeignKey("deal_value_types.id"), nullable=True)
    calculated_on_price_level_id = Column(Integer, ForeignKey("price_level_types.id"), nullable=True)
    
    # Deal-specific value fields
    value_stor = Column(Numeric(12, 4), nullable=True)
    value_stor_incl = Column(Numeric(12, 4), nullable=True)
    value_hoff = Column(Numeric(12, 4), nullable=True)
    value_hoff_incl = Column(Numeric(12, 4), nullable=True)

    # Relationships (existing)
    agreement = relationship("RebateAgreement", back_populates="tiers")
    
    # NEW RELATIONSHIPS
    value_type = relationship("DealValueType", back_populates="rebate_tiers")
    calculated_on_price_level = relationship("PriceLevelType")


class RebateClaim(Base):
    __tablename__ = "rebate_claims"

    id = Column(Integer, primary_key=True)
    rebate_agreement_id = Column(
        Integer, ForeignKey("rebate_agreements.id"), nullable=False
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    # TODO: Uncomment when invoice_lines table is available
    # invoice_line_id = Column(Integer, ForeignKey("invoice_lines.id"), nullable=True)

    # Existing fields
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    quantity_accumulated = Column(Numeric, nullable=True)
    amount_accumulated = Column(Numeric, nullable=True)
    rebate_amount = Column(Numeric, nullable=False)
    status = Column(Enum("To Calculate", "Pending", "Approved", "Paid", name="claim_statuses"), default="To Calculate", nullable=False)
    calculation_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # NEW FIELDS for deal-specific tracking
    deal_calculation_id = Column(Integer, ForeignKey("deal_calculations.id"), nullable=True)
    applied_deal_value = Column(Numeric(12, 4), nullable=True)
    deal_value_type_id = Column(Integer, ForeignKey("deal_value_types.id"), nullable=True)
    
    # Deal timing tracking
    deal_valid_from = Column(DateTime, nullable=True)
    deal_valid_to = Column(DateTime, nullable=True)
    
    # Relationships (existing)
    agreement = relationship("RebateAgreement", back_populates="claims")
    product = relationship("ProductModel", back_populates="rebate_claims")
    
    # NEW RELATIONSHIPS
    deal_calculation = relationship("DealCalculation", back_populates="rebate_claims")
    deal_value_type = relationship("DealValueType", back_populates="rebate_claims")


class DealValueType(Base):
    """
    Stores deal value types (e.g., "percent", "dollar", "unit")
    """
    __tablename__ = "deal_value_types"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    symbol = Column(String, nullable=True)  # e.g., "%", "$"
    
    # Relationships
    rebate_tiers = relationship("RebateTier", back_populates="value_type")
    rebate_claims = relationship("RebateClaim", back_populates="deal_value_type")
    deal_calculations = relationship("DealCalculation", back_populates="deal_value_type")
    
    # Indexes
    __table_args__ = (
        Index('idx_deal_value_types_uuid', 'uuid'),
        Index('idx_deal_value_types_code', 'code'),
        Index('idx_deal_value_types_store', 'store'),
    )


class DealCalculation(Base):
    """
    Tracks individual deal calculations for audit and analysis
    """
    __tablename__ = "deal_calculations"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    
    # Deal and product references
    rebate_agreement_id = Column(Integer, ForeignKey("rebate_agreements.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Calculation details
    calculation_date = Column(DateTime, nullable=False)
    quantity_processed = Column(Numeric(12, 4), nullable=True)
    amount_processed = Column(Numeric(12, 4), nullable=True)
    deal_value_applied = Column(Numeric(12, 4), nullable=False)
    deal_value_type_id = Column(Integer, ForeignKey("deal_value_types.id"), nullable=False)
    
    # Calculation metadata
    calculation_method = Column(String, nullable=True)  # e.g., "percentage", "fixed_amount"
    calculation_notes = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum("pending", "approved", "rejected", "paid", name="calculation_statuses"), default="pending", nullable=False)
    
    # Relationships
    rebate_agreement = relationship("RebateAgreement")  
    product = relationship("ProductModel")
    deal_value_type = relationship("DealValueType", back_populates="deal_calculations")
    rebate_claims = relationship("RebateClaim", back_populates="deal_calculation")
    
    # Indexes
    __table_args__ = (
        Index('idx_deal_calculations_uuid', 'uuid'),
        Index('idx_deal_calculations_agreement', 'rebate_agreement_id'),
        Index('idx_deal_calculations_product', 'product_id'),
        Index('idx_deal_calculations_date', 'calculation_date'),
        Index('idx_deal_calculations_status', 'status'),
    )


### FEATURES AND BENEFITS MODELS ###

class FeaturesBenefitsBase(Base):
    """
    Base class for features and benefits tables
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    feature_name = Column(String, nullable=False)
    feature_description = Column(Text, nullable=True)
    benefit_name = Column(String, nullable=False)
    benefit_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional fields that might come from the API
    external_id = Column(String, nullable=True, index=True)  # ID from the external system
    external_code = Column(String, nullable=True, index=True)  # Code from the external system
    priority = Column(Integer, nullable=True)  # Priority/order of the feature/benefit
    category = Column(String, nullable=True)  # Category of the feature/benefit
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # Metadata
    scraped_at = Column(DateTime, nullable=True)  # When this was scraped from the API
    source_level = Column(String, nullable=False)  # 'class', 'type', or 'category'
    source_level_id = Column(Integer, nullable=False)  # ID from the source level


class ClassFeaturesBenefits(FeaturesBenefitsBase):
    """
    Features and benefits for CTC Class level
    """
    __tablename__ = "class_features_benefits"
    
    # Foreign key to ctc_classes table
    class_id = Column(
        Integer,
        ForeignKey("ctc_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    class_ = relationship("CTCClass", back_populates="features_benefits")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_class_fb_external', 'external_id', 'source_level_id'),
        Index('idx_class_fb_active', 'is_active', 'class_id'),
    )


class TypeFeaturesBenefits(FeaturesBenefitsBase):
    """
    Features and benefits for CTC Type level
    """
    __tablename__ = "type_features_benefits"
    
    # Foreign keys
    type_id = Column(
        Integer,
        ForeignKey("ctc_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    class_id = Column(
        Integer,
        ForeignKey("ctc_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    type_ = relationship("CTCType", back_populates="features_benefits")
    class_ = relationship("CTCClass", back_populates="type_features_benefits")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_type_fb_external', 'external_id', 'source_level_id'),
        Index('idx_type_fb_active', 'is_active', 'type_id'),
        Index('idx_type_fb_class', 'class_id', 'is_active'),
    )


class CategoryFeaturesBenefits(FeaturesBenefitsBase):
    """
    Features and benefits for CTC Category level
    """
    __tablename__ = "category_features_benefits"
    
    # Foreign keys
    category_id = Column(
        Integer,
        ForeignKey("ctc_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type_id = Column(
        Integer,
        ForeignKey("ctc_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    class_id = Column(
        Integer,
        ForeignKey("ctc_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    category = relationship("CTCCategory", back_populates="features_benefits")
    type_ = relationship("CTCType", back_populates="category_features_benefits")
    class_ = relationship("CTCClass", back_populates="category_features_benefits")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_category_fb_external', 'external_id', 'source_level_id'),
        Index('idx_category_fb_active', 'is_active', 'category_id'),
        Index('idx_category_fb_type', 'type_id', 'is_active'),
        Index('idx_category_fb_class', 'class_id', 'is_active'),
    )


class MyPrice(Base):
    """Aggregated pricing information for a product"""
    __tablename__ = "my_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=False)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)

    go = Column(Numeric(12, 4), nullable=True)
    go_special = Column(Numeric(12, 4), nullable=True)
    rrp = Column(Numeric(12, 4), nullable=True)
    rrp_special = Column(Numeric(12, 4), nullable=True)
    trade = Column(Numeric(12, 4), nullable=True)
    off_invoice = Column(Numeric(12, 4), nullable=True)
    invoice = Column(Numeric(12, 4), nullable=True)
    vendor_percent = Column(Numeric(12, 4), nullable=True)
    vendor_dollar = Column(Numeric(12, 4), nullable=True)
    bonus_percent = Column(Numeric(12, 4), nullable=True)
    bonus_dollar = Column(Numeric(12, 4), nullable=True)
    brand_percent = Column(Numeric(12, 4), nullable=True)
    hoff_percent = Column(Numeric(12, 4), nullable=True)
    hoff_dollar = Column(Numeric(12, 4), nullable=True)
    net = Column(Numeric(12, 4), nullable=True)
    sellthru_dollar = Column(Numeric(12, 4), nullable=True)
    nac = Column(Numeric(12, 4), nullable=True)
    off_invoice_hoff = Column(Numeric(12, 4), nullable=True)
    invoice_hoff = Column(Numeric(12, 4), nullable=True)
    vendor_percent_hoff = Column(Numeric(12, 4), nullable=True)
    vendor_dollar_hoff = Column(Numeric(12, 4), nullable=True)
    bonus_percent_hoff = Column(Numeric(12, 4), nullable=True)
    bonus_dollar_hoff = Column(Numeric(12, 4), nullable=True)
    brand_percent_hoff = Column(Numeric(12, 4), nullable=True)
    net_hoff = Column(Numeric(12, 4), nullable=True)
    sellthru_dollar_hoff = Column(Numeric(12, 4), nullable=True)
    nac_hoff = Column(Numeric(12, 4), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("ProductModel", back_populates="my_price", uselist=False)


### PRICE LEVEL TYPE MODELS ###

class PriceLevelType(Base):
    """
    Stores price level types (e.g., "trade", "invoice", "net", "go", "rrp", "catalogue")
    """
    __tablename__ = "price_level_types"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=False, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    is_incl = Column(Boolean, nullable=False, default=False)
    apply_to_db = Column(Boolean, nullable=False, default=True)
    price_type_code = Column(String, nullable=False)  # "buy" or "sell"
    price_type_name = Column(String, nullable=False)  # "Buy Price" or "Sell Price"
    parent_code = Column(String, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_price_level_types_uuid', 'uuid'),
        Index('idx_price_level_types_code', 'code'),
        Index('idx_price_level_types_store', 'store'),
        Index('idx_price_level_types_price_type', 'price_type_code'),
    )


### DEAL MODELS ###

class DealSource(Base):
    """
    Stores deal sources (e.g., "dist", "hoff", "nart")
    """
    __tablename__ = "deal_sources"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    for_hoff_only = Column(Boolean, nullable=False, default=False)

    # Relationships
    deal_types = relationship("DealType", back_populates="default_provider")

    # Indexes
    __table_args__ = (
        Index('idx_deal_sources_uuid', 'uuid'),
        Index('idx_deal_sources_code', 'code'),
        Index('idx_deal_sources_store', 'store'),
    )


class DealType(Base):
    """
    Stores deal types (e.g., "disc", "hoff", "vend", "prod", "brnd", "sellthru", "ppro", "cmpl")
    """
    __tablename__ = "deal_types"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    rank = Column(Integer, nullable=False, default=1)
    bonus_class = Column(String, nullable=False)
    claimable = Column(Boolean, nullable=False, default=False)
    deductable = Column(Boolean, nullable=False, default=True)

    # Foreign key to deal source
    default_provider_id = Column(
        Integer,
        ForeignKey("deal_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    default_provider = relationship("DealSource", back_populates="deal_types")

    # Indexes
    __table_args__ = (
        Index('idx_deal_types_uuid', 'uuid'),
        Index('idx_deal_types_code', 'code'),
        Index('idx_deal_types_store', 'store'),
        Index('idx_deal_types_rank', 'rank'),
        Index('idx_deal_types_bonus_class', 'bonus_class'),
    )

# === CTC LINK-TYPES MODELS ===

class CTCTypeLink(Base):
    """
    Stores CTC type linking relationships
    Links one product type to another product type
    """
    __tablename__ = "ctc_type_links"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    
    # Source type (the type that has the link)
    source_type_id = Column(Integer, nullable=False, index=True)
    source_type_name = Column(String, nullable=False)
    
    # Target type (the type that is linked to)
    target_type_id = Column(Integer, nullable=False, index=True)
    target_type_name = Column(String, nullable=False)
    
    # Metadata
    scraped_at = Column(DateTime, nullable=False)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_ctc_type_links_source', 'source_type_id'),
        Index('idx_ctc_type_links_target', 'target_type_id'),
        Index('idx_ctc_type_links_scraped', 'scraped_at'),
        UniqueConstraint('source_type_id', 'target_type_id', name='uq_type_link_relationship'),
    )

class CTCTypeOption(Base):
    """
    Stores all available type options for each source type
    This is for reference and analysis purposes
    """
    __tablename__ = "ctc_type_options"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    
    # Source type (the type being queried)
    source_type_id = Column(Integer, nullable=False, index=True)
    source_type_name = Column(String, nullable=False)
    
    # Available option
    option_type_id = Column(Integer, nullable=False, index=True)
    option_type_name = Column(String, nullable=False)
    
    # Metadata
    scraped_at = Column(DateTime, nullable=False)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_ctc_type_options_source', 'source_type_id'),
        Index('idx_ctc_type_options_option', 'option_type_id'),
        Index('idx_ctc_type_options_scraped', 'scraped_at'),
        UniqueConstraint('source_type_id', 'option_type_id', name='uq_type_option_relationship'),
    )