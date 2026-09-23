from app.models.document import Document, DocumentChunk
from tests.conftest import TestingSessionLocal


def test_ask_document(client, monkeypatch):

    def fake_generate_embedding(text):
        return [1.0, 0.0, 0.0]

    def fake_generate_answer(prompt):
        return "This is the answer from the test AI."

    monkeypatch.setattr(
        "app.routers.documents.generate_embedding",
        fake_generate_embedding
    )

    monkeypatch.setattr(
        "app.routers.documents.generate_answer",
        fake_generate_answer
    )

    db = TestingSessionLocal()

    # Get the authenticated test user's ID from the JWT
    from app.dependencies import get_current_user

    user = db.query(
        __import__("app.models.user", fromlist=["User"]).User
    ).filter(
        __import__("app.models.user", fromlist=["User"]).User.username == "testuser"
    ).first()

    document = Document(
        user_id=user.id,
        filename="rag-test.pdf",
        filename_normalized="rag test",
        file_path="storage/rag-test.pdf",
        extracted_text="This document is about software testing.",
        document_type="test",
        analysis='{"document_type":"test","summary":"Test document","topics":[],"people":[],"organizations":[],"dates":[]}',
        embedding='[1.0, 0.0, 0.0]'
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        text="This document is about software testing.",
        embedding='[1.0, 0.0, 0.0]'
    )

    db.add(chunk)
    db.commit()

    document_id = document.id

    db.close()

    response = client.post(
        f"/documents/{document_id}/ask",
        json={
            "question": "What is this document about?"
        }
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "This is the answer from the test AI."