def test_upload_rejects_non_pdf(client):
    response = client.post(
        "/documents",
        files={
            "file": (
                "test.txt",
                b"This is not a PDF",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Only PDF files are supported."
    }


def test_get_and_delete_document(client, monkeypatch, test_pdf):

    def fake_analyze_document(text):
        return """
        {
            "document_type": "test",
            "summary": "Test document",
            "topics": ["testing"],
            "people": [],
            "organizations": [],
            "dates": []
        }
        """

    def fake_generate_embedding(text):
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(
        "app.routers.documents.analyze_document",
        fake_analyze_document
    )

    monkeypatch.setattr(
        "app.routers.documents.generate_embedding",
        fake_generate_embedding
    )

    pdf = test_pdf

    upload_response = client.post(
        "/documents",
        files={
            "file": (
                "crud-test.pdf",
                pdf,
                "application/pdf"
            )
        }
    )

    assert upload_response.status_code == 200

    document_id = upload_response.json()["id"]

    # Test GET /documents/{id}

    get_response = client.get(
        f"/documents/{document_id}"
    )

    assert get_response.status_code == 200

    document = get_response.json()

    assert document["id"] == document_id
    assert document["filename"] == "crud-test.pdf"
    assert document["document_type"] == "test"

    # Test DELETE /documents/{id}

    delete_response = client.delete(
        f"/documents/{document_id}"
    )

    assert delete_response.status_code == 200

    assert delete_response.json() == {
        "message": "Document deleted successfully",
        "id": document_id
    }

    # Confirm document is actually gone

    get_deleted_response = client.get(
        f"/documents/{document_id}"
    )

    assert get_deleted_response.status_code == 404