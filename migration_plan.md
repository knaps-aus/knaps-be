# Migration and Restructuring Plan

**Project Context**

- `database.py` already initializes an async SQLAlchemy engine using `create_async_engine` and exposes `AsyncSessionLocal`.
- `db_models.py` contains relational tables such as `Contact` and `Address` with many columns representing address details and contact details separately from `Distributor`.
- `storage.py` implements a monolithic `SQLStorage` class with many async methods for CRUD operations on contacts and addresses, e.g., `get_contact`, `get_address`, `create_address`, etc.

---

## 1. Project Layout Changes

1. **Create a new `repositories/` package**
   - Move domain-specific repository logic from `storage.py` into separate modules.
   - Example structure:
     ```
     src/
       repositories/
         __init__.py
         base.py           # Async SQLAlchemyRepository base class
         product_repo.py
         distributor_repo.py
         contact_repo.py   # Handles jsonb access once migrated
         address_repo.py   # Handles jsonb access once migrated
     ```
2. **Keep `db_models.py` and `database.py` under `src/`**
   - New models will still live in `db_models.py` but with JSONB columns for embedded structures.
3. **Adjust routes/services to import from the new repository modules instead of the old `storage.SQLStorage` class.**
4. **Optionally add a `schemas/` package** for Pydantic models if not already in `models.py`.

---

## 2. Changes to `storage.py`

Replace the monolithic `SQLStorage` class with smaller repository classes following the guide’s pattern.

### `repositories/base.py`

```python
# repositories/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Generic, TypeVar, Type

ModelType = TypeVar("ModelType")

class SQLAlchemyRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get(self, id: int) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def list(self) -> list[ModelType]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars())
```

### Example `contact_repo.py`

```python
# repositories/contact_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from .base import SQLAlchemyRepository
from ..db_models import Distributor
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import JSONB

class ContactRepository(SQLAlchemyRepository[Distributor]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Distributor)

    async def add_contact(self, distributor_id: int, contact_data: dict):
        stmt = (
            update(Distributor)
            .where(Distributor.id == distributor_id)
            .values(
                contacts=Distributor.contacts.concat(JSONB([contact_data]))
            )
            .returning(Distributor)
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.scalar_one()
```

### Patterns

- **Scoped sessions**: open a session in the FastAPI dependency layer (`async_session_maker()` from `database.py`) and pass it into the repository.
- **One repository per model/domain**: e.g., `ProductRepository`, `DistributorRepository`.
- **Use SQLAlchemy Core or ORM with async support**.
- **Return Pydantic schemas using `model_validate()`** when interacting with API layers.

---

## 3. Changes to `db_model.py`

### Before

Contact and address use many individual columns:

```python
class Contact(Base):
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    ...
```

```python
class Address(Base):
    id = Column(Integer, primary_key=True)
    address1 = Column(String)
    city = Column(String)
    ...
```


### After (using JSONB)

```python
from sqlalchemy.dialects.postgresql import JSONB

class Distributor(Base):
    __tablename__ = "distributors"

    id = Column(Integer, primary_key=True)
    ...
    contacts = Column(JSONB, nullable=False, default=list)   # list of contact objects
    addresses = Column(JSONB, nullable=False, default=list)  # list of address objects
```

- Remove the separate `Contact` and `Address` tables.
- Each contact or address is stored as a JSON object (matching a Pydantic schema) inside the distributor row.
- Example JSON structure for contacts:
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "mobile": "555-1234",
    "contact_type": "sales"
  }
  ```
- Pydantic models for validation:

```python
from pydantic import BaseModel, Field

class ContactData(BaseModel):
    name: str
    email: str | None = None
    mobile: str | None = None

class AddressData(BaseModel):
    line1: str
    line2: str | None = None
    city: str | None = None
    postcode: str | None = None
```

- Repositories store and retrieve these dictionaries from JSONB columns.

---

## 4. Migration Strategy

1. **Create new columns on `distributors`**
   ```sql
   ALTER TABLE distributors ADD COLUMN contacts JSONB DEFAULT '[]';
   ALTER TABLE distributors ADD COLUMN addresses JSONB DEFAULT '[]';
   ```

2. **Backfill data**
   - Query existing `Contact` and `Address` rows and group them by `distributor_id`.
   - Convert each row into the JSON format expected by the new columns.
   - Update the corresponding `distributors` row to append JSON arrays.

   Example script (simplified):

   ```python
   async with AsyncSessionLocal() as session:
       distributors = await session.execute(select(Distributor))
       for dist in distributors.scalars():
           contacts = await session.execute(
               select(Contact).where(Contact.distributor_id == dist.id)
           )
           addresses = await session.execute(
               select(Address).where(Address.distributor_id == dist.id)
           )
           dist.contacts = [ContactData.model_validate(c).__dict__ for c in contacts.scalars()]
           dist.addresses = [AddressData.model_validate(a).__dict__ for a in addresses.scalars()]
       await session.commit()
   ```

3. **Remove foreign keys and drop old tables**
   ```sql
   DROP TABLE contacts;
   DROP TABLE addresses;
   ```

4. **Update Pydantic schemas and application logic**
   - Replace `ContactRead`, `AddressRead`, etc., with schemas representing embedded JSON items.
   - Repository methods read/write to JSONB fields using SQLAlchemy’s `JSONB` operators.

5. **Validate migration**
   - Unit tests: ensure retrieving a distributor returns the new JSON structures.
   - Data verification scripts: count original contacts/addresses vs. the number embedded in JSON after migration.

6. **Deployment considerations**
   - Perform the migration in a transaction or via Alembic migration scripts.
   - Ensure backups exist before dropping tables.
   - Temporarily disable API endpoints for contacts/addresses during migration to avoid inconsistent state.

---

## 5. Bonus: Before/After Examples

### Before (`storage.py` contact operations)

```python
class SQLStorage:
    async def create_contact(self, data: ContactCreate) -> ContactRead:
        async with get_async_session() as session:
            contact_data = data.model_dump()
            contact_data['uuid'] = str(uuid.uuid4())
            obj = Contact(**contact_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, ContactRead)
```


### After (`contact_repo.py` using JSONB)

```python
class ContactRepository(SQLAlchemyRepository[Distributor]):
    async def add_contact(self, distributor_id: int, data: ContactData):
        stmt = (
            update(Distributor)
            .where(Distributor.id == distributor_id)
            .values(
                contacts=Distributor.contacts.concat([data.model_dump()])
            )
            .returning(Distributor)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()   # distributor with updated JSONB field
```

### Before (`db_models.py` for contacts/addresses)

Relational columns as shown above.

### After (`db_models.py` excerpt)

```python
class Distributor(Base):
    __tablename__ = "distributors"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String, nullable=False)
    contacts = Column(JSONB, default=list, nullable=False)
    addresses = Column(JSONB, default=list, nullable=False)
```

---

## Summary

1. **Create a dedicated `repositories/` package** with a `SQLAlchemyRepository` base class to handle async database interactions.
2. **Refactor `storage.py`**: split monolithic methods into domain-specific repositories. Each repository will use dependency-injected `AsyncSession` and operate on models or JSONB fields.
3. **Modify `db_models.py`**: embed `contacts` and `addresses` as `JSONB` columns in `Distributor` (or whichever parent table is appropriate), removing the relational `Contact` and `Address` tables.
4. **Migration plan**: add new columns, backfill JSON data from existing tables, drop old tables, update schemas and endpoints, and validate with unit tests.
5. **Example code snippets** above illustrate the transition from relational models and monolithic storage logic to JSONB-based models and modular async repositories.

This restructuring follows the patterns described in the asynchronous repository guide, enabling cleaner repository code, more efficient async data access, and simplified JSON-based storage for addresses and contacts.
