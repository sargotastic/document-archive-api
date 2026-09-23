````markdown
# Document Intelligence + Personal Archive API

A backend API that turns uploaded PDF documents into searchable, structured knowledge.

Upload a document → extract its text → analyze it with AI → generate embeddings → store everything → search and ask questions about it later.

## Features

- PDF document upload
- PDF text extraction
- AI-powered document analysis
- Automatic document classification
- Summary generation
- Topic, people, organization and date extraction
- Document metadata storage
- Text chunking for retrieval
- Local semantic embeddings using Sentence Transformers
- Semantic search using cosine similarity
- Retrieval-Augmented Generation (RAG)
- AI-powered questions about individual documents
- JWT authentication
- Password hashing with Argon2
- User-specific document authorization
- Input validation
- Error handling
- Automated API tests

## Architecture

```mermaid
flowchart TD
    A[Client<br/>Swagger / Postman] --> B[FastAPI API]

    B --> C[Authentication]
    B --> D[Document Processing]
    B --> E[Search]

    D --> F[PDF Text Extraction]
    F --> G[Gemini AI Analysis]
    G --> H[Text Chunking]
    H --> I[MiniLM Embeddings]
    I --> J[(SQLite Database)]

    E --> J
    E --> K[Semantic Search]
    D --> L[RAG / Document Q&A]

    J --> L
    L --> G

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn
* SQLAlchemy
* SQLite

### AI / NLP

* Google Gemini
* Sentence Transformers
* `all-MiniLM-L6-v2`
* NumPy

### Document Processing

* PyPDF

### Authentication

* JWT
* PyJWT
* Argon2 password hashing

### Testing

* Pytest
* FastAPI TestClient

## Project Structure

```text
document-archive-api/
│
├── app/
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   │
│   ├── models/
│   │   ├── document.py
│   │   └── user.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   └── search.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── document.py
│   │   └── question.py
│   │
│   └── services/
│       ├── ai.py
│       ├── auth.py
│       ├── embeddings.py
│       └── search.py
│
├── tests/
│   ├── conftest.py
│   ├── test_documents.py
│   ├── test_health.py
│   ├── test_rag.py
│   └── test_upload.py
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## API Endpoints

### Health

```text
GET /health
```

Checks whether the API is running.

### Authentication

```text
POST /auth/register
POST /auth/login
```

Users can create an account and receive a JWT access token.

Protected endpoints use:

```text
Authorization: Bearer <token>
```

### Documents

```text
POST   /documents
GET    /documents
GET    /documents/{id}
DELETE /documents/{id}
GET    /documents/{id}/chunks
POST   /documents/{id}/ask
```

### Search

```text
GET /search
GET /semantic-search
```

## Document Processing Pipeline

When a PDF is uploaded:

```text
PDF
 ↓
File validation
 ↓
Text extraction
 ↓
Gemini document analysis
 ↓
Metadata + summary
 ↓
Text chunking
 ↓
MiniLM embeddings
 ↓
SQLite storage
```

The system stores both document-level and chunk-level information.

## Semantic Search

The semantic search endpoint converts the user's query into an embedding using:

```text
all-MiniLM-L6-v2
```

The query embedding is compared against stored chunk embeddings using cosine similarity.

This allows searches based on meaning rather than exact keyword matches.

## RAG / Document Q&A

The `/documents/{id}/ask` endpoint implements a basic Retrieval-Augmented Generation pipeline.

```text
Question
   ↓
Generate query embedding
   ↓
Find relevant document chunks
   ↓
Build context
   ↓
Send context + question to Gemini
   ↓
Generate answer
```

This allows users to ask questions about the contents of a specific document.

## Authentication & Authorization

The API uses JWT-based authentication.

Passwords are never stored directly. They are hashed using Argon2.

Documents are associated with the user who uploaded them.

Protected document operations verify that the authenticated user owns the requested document.

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd document-archive-api
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate it

macOS / Linux:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_long_random_secret
```

Never commit `.env` to Git.

### 6. Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Running Tests

Run the complete test suite:

```bash
pytest
```

The test suite covers:

* Health endpoint
* PDF validation
* Document upload
* Document retrieval
* Document deletion
* Authentication-aware document access
* RAG document question answering

## Environment Variables

| Variable         | Description                           |
| ---------------- | ------------------------------------- |
| `GEMINI_API_KEY` | API key used for Gemini AI features   |
| `JWT_SECRET_KEY` | Secret used to sign JWT access tokens |

## Current Limitations

* PDF text extraction only
* No OCR for scanned/image-only PDFs
* SQLite is used for local storage
* Semantic search is implemented in Python rather than a dedicated vector database
* Embeddings are stored directly in SQLite
* No frontend application

## Future Improvements

Potential future improvements include:

* OCR support
* PostgreSQL
* Dedicated vector database
* Background document processing
* File type expansion
* Document versioning
* Advanced metadata filtering
* Conversation history for document Q&A
* Frontend interface
* Local LLM support using Ollama
* Cloud deployment

## Why I Built This

This project was built to explore backend engineering and AI application development through a complete end-to-end system.

It combines:

* REST API design
* Database modeling
* Authentication and authorization
* Document processing
* NLP embeddings
* Semantic search
* Retrieval-Augmented Generation
* External AI API integration
* Automated testing
* Production-oriented error handling

````