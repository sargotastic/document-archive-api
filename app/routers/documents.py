import json
import re

from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pypdf import PdfReader

from app.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse
from app.schemas.question import QuestionRequest

from app.services.ai import analyze_document, generate_answer
from app.services.embeddings import generate_embedding
from app.services.search import cosine_similarity
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

def normalize_filename(filename: str) -> str:
    filename = Path(filename).stem
    filename = re.sub(r"[-_/]+", " ", filename)
    filename = re.sub(r"\s+", " ", filename)
    return filename.lower().strip()

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    file_path = storage_dir / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        print(f"PDF extraction failed: {e}")

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid readable PDF."
        )

    filename_normalized = normalize_filename(file.filename)

    try:
        analysis = analyze_document(text)

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    from app.schemas.document import DocumentAnalysis

    analysis_data = DocumentAnalysis.model_validate_json(analysis)

    document_type = analysis_data.document_type

    embedding_text = f"""
Document type: {analysis_data.document_type}
Summary: {analysis_data.summary}
Topics: {", ".join(analysis_data.topics)}
People: {", ".join(analysis_data.people)}
Organizations: {", ".join(analysis_data.organizations)}
Dates: {", ".join(analysis_data.dates)}

Document content:
{text}
"""

    embedding = generate_embedding(embedding_text)

    chunks = chunk_text(text)

    db = SessionLocal()

    try:
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            filename_normalized=filename_normalized,
            file_path=str(file_path),
            extracted_text=text,
            document_type=document_type,
            analysis=analysis_data.model_dump_json(),
            embedding=json.dumps(embedding)
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        for index, chunk in enumerate(chunks):

            chunk_embedding = generate_embedding(chunk)

            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                text=chunk,
                embedding=json.dumps(chunk_embedding)
            )

            db.add(document_chunk)

        db.commit()

        document_id = document.id
        document_filename = document.filename
        document_type = document.document_type

    except Exception as e:

        db.rollback()

        print(f"Database operation failed: {e}")

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Failed to save the document."
        )

    finally:
        db.close()

    return {
        "id": document_id,
        "filename": document_filename,
        "pages": len(reader.pages),
        "document_type": document_type,
        "message": "Document uploaded successfully"
    }


@router.get("", response_model=list[DocumentResponse])
def get_documents(current_user: User = Depends(get_current_user)):

    db = SessionLocal()

    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
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

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, current_user: User = Depends(get_current_user)):

    db = SessionLocal()

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    db.close()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": document.id,
        "filename": document.filename,
        "document_type": document.document_type,
        "analysis": json.loads(document.analysis),
        "uploaded_at": document.uploaded_at
    }

@router.delete("/{document_id}")
def delete_document(document_id: int, current_user: User = Depends(get_current_user)):

    db = SessionLocal()

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    file_path = Path(document.file_path)

    if file_path.exists():
        file_path.unlink()

    db.delete(document)

    db.commit()

    db.close()

    return {
        "message": "Document deleted successfully",
        "id": document_id
    }

@router.get("/{document_id}/chunks")
def get_document_chunks(document_id: int, current_user: User = Depends(get_current_user)):

    db = SessionLocal()

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .all()
    )

    db.close()

    return [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text
        }
        for chunk in chunks
    ]


@router.post("/{document_id}/ask")
def ask_document(
    document_id: int,
    request: QuestionRequest, 
    current_user: User = Depends(get_current_user)
):

    db = SessionLocal()

    document = (
        db.query(Document)
        .filter(Document.id == document_id,Document.user_id == current_user.id)
        .first()
    )

    if document is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    query_embedding = generate_embedding(request.question)

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .all()
    )

    db.close()

    results = []

    for chunk in chunks:

        chunk_embedding = json.loads(chunk.embedding)

        score = cosine_similarity(
            query_embedding,
            chunk_embedding
        )

        results.append({
            "text": chunk.text,
            "similarity": float(score)
        })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    relevant_chunks = results[:3]

    context = "\n\n".join(
        chunk["text"]
        for chunk in relevant_chunks
    )

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the provided document context.

If the answer cannot be found in the context, say:
"I couldn't find that information in the document."

Do not invent information.

DOCUMENT CONTEXT:
{context}

QUESTION:
{request.question}

Answer clearly and concisely.
"""

    try:
        answer = generate_answer(prompt)

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    return {
        "document_id": document_id,
        "question": request.question,
        "answer": answer
    }