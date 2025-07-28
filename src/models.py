from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, Union, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID, uuid4


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# Auth models
class Org(ORMBase):
    org_name: str
    org_id: int
    org_uuid: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

class Store(ORMBase):
    store_name: str
    store_id: int
    store_uuid: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    level: Optional[Literal['superadmin', 'admin', 'user']] = None
    org: Optional[Org] = None
    store: Optional[Store] = None
    created_at: datetime
    updated_at: datetime
    
class Token(ORMBase):
    access_token: str
    token_type: str

# Price Level models
class PriceLevel(ORMBase):
    id: Optional[int] = None
    uuid: Optional[str] = None
    product_id: Optional[int] = None  # Foreign key to product
    price_level: str  # Literal["MWP", "Trade", "GO", "RRP"]  # Price level type
    type: str  # e.g., "Standard", "Promotional", "Bulk", etc.
    value_excl: Decimal  # Value excluding tax
    value_incl: Optional[Decimal] = None  # Value including tax
    comments: Optional[str] = None  # Additional comments about this price level
    valid_start: Optional[datetime] = None  # When this price level becomes valid
    valid_end: Optional[datetime] = None  # When this price level expires
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MyPrice(ORMBase):
    """Aggregated pricing information for a product"""
    id: Optional[int] = None
    uuid: Optional[str] = None
    product_id: Optional[int] = None
    active: Optional[bool] = None
    
    # Basic pricing fields
    go: Optional[Decimal] = None
    go_special: Optional[Decimal] = None
    rrp: Optional[Decimal] = None
    rrp_special: Optional[Decimal] = None
    trade: Optional[Decimal] = None
    off_invoice: Optional[Decimal] = None
    invoice: Optional[Decimal] = None
    
    # Percentage and dollar amounts
    vendor_percent: Optional[Decimal] = None
    vendor_dollar: Optional[Decimal] = None
    bonus_percent: Optional[Decimal] = None
    bonus_dollar: Optional[Decimal] = None
    brand_percent: Optional[Decimal] = None
    hoff_percent: Optional[Decimal] = None
    hoff_dollar: Optional[Decimal] = None
    net: Optional[Decimal] = None
    sellthru_dollar: Optional[Decimal] = None
    nac: Optional[Decimal] = None
    
    # Hoff-specific fields
    off_invoice_hoff: Optional[Decimal] = None
    invoice_hoff: Optional[Decimal] = None
    vendor_percent_hoff: Optional[Decimal] = None
    vendor_dollar_hoff: Optional[Decimal] = None
    bonus_percent_hoff: Optional[Decimal] = None
    bonus_dollar_hoff: Optional[Decimal] = None
    brand_percent_hoff: Optional[Decimal] = None
    net_hoff: Optional[Decimal] = None
    sellthru_dollar_hoff: Optional[Decimal] = None
    nac_hoff: Optional[Decimal] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

class InsertPriceLevel(ORMBase):
    price_level: str
    type: str
    value_excl: Decimal
    value_incl: Optional[Decimal] = None
    comments: Optional[str] = None

# Product models
class InsertProduct(ORMBase):
    distributor_name: str
    brand_name: str
    product_code: str
    product_secondary_code: Optional[str] = None
    product_name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    shipping_class: Optional[str] = None
    category_name: str
    product_availability: str = 'In Stock'
    status: str = 'Active'
    online: bool = True
    superceded_by: Optional[str] = None
    ean: Optional[str] = None
    pack_size: int = 1
    price_levels: List[InsertPriceLevel] = []
    core_group: Optional[str] = None
    tax_exmt: bool = False
    hyperlink: Optional[str] = None
    web_title: Optional[str] = None
    features_and_benefits_codes: Optional[str] = None
    badges_codes: Optional[str] = None
    stock_unmanaged: bool = False
    # CTC relationships
    ctc_class_id: Optional[int] = None
    ctc_type_id: Optional[int] = None
    ctc_category_id: Optional[int] = None

# Rebate models

class RebateTierCreate(ORMBase):
    rebate_agreement_uuid: Optional[str] = None
    from_quantity: Optional[float] = None
    to_quantity: Optional[float] = None  # None if open-ended
    from_amount: Optional[float] = None
    to_amount: Optional[float] = None  # None if open-ended
    rebate_value: float         # percent or per-unit amount
    rebate_unit: Literal["percent", "per_unit", "fixed"]
    
    # NEW FIELDS for deals
    value_type_id: Optional[int] = None
    calculated_on_price_level_id: Optional[int] = None
    value_stor: Optional[Decimal] = None
    value_stor_incl: Optional[Decimal] = None
    value_hoff: Optional[Decimal] = None
    value_hoff_incl: Optional[Decimal] = None

class RebateTierRead(ORMBase):
    id: int
    uuid: str
    agreement_id: int
    rebate_agreement_uuid: str
    from_quantity: Optional[float] = None
    to_quantity: Optional[float] = None  # None if open-ended
    from_amount: Optional[float] = None
    to_amount: Optional[float] = None  # None if open-ended
    rebate_value: float         # percent or per-unit amount
    rebate_unit: Literal["percent", "per_unit", "fixed"]
    
    # NEW FIELDS for deals
    value_type_id: Optional[int] = None
    calculated_on_price_level_id: Optional[int] = None
    value_stor: Optional[Decimal] = None
    value_stor_incl: Optional[Decimal] = None
    value_hoff: Optional[Decimal] = None
    value_hoff_incl: Optional[Decimal] = None

class RebateAgreementCreate(ORMBase):
    agreement_type: Literal["vendor", "customer"]
    distributor_id: int  # vendor ID or customer ID 
    description: Optional[str] = None  # Changed to Optional
    start_date: date
    end_date: Optional[date] = None  # Changed to Optional
    calc_frequency: Literal["invoice", "daily", "monthly", "quarterly", "yearly"]  # Added 'daily', kept 'invoice'
    basis: Literal["quantity", "amount"] 
    rate_type: Literal["percent", "per_unit", "fixed", "percentage"]
    approval_required: bool = False
    products: List[int] = []           # product IDs this agreement applies to
    product_category_ids: List[int] = []  # alternatively or additionally, categories
    tiers: List[RebateTierCreate] = []  # tier definitions (if any)
    # NEW FIELDS for deals
    deal_type_id: Optional[int] = None
    deal_source_id: Optional[int] = None
    price_level_type_id: Optional[int] = None
    value_stor: Optional[Decimal] = None
    value_stor_incl: Optional[Decimal] = None
    value_hoff: Optional[Decimal] = None
    value_hoff_incl: Optional[Decimal] = None
    valid_start: Optional[datetime] = None
    valid_end: Optional[datetime] = None
    claim_start: Optional[datetime] = None
    claim_end: Optional[datetime] = None
    bonus_status_code: Optional[str] = None
    bonus_status_name: Optional[str] = None
    deal_code: Optional[str] = None
    store: Optional[str] = None
    # NEW FIELDS for CTC/brand/product relationships
    product_class_id: Optional[int] = None
    product_type_id: Optional[int] = None
    product_category_id: Optional[int] = None
    brand_id: Optional[int] = None
    product_id: Optional[int] = None
    deal_calculation_id: Optional[int] = None
    deal_value_type_id: Optional[int] = None
    calculated_on_price_level_id: Optional[int] = None

class RebateAgreementRead(ORMBase):
    id: int
    uuid: Optional[str] = None
    agreement_type: str 
    distributor_id: int 
    description: Optional[str] = None  # Changed to Optional
    start_date: date 
    end_date: Optional[date] = None  # Changed to Optional
    calc_frequency: str 
    basis: str 
    rate_type: str 
    approval_required: bool 
    products: List[int] 
    product_category_ids: List[int] 
    tiers: List[RebateTierRead] 
    status: Literal["active", "expired", "Current", "Expired"]
    deal_type_id: Optional[int] = None
    deal_source_id: Optional[int] = None
    price_level_type_id: Optional[int] = None
    value_stor: Optional[Decimal] = None
    value_stor_incl: Optional[Decimal] = None
    value_hoff: Optional[Decimal] = None
    value_hoff_incl: Optional[Decimal] = None
    valid_start: Optional[datetime] = None
    valid_end: Optional[datetime] = None
    claim_start: Optional[datetime] = None
    claim_end: Optional[datetime] = None
    bonus_status_code: Optional[str] = None
    bonus_status_name: Optional[str] = None
    deal_code: Optional[str] = None
    store: Optional[str] = None

    # CTC Based Relationship Filters 
    product_class_id: Optional[int] = None
    product_class_name: Optional[str] = None
    product_type_id: Optional[int] = None
    product_type_name: Optional[str] = None
    product_category_id: Optional[int] = None
    product_category_name: Optional[str] = None
    
    #  Brand / Distributor
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    distributor_id: Optional[int] = None
    distributor_name: Optional[str] = None

    # Product Filter 
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    # deal_calculation_id: Optional[int] = None
    deal_value_type_id: Optional[int] = None
    calculated_on_price_level_id: Optional[int] = None


# NEW MODELS FOR DEAL VALUE TYPES AND CALCULATIONS

class DealValueTypeCreate(ORMBase):
    """Model for creating a new deal value type"""
    code: str
    name: str
    store: str
    symbol: Optional[str] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class DealValueTypeRead(ORMBase):
    """Model for reading deal value type data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    symbol: Optional[str] = None
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None


class DealValueTypeUpdate(ORMBase):
    """Model for updating deal value type data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    symbol: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class DealCalculationCreate(ORMBase):
    """Model for creating a new deal calculation"""
    rebate_agreement_id: int
    product_id: int
    calculation_date: datetime
    quantity_processed: Optional[Decimal] = None
    amount_processed: Optional[Decimal] = None
    deal_value_applied: Decimal
    deal_value_type_id: int
    calculation_method: Optional[str] = None
    calculation_notes: Optional[str] = None
    status: Literal["pending", "approved", "rejected", "paid"] = "pending"
    modified_by: str = "system"
    created_by: str = "system"


class DealCalculationRead(ORMBase):
    """Model for reading deal calculation data"""
    id: int
    uuid: str
    rebate_agreement_id: int
    product_id: int
    calculation_date: datetime
    quantity_processed: Optional[Decimal] = None
    amount_processed: Optional[Decimal] = None
    deal_value_applied: Decimal
    deal_value_type: DealValueTypeRead
    calculation_method: Optional[str] = None
    calculation_notes: Optional[str] = None
    status: str
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None


class DealCalculationUpdate(ORMBase):
    """Model for updating deal calculation data"""
    quantity_processed: Optional[Decimal] = None
    amount_processed: Optional[Decimal] = None
    deal_value_applied: Optional[Decimal] = None
    deal_value_type_id: Optional[int] = None
    calculation_method: Optional[str] = None
    calculation_notes: Optional[str] = None
    status: Optional[Literal["pending", "approved", "rejected", "paid"]] = None
    modified_by: str = "system"


# Analytics types
class ProductAnalytics(ORMBase):
    product_id: int
    product_name: str
    product_code: str
    brand_name: str
    turnover_rate: float
    total_revenue: Decimal
    current_stock: int

class OverallAnalytics(ORMBase):
    average_turnover_rate: float
    total_revenue: Decimal
    total_products: int
    active_products: int
    total_brands: int
    total_categories: int
    total_distributors: int

# Distributor models
class PurchaserCreate(ORMBase):
    """Model for creating a new purchaser"""
    code: str
    name: str
    store: str
    icon_owner: Optional[str] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"

class PurchaserRead(ORMBase):
    """Model for reading purchaser data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    icon_owner: Optional[str] = None
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None

class PurchaserUpdate(ORMBase):
    """Model for updating purchaser data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    icon_owner: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"

class ContactCreate(ORMBase):
    """Model for creating a new contact"""
    code: str
    name: str
    store: str
    distributor_id: int
    title_code: Optional[str] = None
    title_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    bounced_email: bool = False
    no_email: bool = False
    landline: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    comment: Optional[str] = None
    visible_to_all: bool = True
    visible_to_group: bool = True
    is_default: bool = False
    contact_type_code: Optional[str] = None
    contact_type_name: Optional[str] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"

class ContactRead(ORMBase):
    """Model for reading contact data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    distributor_id: int
    title_code: Optional[str] = None
    title_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    bounced_email: bool
    no_email: bool
    landline: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    comment: Optional[str] = None
    visible_to_all: bool
    visible_to_group: bool
    is_default: bool
    contact_type_code: Optional[str] = None
    contact_type_name: Optional[str] = None
    default_address_id: Optional[int] = None
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None

class ContactUpdate(ORMBase):
    """Model for updating contact data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    distributor_id: Optional[int] = None
    title_code: Optional[str] = None
    title_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    bounced_email: Optional[bool] = None
    no_email: Optional[bool] = None
    landline: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    comment: Optional[str] = None
    visible_to_all: Optional[bool] = None
    visible_to_group: Optional[bool] = None
    is_default: Optional[bool] = None
    contact_type_code: Optional[str] = None
    contact_type_name: Optional[str] = None
    default_address_id: Optional[int] = None
    active: Optional[bool] = None
    modified_by: str = "system"

class AddressCreate(ORMBase):
    """Model for creating a new address"""
    code: str
    name: Optional[str] = None
    store: str
    distributor_id: Optional[int] = None
    contact_id: Optional[int] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_default: bool = False
    gln: Optional[str] = None
    address_type_code: Optional[str] = None
    address_type_name: Optional[str] = None
    address_type_fa_icon: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    postcode_code: Optional[str] = None
    postcode_name: Optional[str] = None
    suburb_code: Optional[str] = None
    suburb_name: Optional[str] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"

class AddressRead(ORMBase):
    """Model for reading address data"""
    id: int
    uuid: str
    code: str
    name: Optional[str] = None
    store: str
    distributor_id: Optional[int] = None
    contact_id: Optional[int] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_default: bool
    gln: Optional[str] = None
    address_type_code: Optional[str] = None
    address_type_name: Optional[str] = None
    address_type_fa_icon: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    postcode_code: Optional[str] = None
    postcode_name: Optional[str] = None
    suburb_code: Optional[str] = None
    suburb_name: Optional[str] = None
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None

class AddressUpdate(ORMBase):
    """Model for updating address data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    distributor_id: Optional[int] = None
    contact_id: Optional[int] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_default: Optional[bool] = None
    gln: Optional[str] = None
    address_type_code: Optional[str] = None
    address_type_name: Optional[str] = None
    address_type_fa_icon: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    postcode_code: Optional[str] = None
    postcode_name: Optional[str] = None
    suburb_code: Optional[str] = None
    suburb_name: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"

class DistributorCreate(ORMBase):
    """Model for creating a new distributor"""
    code: str
    name: str
    store: str
    edi: bool = False
    auto_claim_over_charge: bool = False
    is_central: bool = True
    icon_owner: Optional[str] = None
    gln: Optional[str] = None
    business_number: Optional[str] = None
    accounting_date: Optional[int] = None
    web_portal_url: Optional[str] = None
    pp_claim_from: Optional[str] = None
    fis_minimum_order: Optional[str] = None
    default_extended_credits_code: Optional[str] = None
    default_extended_credits_name: Optional[str] = None
    purchaser_id: Optional[int] = None
    source: Optional[str] = None
    default_contact_id: Optional[int] = None
    company_number: Optional[str] = None
    permit_bup: bool = False
    intranet_only: bool = False
    accounting_only: bool = False
    is_head_office: bool = False
    core_group_code: Optional[str] = None
    core_group_name: Optional[str] = None
    core_group_rank: Optional[int] = None
    membership_code: Optional[str] = None
    membership_name: Optional[str] = None
    internal_email: Optional[str] = None
    google_place_id: Optional[str] = None
    enable_formatted_emails: bool = True
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class DistributorRead(ORMBase):
    """Model for reading distributor data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    edi: bool
    auto_claim_over_charge: bool
    is_central: bool
    icon_owner: Optional[str] = None
    gln: Optional[str] = None
    business_number: Optional[str] = None
    accounting_date: Optional[int] = None
    web_portal_url: Optional[str] = None
    pp_claim_from: Optional[str] = None
    fis_minimum_order: Optional[str] = None
    default_extended_credits_code: Optional[str] = None
    default_extended_credits_name: Optional[str] = None
    purchaser_id: Optional[int] = None
    purchaser: Optional[PurchaserRead] = None
    source: Optional[str] = None
    default_contact_id: Optional[int] = None
    default_contact: Optional[ContactRead] = None
    company_number: Optional[str] = None
    permit_bup: bool
    intranet_only: bool
    accounting_only: bool
    is_head_office: bool
    core_group_code: Optional[str] = None
    core_group_name: Optional[str] = None
    core_group_rank: Optional[int] = None
    membership_code: Optional[str] = None
    membership_name: Optional[str] = None
    internal_email: Optional[str] = None
    google_place_id: Optional[str] = None
    enable_formatted_emails: bool
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None

class DistributorUpdate(ORMBase):
    """Model for updating distributor data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    edi: Optional[bool] = None
    auto_claim_over_charge: Optional[bool] = None
    is_central: Optional[bool] = None
    icon_owner: Optional[str] = None
    gln: Optional[str] = None
    business_number: Optional[str] = None
    accounting_date: Optional[int] = None
    web_portal_url: Optional[str] = None
    pp_claim_from: Optional[str] = None
    fis_minimum_order: Optional[str] = None
    default_extended_credits_code: Optional[str] = None
    default_extended_credits_name: Optional[str] = None
    purchaser_id: Optional[int] = None
    source: Optional[str] = None
    default_contact_id: Optional[int] = None
    company_number: Optional[str] = None
    permit_bup: Optional[bool] = None
    intranet_only: Optional[bool] = None
    accounting_only: Optional[bool] = None
    is_head_office: Optional[bool] = None
    core_group_code: Optional[str] = None
    core_group_name: Optional[str] = None
    core_group_rank: Optional[int] = None
    membership_code: Optional[str] = None
    membership_name: Optional[str] = None
    internal_email: Optional[str] = None
    google_place_id: Optional[str] = None
    enable_formatted_emails: Optional[bool] = None
    active: Optional[bool] = None
    modified_by: str = "system"

# Brand models
class BrandCreate(ORMBase):
    """Model for creating a new brand"""
    code: str
    name: str
    store: str
    distributor_id: int
    is_hof_pref: bool = True
    comments: Optional[str] = None
    narta_rept: bool = True
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"

class BrandRead(ORMBase):
    """Model for reading brand data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    distributor_id: int
    is_hof_pref: bool
    comments: Optional[str] = None
    narta_rept: bool
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None

class BrandUpdate(ORMBase):
    """Model for updating brand data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    distributor_id: Optional[int] = None
    is_hof_pref: Optional[bool] = None
    comments: Optional[str] = None
    narta_rept: Optional[bool] = None
    active: Optional[bool] = None
    modified_by: str = "system"


#####


### CTC MODELS ###

# CTC Models
class CTCBase(ORMBase):
    """Base model for CTC entities"""
    id: Optional[int] = None
    uuid: Optional[str] = None
    active: bool = True
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None
    code: str
    name: str
    store: str


class CTCClassCreate(ORMBase):
    """Model for creating a new CTC class"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCClassRead(CTCBase):
    """Model for reading CTC class data"""
    pass


class CTCClassUpdate(ORMBase):
    """Model for updating CTC class data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCTypeCreate(ORMBase):
    """Model for creating a new CTC type"""
    code: str
    name: str
    store: str
    class_id: int
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCTypeRead(CTCBase):
    """Model for reading CTC type data"""
    class_id: int


class CTCTypeUpdate(ORMBase):
    """Model for updating CTC type data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    class_id: Optional[int] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCCategoryCreate(ORMBase):
    """Model for creating a new CTC category"""
    code: str
    name: str
    store: str
    type_id: int
    product_id: Optional[int] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCCategoryRead(CTCBase):
    """Model for reading CTC category data"""
    type_id: int
    product_id: Optional[int] = None


class Product(ORMBase):
    id: Optional[int] = None
    uuid: Optional[str] = None  # Optional UUID field for updates
    distributor_id: Optional[int] = None
    distributor_name: Optional[str] = None
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    product_code: Optional[str] = None
    product_secondary_code: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    shipping_class: Optional[str] = None
    category_name: Optional[str] = None
    product_availability: Optional[str] = None
    status: Optional[str] = None
    online: Optional[bool] = None
    superceded_by: Optional[str] = None
    ean: Optional[str] = None
    pack_size: Optional[int] = None
    price_levels: Optional[List[PriceLevel]] = None
    my_price: Optional[MyPrice] = None
    core_group: Optional[str] = None
    tax_exmt: Optional[bool] = None
    hyperlink: Optional[str] = None
    web_title: Optional[str] = None
    features_and_benefits_codes: Optional[str] = None
    badges_codes: Optional[str] = None
    stock_unmanaged: Optional[bool] = None
    brand: Optional[BrandRead] = None
    distributor: Optional[DistributorRead] = None
    ctc_class: Optional[CTCClassRead] = None
    ctc_type: Optional[CTCTypeRead] = None
    ctc_category: Optional[CTCCategoryRead] = None
    # CTC relationship IDs
    ctc_class_id: Optional[int] = None
    ctc_type_id: Optional[int] = None
    ctc_category_id: Optional[int] = None


###
class CategoryAttributeSchema(ORMBase):
    id: Optional[int]
    name: str
    unit: Optional[str] = None
    value: str


class ProductCategorySchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    product_type_id: int
    attributes: List[CategoryAttributeSchema] = []

    class Config:
        orm_mode = True


class ProductTypeSchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    product_class_id: int
    categories: List[ProductCategorySchema] = []


class ProductClassSchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    types: List[ProductTypeSchema] = []


### FEATURES AND BENEFITS MODELS ###

class FeaturesBenefitsBase(ORMBase):
    """Base model for features and benefits"""
    id: Optional[int] = None
    feature_name: str
    feature_description: Optional[str] = None
    benefit_name: str
    benefit_description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    external_id: Optional[str] = None
    external_code: Optional[str] = None
    priority: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    scraped_at: Optional[datetime] = None
    source_level: str  # 'class', 'type', or 'category'
    source_level_id: int


class ClassFeaturesBenefitsCreate(FeaturesBenefitsBase):
    """Create model for class features and benefits"""
    class_id: int


class ClassFeaturesBenefitsRead(FeaturesBenefitsBase):
    """Read model for class features and benefits"""
    class_id: int


class ClassFeaturesBenefitsUpdate(ORMBase):
    """Update model for class features and benefits"""
    feature_name: Optional[str] = None
    feature_description: Optional[str] = None
    benefit_name: Optional[str] = None
    benefit_description: Optional[str] = None
    is_active: Optional[bool] = None
    external_id: Optional[str] = None
    external_code: Optional[str] = None
    priority: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    scraped_at: Optional[datetime] = None


class TypeFeaturesBenefitsCreate(FeaturesBenefitsBase):
    """Create model for type features and benefits"""
    type_id: int
    class_id: int


class TypeFeaturesBenefitsRead(FeaturesBenefitsBase):
    """Read model for type features and benefits"""
    type_id: int
    class_id: int


class TypeFeaturesBenefitsUpdate(ORMBase):
    """Update model for type features and benefits"""
    feature_name: Optional[str] = None
    feature_description: Optional[str] = None
    benefit_name: Optional[str] = None
    benefit_description: Optional[str] = None
    is_active: Optional[bool] = None
    external_id: Optional[str] = None
    external_code: Optional[str] = None
    priority: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    scraped_at: Optional[datetime] = None


class CategoryFeaturesBenefitsCreate(FeaturesBenefitsBase):
    """Create model for category features and benefits"""
    category_id: int
    type_id: int
    class_id: int


class CategoryFeaturesBenefitsRead(FeaturesBenefitsBase):
    """Read model for category features and benefits"""
    category_id: int
    type_id: int
    class_id: int


class CategoryFeaturesBenefitsUpdate(ORMBase):
    """Update model for category features and benefits"""
    feature_name: Optional[str] = None
    feature_description: Optional[str] = None
    benefit_name: Optional[str] = None
    benefit_description: Optional[str] = None
    is_active: Optional[bool] = None
    external_id: Optional[str] = None
    external_code: Optional[str] = None
    priority: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    scraped_at: Optional[datetime] = None


class CTCCategoryUpdate(ORMBase):
    """Model for updating CTC category data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    type_id: Optional[int] = None
    product_id: Optional[int] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCAttributeGroupCreate(ORMBase):
    """Model for creating a new CTC attribute group"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCAttributeGroupRead(CTCBase):
    """Model for reading CTC attribute group data"""
    pass


class CTCAttributeGroupUpdate(ORMBase):
    """Model for updating CTC attribute group data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCDataTypeCreate(ORMBase):
    """Model for creating a new CTC data type"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCDataTypeRead(CTCBase):
    """Model for reading CTC data type data"""
    pass


class CTCDataTypeUpdate(ORMBase):
    """Model for updating CTC data type data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCUnitOfMeasureCreate(ORMBase):
    """Model for creating a new CTC unit of measure"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCUnitOfMeasureRead(CTCBase):
    """Model for reading CTC unit of measure data"""
    pass


class CTCUnitOfMeasureUpdate(ORMBase):
    """Model for updating CTC unit of measure data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCAttributeCreate(ORMBase):
    """Model for creating a new CTC attribute"""
    name: str
    store: str
    category_id: int
    attribute_group_id: int
    data_type_id: int
    uom_id: Optional[int] = None
    rank: int = 0
    as_filter: bool = False
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCAttributeRead(ORMBase):
    """Model for reading CTC attribute data"""
    id: int
    uuid: str
    name: str
    store: str
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None
    category_id: int
    attribute_group_id: int
    data_type_id: int
    uom_id: Optional[int] = None
    rank: int
    as_filter: bool
    scraped_at: Optional[datetime] = None


class CTCAttributeUpdate(ORMBase):
    """Model for updating CTC attribute data"""
    name: Optional[str] = None
    store: Optional[str] = None
    category_id: Optional[int] = None
    attribute_group_id: Optional[int] = None
    data_type_id: Optional[int] = None
    uom_id: Optional[int] = None
    rank: Optional[int] = None
    as_filter: Optional[bool] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CategoryAttributeCreate(ORMBase):
    """Model for creating a new category attribute"""
    category_id: int
    name: str
    value: str


class CategoryAttributeRead(ORMBase):
    """Model for reading category attribute data"""
    category_id: int
    name: str
    value: str


class CategoryAttributeUpdate(ORMBase):
    """Model for updating category attribute data"""
    name: Optional[str] = None
    value: Optional[str] = None


# CTC Hierarchy Models
class CTCCategoryHierarchy(ORMBase):
    """Model for CTC category in hierarchy"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    product_id: Optional[int] = None


class CTCTypeHierarchy(ORMBase):
    """Model for CTC type in hierarchy"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    categories: List[CTCCategoryHierarchy] = []


class CTCClassHierarchy(ORMBase):
    """Model for CTC class in hierarchy"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    types: List[CTCTypeHierarchy] = []


# CTC Search Models
class CTCSearchResult(ORMBase):
    """Model for CTC search results"""
    level: int
    type: str  # 'class', 'type', or 'category'
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    class_id: Optional[int] = None
    type_id: Optional[int] = None
    product_id: Optional[int] = None


# CTC Statistics Models
class CTCStatistics(ORMBase):
    """Model for CTC statistics"""
    classes: Dict[str, int]
    types: Dict[str, int]
    categories: Dict[str, int]
    attributes: Dict[str, int]


# CTC Attribute Detail Models
class CTCAttributeGroupDetail(ORMBase):
    """Model for attribute group details"""
    id: int
    name: str
    code: str


class CTCDataTypeDetail(ORMBase):
    """Model for data type details"""
    id: int
    name: str
    code: str


class CTCUnitOfMeasureDetail(ORMBase):
    """Model for unit of measure details"""
    id: int
    name: str
    code: str


class CTCAttributeDetail(ORMBase):
    """Model for CTC attribute details"""
    id: int
    uuid: str
    name: str
    rank: int
    as_filter: bool
    active: bool
    attribute_group: CTCAttributeGroupDetail
    data_type: CTCDataTypeDetail
    unit_of_measure: Optional[CTCUnitOfMeasureDetail] = None


class SimpleAttributeDetail(ORMBase):
    """Model for simple attribute details"""
    id: int
    name: str
    value: str


class CTCCategoryWithAttributes(ORMBase):
    """Model for category with all its attributes"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    type_id: int
    product_id: Optional[int] = None
    ctc_attributes: List[CTCAttributeDetail] = []
    simple_attributes: List[SimpleAttributeDetail] = []


class ProductCTCCategoryRead(ORMBase):
    id: int
    uuid: str
    code: str
    name: str
    type_id: int
    type_code: str
    type_name: str
    class_id: int
    class_code: str
    class_name: str


class ProductCTCHierarchy(ORMBase):
    class_id: int
    class_code: str
    class_name: str
    type_id: int
    type_code: str
    type_name: str
    category_id: int
    category_code: str
    category_name: str


class AssignProductToCategoryRequest(ORMBase):
    category_id: int


# CTC Consolidated Hierarchy Response Models
class ConsolidatedHierarchyResponse(ORMBase):
    """Model for consolidated hierarchy endpoint response"""
    level: str  # "classes", "types", or "categories"
    parent_class_uuid: Optional[str] = None
    parent_type_uuid: Optional[str] = None
    data: List[Union[CTCClassRead, CTCTypeRead, CTCCategoryRead]]


class FuzzyMatchInfo(ORMBase):
    is_fuzzy: bool
    field: str  # 'brand' or 'distributor'
    input_value: str
    matched_value: str
    similarity: float

class ProductCreateResult(ORMBase):
    product: Optional[Product] = None
    fuzzy_matches: List[FuzzyMatchInfo] = []
    error: Optional[str] = None

class BulkProductCreateResult(ORMBase):
    created: List[ProductCreateResult] = []
    failed: List[ProductCreateResult] = []


### PRICE LEVEL TYPE MODELS ###

class PriceLevelTypeCreate(ORMBase):
    """Model for creating a new price level type"""
    code: str
    name: str
    store: str
    is_incl: bool = False
    apply_to_db: bool = True
    price_type_code: str  # "buy" or "sell"
    price_type_name: str  # "Buy Price" or "Sell Price"
    parent_code: Optional[str] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class PriceLevelTypeRead(ORMBase):
    """Model for reading price level type data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    is_incl: bool
    apply_to_db: bool
    price_type_code: str
    price_type_name: str
    parent_code: Optional[str] = None
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None


class PriceLevelTypeUpdate(ORMBase):
    """Model for updating price level type data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    is_incl: Optional[bool] = None
    apply_to_db: Optional[bool] = None
    price_type_code: Optional[str] = None
    price_type_name: Optional[str] = None
    parent_code: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


### DEAL SOURCE MODELS ###

class DealSourceCreate(ORMBase):
    """Model for creating a new deal source"""
    code: str
    name: str
    store: str
    for_hoff_only: bool = False
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class DealSourceRead(ORMBase):
    """Model for reading deal source data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    for_hoff_only: bool
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None


class DealSourceUpdate(ORMBase):
    """Model for updating deal source data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    for_hoff_only: Optional[bool] = None
    active: Optional[bool] = None
    modified_by: str = "system"


### DEAL TYPE MODELS ###

class DealTypeCreate(ORMBase):
    """Model for creating a new deal type"""
    code: str
    name: str
    store: str
    rank: int = 1
    bonus_class: str
    claimable: bool = False
    deductable: bool = True
    default_provider_id: Optional[int] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class DealTypeRead(ORMBase):
    """Model for reading deal type data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    rank: int
    bonus_class: str
    claimable: bool
    deductable: bool
    default_provider_id: Optional[int] = None
    default_provider: Optional[DealSourceRead] = None
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None


class DealTypeUpdate(ORMBase):
    """Model for updating deal type data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    rank: Optional[int] = None
    bonus_class: Optional[str] = None
    claimable: Optional[bool] = None
    deductable: Optional[bool] = None
    default_provider_id: Optional[int] = None
    active: Optional[bool] = None
    modified_by: str = "system"


# CTC Link-Types Models
class CTCTypeLinkCreate(ORMBase):
    """Model for creating a new CTC type link"""
    source_type_id: int
    source_type_name: str
    target_type_id: int
    target_type_name: str
    scraped_at: datetime
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCTypeLinkRead(ORMBase):
    """Model for reading CTC type link data"""
    id: int
    uuid: str
    source_type_id: int
    source_type_name: str
    target_type_id: int
    target_type_name: str
    scraped_at: datetime
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime


class CTCTypeOptionCreate(ORMBase):
    """Model for creating a new CTC type option"""
    source_type_id: int
    source_type_name: str
    option_type_id: int
    option_type_name: str
    scraped_at: datetime
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCTypeOptionRead(ORMBase):
    """Model for reading CTC type option data"""
    id: int
    uuid: str
    source_type_id: int
    source_type_name: str
    option_type_id: int
    option_type_name: str
    scraped_at: datetime
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime


# CTC Link-Types Query Models
class CTCTypeLinkQuery(ORMBase):
    """Model for querying CTC type links"""
    source_type_id: Optional[int] = None
    target_type_id: Optional[int] = None
    active: Optional[bool] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class CTCTypeOptionQuery(ORMBase):
    """Model for querying CTC type options"""
    source_type_id: Optional[int] = None
    option_type_id: Optional[int] = None
    active: Optional[bool] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


# CTC Link-Types Response Models
class CTCTypeLinkResponse(ORMBase):
    """Model for CTC type link API response"""
    success: bool
    data: Optional[CTCTypeLinkRead] = None
    message: Optional[str] = None


class CTCTypeLinksResponse(ORMBase):
    """Model for CTC type links list API response"""
    success: bool
    data: List[CTCTypeLinkRead] = []
    total: int
    limit: int
    offset: int
    message: Optional[str] = None


class CTCTypeOptionResponse(ORMBase):
    """Model for CTC type option API response"""
    success: bool
    data: Optional[CTCTypeOptionRead] = None
    message: Optional[str] = None


class CTCTypeOptionsResponse(ORMBase):
    """Model for CTC type options list API response"""
    success: bool
    data: List[CTCTypeOptionRead] = []
    total: int
    limit: int
    offset: int
    message: Optional[str] = None


# CTC Link-Types Statistics Models
class CTCTypeLinkStatistics(ORMBase):
    """Model for CTC type link statistics"""
    total_links: int
    unique_source_types: int
    unique_target_types: int
    most_linked_source_type: Optional[Dict[str, Any]] = None
    most_linked_target_type: Optional[Dict[str, Any]] = None
    average_links_per_source: float
    scraped_at_range: Optional[Dict[str, datetime]] = None


class CTCTypeOptionStatistics(ORMBase):
    """Model for CTC type option statistics"""
    total_options: int
    unique_source_types: int
    unique_option_types: int
    most_common_source_type: Optional[Dict[str, Any]] = None
    most_common_option_type: Optional[Dict[str, Any]] = None
    average_options_per_source: float
    scraped_at_range: Optional[Dict[str, datetime]] = None

