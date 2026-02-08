import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so `app` package is importable when pytest runs.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import create_db_and_tables, engine
from app.models import SQLModel
from main import app


@pytest.fixture(scope="session", autouse=True)
def prepare_db():
    # Drop all existing tables and recreate them for a clean test environment
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
