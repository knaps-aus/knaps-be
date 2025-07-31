# PostgreSQL-Backed Async Record Repository — Implementation Guide

This document provides a step-by-step breakdown of how to build and extend an asynchronous PostgreSQL-backed record repository using SQLAlchemy, SQLModel, and Pydantic.

---

## ✅ Overview of the Current Stack

| Layer              | Tooling Used                        |
|-------------------|-------------------------------------|
| ORM + Validation  | `sqlmodel` (SQLAlchemy + Pydantic)  |
| Async Postgres    | `sqlalchemy.ext.asyncio + asyncpg` |
| JSON Fields       | PostgreSQL `JSONB` columns          |
| Logging           | `loguru` with SQLAlchemy bridge     |
| Repository Layer  | Async CRUD pattern                  |
| Record Execution     | Demo in `main.py` (can be swapped with background task or queue) |

---

## 🧭 Step-by-Step Implementation Plan

### 🔹 Step 1: Install Required Dependencies

```bash
pip install sqlmodel sqlalchemy asyncpg pydantic loguru
```

---

### 🔹 Step 2: Define the Record Model

Use SQLModel with Enum and JSONB:

```python
class Record(SQLModel, table=True):
    ...
    record_spec: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
```

#### ✅ Conditional Structure

- **Known nested structure**:
    ```python
    class RecordSpec(BaseModel):
        file_path: str
        embedding_service: str
        ...
    ```

- **Flexible/unknown schema**:
    Use `Dict[str, Any]` and store as `JSONB`.

---

### 🔹 Step 3: Setup the Async Engine and Session

```python
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)
```

#### ✅ For heavy loads:

```python
create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)
```

---

### 🔹 Step 4: Initialize Schema

```python
async with engine.begin() as conn:
    await conn.run_sync(lambda conn: SQLModel.metadata.create_all(conn))
```

---

### 🔹 Step 5: Build the Repository Layer

Leverage the async session for:
- `insert_record`
- `select_record`
- `update_record_status`
- `mark_record_*` methods

---

### 🔹 Step 6: Setup Logging

Use Loguru with SQLAlchemy bridge:

```python
setup_sqlalchemy_loguru_logging(level="INFO")
```

---

### 🔹 Step 7: Record Execution Logic

Use demo from `main.py`:

```python
record = Record(record_type=..., record_spec={...})
await repo.insert_record(record)
await repo.update_record_status(record.id, RecordStatusEnum.RUNNING)
```

#### ✅ For production:

Use FastAPI or a background loop/queue:
```python
while True:
    record = await repo.select_next_record_by_type_and_service(...)
    ...
```

---

### 🔹 Step 8: Advanced Extensions

- Add audit logs: `audit: Dict[str, Any]`
- Add record chaining: `parent_record_id`
- Add retry/failure logic
- Enforce stricter record spec schemas

---

## ⚙️ Conditional Structure Table

| Use Case                | Recommendation                                      |
|-------------------------|-----------------------------------------------------|
| Simple records             | Use `Dict[str, Any]` with JSONB                     |
| Nested structures       | Use `RecordSpec` Pydantic model                        |
| High load               | Tune `create_async_engine` pool parameters          |
| Background processing   | Use ARQ, Celery, or custom polling loop             |
| Status logging          | Use `record_status_details` with error traces          |

---

## 🧪 Testing

Use `pytest-asyncio` and a test Postgres container to test all CRUD paths.

---

## 🚀 Final Notes

This structure is production-ready and extensible. To move forward, integrate it with FastAPI for RESTful control, and a background record system for processing workflows.

