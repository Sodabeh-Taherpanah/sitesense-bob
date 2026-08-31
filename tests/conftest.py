# conftest.py
# Shared pytest fixtures using a temporary file-based SQLite DB.
#
# WHY NOT :memory:?
# SQLite :memory: databases are per-connection. FastAPI's TestClient runs
# requests in a worker thread (anyio), which opens a new connection — and
# therefore sees a blank database even if tables were created on another
# connection. Using a temp file avoids this: all connections share one file.

import os
import sys
import tempfile

# backend/ must be on sys.path before any backend import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- create a temp-file engine once for the whole test session ---
_db_fd, _db_path = tempfile.mkstemp(suffix=".test.db")
os.close(_db_fd)
TEST_DB_URL = f"sqlite:///{_db_path}"

TEST_ENGINE = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

# Patch BEFORE importing anything from backend so all modules see the test engine
import database as _db_module
_db_module.engine = TEST_ENGINE
_db_module.SessionLocal = TestingSessionLocal

from database import Base, get_db  # noqa: E402
from main import app               # noqa: E402


def _override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def fresh_tables():
    """Drop and recreate all tables before each test for a clean slate."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client(fresh_tables):
    """TestClient with get_db overridden to use the test DB."""
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def pytest_sessionfinish(session, exitstatus):
    """Clean up the temp DB file after the test run."""
    try:
        TEST_ENGINE.dispose()
        os.unlink(_db_path)
    except OSError:
        pass
