from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Message
from schemas import MessageCreate, MessageResponse
from crypto import encrypt_message_aes_gcm

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)):
    ciphertext, nonce = encrypt_message_aes_gcm(payload.content)

    message = Message(
        ciphertext=ciphertext,
        nonce=nonce,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.get("/", response_model=list[MessageResponse])
def get_messages(db: Session = Depends(get_db)):
    return db.query(Message).all()