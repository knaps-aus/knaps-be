# Brands and Distributors Import

This document describes how to import brands and distributors data from `brands_data.json` into the database.

## Overview

The import system consists of:

1. **Database Models**: `Distributor` and `Brand` models in `src/db_models.py`
2. **Import Script**: `src/brands_init.py` - Core import logic
3. **Standalone Script**: `import_brands.py` - Easy-to-use import script
4. **Test Script**: `test_brands_models.py` - Verify models work correctly

## Database Models

### Distributor Model
Stores distributor information with fields:
- Basic info: `id`, `code`, `name`, `store`
- Metadata: `active`, `modified_by`, `modified`, `created_by`, `created`
- Business info: `edi`, `auto_claim_over_charge`, `is_central`
- Contact info: `gln`, `business_number`, `web_portal_url`
- Settings: `accounting_date`, `fis_minimum_order`, `default_extended_credits`

### Brand Model
Stores brand information with relationship to distributors:
- Basic info: `id`, `code`, `name`, `store`
- Metadata: `active`, `modified_by`, `modified`, `created_by`, `created`
- Business info: `is_hof_pref`, `comments`, `narta_rept`
- Relationship: `distributor_id` (foreign key to Distributor)

## Usage

### Option 1: Standalone Import Script (Recommended)

```bash
python import_brands.py
```

This script will:
1. Initialize the database connection
2. Import all brands and distributors from `distributor/brands_data.json`
3. Display a summary of the import results

### Option 2: Programmatic Import

```python
from src.database import init_db
from src.brands_init import initialize_brands_data, get_brands_summary

# Initialize database
await init_db(drop_existing=False)

# Import brands data
success = await initialize_brands_data()

# Get summary
summary = await get_brands_summary()
```

### Option 3: Database Initialization with Brands

```python
from src.database import init_db

# Initialize database and load brands data
await init_db(drop_existing=False, load_brands_data=True)
```

## Testing

To test that the models work correctly:

```bash
python test_brands_models.py
```

This will create test data and verify the relationships work properly.

## Data Structure

The `brands_data.json` file contains an array of brand objects, each with:

```json
{
  "id": 1,
  "code": "Electrolux",
  "name": "Electrolux",
  "store": "QHOF",
  "is_hof_pref": true,
  "distributor": {
    "id": 1,
    "code": "ehp",
    "name": "Electrolux Home Products",
    "store": "QHOF",
    "edi": false,
    "auto_claim_over_charge": true,
    "is_central": true,
    "GLN": "9377778038100",
    "business_number": "1",
    "accounting_date": 31,
    "default_extended_credits": {
      "code": "30",
      "name": "30 Days"
    }
  },
  "comments": "",
  "narta_rept": true
}
```

## Import Features

- **Duplicate Handling**: Skips existing distributors and brands
- **Relationship Management**: Properly links brands to distributors
- **Error Handling**: Continues processing even if individual records fail
- **Statistics**: Provides detailed import statistics
- **Transaction Safety**: Uses database transactions for data integrity

## File Locations

- `data_management/data/brands_data.json` - Source data file
- `src/db_models.py` - Database models
- `src/brands_init.py` - Import logic
- `import_brands.py` - Standalone import script
- `test_brands_models.py` - Test script

## Troubleshooting

### Common Issues

1. **File not found**: Ensure `distributor/brands_data.json` exists
2. **Database connection**: Check database configuration in `src/config.py`
3. **Permission errors**: Ensure write access to the database
4. **Duplicate key errors**: The import handles duplicates automatically

### Logging

The import process logs detailed information. Check the console output for:
- Number of distributors and brands processed
- Any errors during import
- Summary statistics

## Database Schema

After import, you'll have two new tables:

### distributors
- Primary key: `id`
- Unique constraint: `code`
- Indexes on: `uuid`, `code`, `store`

### brands
- Primary key: `id`
- Unique constraint: `code`
- Foreign key: `distributor_id` references `distributors.id`
- Indexes on: `uuid`, `code`, `store`, `distributor_id` 