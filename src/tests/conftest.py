import os
import tempfile
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient

# setup temporary database before importing app
_db_fd, _db_path = tempfile.mkstemp(prefix="test_db", suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_db_path}"

from src.main import app
from src.database import init_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    await init_db()
    yield
    os.remove(_db_path)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
