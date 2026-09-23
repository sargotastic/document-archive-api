import pytest
from io import BytesIO

from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.database import Base
from app.main import app
import app.routers.documents as documents_router


TEST_DATABASE_URL = "sqlite:///./test_documents.db"

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture
def test_pdf():
    pdf = PdfWriter()
    pdf.add_blank_page(width=300, height=300)

    buffer = BytesIO()
    pdf.write(buffer)
    buffer.seek(0)

    return buffer


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    documents_router.SessionLocal = TestingSessionLocal

    test_client = TestClient(app)

    # Create test user directly in the SAME database used by the tests
    from app.models.user import User
    from app.services.auth import hash_password

    db = TestingSessionLocal()

    user = User(
        username="testuser",
        password_hash=hash_password("testpassword")
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    db.close()

    # Create JWT directly
    from app.services.auth import create_access_token

    token = create_access_token(user_id)

    test_client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    yield test_client

    test_client.close()
    Base.metadata.drop_all(bind=test_engine)