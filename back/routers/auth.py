from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import User
from schemas import UserRegister, UserResponse
from crypto import hash_password, generate_key_pair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    # Verificar email único antes de hacer trabajo costoso
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado.",
        )

    password_hash = hash_password(payload.password)
    public_key_pem, encrypted_private_key = generate_key_pair(payload.password)

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=password_hash,
        public_key_pem=public_key_pem,
        encrypted_private_key=encrypted_private_key,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado.",
        )

    return user
