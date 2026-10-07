import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
import app.core.database as database_module
from app.core.config import settings

# Use in-memory SQLite database for testing with StaticPool so memory DB persists across threads
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    """Overrides generated files directory to a temporary path during tests."""
    temp_dir = tmp_path_factory.mktemp("generated_test_certs")
    settings.GENERATED_CERTIFICATES_DIR = str(temp_dir)
    yield temp_dir


@pytest.fixture(scope="function")
def db_session():
    """Creates a clean database session for each test and overrides SessionLocal."""
    # Direct SessionLocal in app.core.database to use TestingSessionLocal for background tasks
    old_session_local = database_module.SessionLocal
    database_module.SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        database_module.SessionLocal = old_session_local


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient equipped with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
