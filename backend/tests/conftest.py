"""
Test configuration and fixtures for pytest
"""
"""
Test configuration and fixtures for pytest
"""
import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.reference import Brand, MovementType, Complication
from app.models.collection import Collection
from app.models.watch import Watch
from app.core.security import get_password_hash, create_access_token


# Get test database URL from environment variables (same as main app)
POSTGRES_USER = os.getenv("POSTGRES_USER", "testuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "testpass")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "watch_tracker_test")

TEST_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create a new session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with dependency overrides.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(test_db: Session) -> User:
    """
    Create a test user in the database.
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user2(test_db: Session) -> User:
    """
    Create a second test user for ownership tests.
    """
    user = User(
        email="test2@example.com",
        hashed_password=get_password_hash("testpass123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """
    Generate JWT token for authenticated requests.
    """
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def auth_headers2(test_user2: User) -> dict:
    """
    Generate JWT token for second user.
    """
    access_token = create_access_token(data={"sub": str(test_user2.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_brand(test_db: Session) -> Brand:
    """
    Create a test brand.
    """
    brand = Brand(name="Rolex")
    test_db.add(brand)
    test_db.commit()
    test_db.refresh(brand)
    return brand


@pytest.fixture(scope="function")
def test_movement_type(test_db: Session) -> MovementType:
    """
    Create a test movement type.
    """
    movement = MovementType(name="Automatic")
    test_db.add(movement)
    test_db.commit()
    test_db.refresh(movement)
    return movement


@pytest.fixture(scope="function")
def test_complication(test_db: Session) -> Complication:
    """
    Create a test complication.
    """
    complication = Complication(name="Date")
    test_db.add(complication)
    test_db.commit()
    test_db.refresh(complication)
    return complication


@pytest.fixture(scope="function")
def test_collection(test_db: Session, test_user: User) -> Collection:
    """
    Create a test collection.
    """
    collection = Collection(
        name="Test Collection",
        description="A test collection",
        color="#FF0000",
        user_id=test_user.id
    )
    test_db.add(collection)
    test_db.commit()
    test_db.refresh(collection)
    return collection


@pytest.fixture(scope="function")
def test_watch(
    test_db: Session,
    test_user: User,
    test_brand: Brand,
    test_movement_type: MovementType,
    test_collection: Collection
) -> Watch:
    """
    Create a test watch with all associations.
    """
    watch = Watch(
        model="Submariner Date",
        brand_id=test_brand.id,
        collection_id=test_collection.id,
        reference_number="116610LN",
        serial_number="ABC12345",
        movement_type_id=test_movement_type.id,
        case_diameter=40.0,
        water_resistance=300,
        purchase_price=9000.00,
        purchase_currency="USD",
        condition="excellent",
        user_id=test_user.id
    )
    test_db.add(watch)
    test_db.commit()
    test_db.refresh(watch)
    return watch


@pytest.fixture(scope="function")
def mock_upload_dir(tmp_path, monkeypatch):
    """
    Create a temporary upload directory and mock the upload path.
    """
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    # Mock the UPLOAD_DIR in the file_upload module
    from app.utils import file_upload
    monkeypatch.setattr(file_upload, "UPLOAD_DIR", str(upload_dir))

    return upload_dir
