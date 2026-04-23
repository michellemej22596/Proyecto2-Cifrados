from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import PublicKeyResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/key", response_model=PublicKeyResponse)
def get_public_key(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    return {
        "user_id": user.id,
        "public_key_pem": user.public_key_pem,
    }