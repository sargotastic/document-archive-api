import json

from fastapi import APIRouter

from app.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse

from app.services.embeddings import generate_embedding
from app.services.search import cosine_similarity


router = APIRouter(
    tags=["Search"]
)

@router.get("/search", response_model=list[DocumentResponse])
def search_documents(q: str):

    db = SessionLocal()

    search_term = f"%{q.lower()}%"

    documents = (
        db.query(Document)
        .filter(
            (Document.filename_normalized.ilike(search_term))
            | (Document.document_type.ilike(search_term))
            | (Document.extracted_text.ilike(search_term))
            | (Document.analysis.ilike(search_term))
        )
        .all()
    )

    db.close()

    results = []

    for document in documents:

        results.append({
            "id": document.id,
            "filename": document.filename,
            "document_type": document.document_type,
            "analysis": json.loads(document.analysis),
            "uploaded_at": document.uploaded_at
        })

    return results


@router.get("/semantic-search")
def semantic_search(
    q: str,
    limit: int = 5,
    threshold: float = 0.15
):

    db = SessionLocal()

    query_embedding = generate_embedding(q)

    chunks = db.query(DocumentChunk).all()

    results = []

    for chunk in chunks:

        if not chunk.embedding:
            continue

        chunk_embedding = json.loads(chunk.embedding)

        score = cosine_similarity(
            query_embedding,
            chunk_embedding
        )

        if score >= threshold:

            results.append({
                "document_id": chunk.document_id,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "similarity": round(float(score), 4)
            })

    db.close()

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:limit]