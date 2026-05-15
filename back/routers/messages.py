from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from database import get_db
from models import Message, User
from schemas import (
    HybridMessageCreate,
    HybridMessageResponse,
    MessageDecryptRequest,
    MessageDecryptResponse,
)
from crypto import (
    SECRET_KEY,
    ALGORITHM,
    decrypt_private_key,
    encrypt_message_hybrid,
    decrypt_message_hybrid,
)

router = APIRouter(prefix="/messages", tags=["messages"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# ---------------------------------------------------------------------------
# Endpoints híbridos — cifrado RSA-OAEP + AES-256-GCM efímero
# ---------------------------------------------------------------------------

@router.get("/hybrid/", response_model=list[HybridMessageResponse])
def get_hybrid_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Message)
        .filter(
            (Message.recipient_id == current_user.id)
            | (Message.sender_id == current_user.id)
        )
        .all()
    )


@router.post("/hybrid/", response_model=HybridMessageResponse, status_code=status.HTTP_201_CREATED)
def create_hybrid_message(
    payload: HybridMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    if recipient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario no encontrado",
        )

    encrypted = encrypt_message_hybrid(payload.content, recipient.public_key_pem)

    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        ciphertext=encrypted["ciphertext"],
        nonce=encrypted["nonce"],
        auth_tag=encrypted["auth_tag"],
        encrypted_key=encrypted["encrypted_key"],
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.post("/{message_id}/decrypt", response_model=MessageDecryptResponse)
def decrypt_hybrid_message(
    message_id: int,
    payload: MessageDecryptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )

    if message.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el destinatario puede descifrar este mensaje",
        )

    if message.encrypted_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este mensaje no usa cifrado híbrido",
        )

    try:
        private_key_pem = decrypt_private_key(payload.password, current_user.encrypted_private_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
        )

    if message.auth_tag is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este mensaje no contiene auth tag (no es un mensaje híbrido válido)",
        )

    try:
        plaintext = decrypt_message_hybrid(
            private_key_pem,
            message.encrypted_key,
            message.ciphertext,
            message.nonce,
            message.auth_tag,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al descifrar el mensaje",
        )

    return {"plaintext": plaintext}
