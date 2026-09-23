from fastapi import FastAPI
from app.database import Base, engine
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.routers.documents import router as documents_router
from app.routers.search import router as search_router
from app.routers.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Archive API",
    description="API for storing and understanding documents.",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(auth_router)