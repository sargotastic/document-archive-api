from fastapi import APIRouter, HTTPException
from app.schemas.auth import RegisterRequest, LoginRequest
from app.database import SessionLocal
from app.models.user import User
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register")
def register(request: RegisterRequest):

    db = SessionLocal()

    existing_user = (
        db.query(User)
        .filter(User.username == request.username)
        .first()
    )

    if existing_user:
        db.close()

        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )

    user = User(
    username=request.username,
    password_hash=hash_password(request.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    db.close()

    return {
        "id": user_id,
        "username": request.username,
        "message": "User registered successfully."
    }

@router.post("/login")
def login(request: LoginRequest):

    db = SessionLocal()

    user = (
        db.query(User)
        .filter(User.username == request.username)
        .first()
    )

    db.close()

    if user is None or not verify_password(
        request.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }