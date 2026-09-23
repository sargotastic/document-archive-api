def test_upload_document(client, monkeypatch, test_pdf):

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

    response = client.post(
        "/documents",
        files={
            "file": (
                "test.pdf",
                pdf,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "test.pdf"
    assert data["document_type"] == "test"
    assert data["message"] == "Document uploaded successfully"