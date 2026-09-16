from fastapi import FastAPI

app = FastAPI(
    title="Document Archive API",
    description="API for storing and understanding documents.",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}