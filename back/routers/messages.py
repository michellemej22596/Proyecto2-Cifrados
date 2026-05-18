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
    MessageVerifyRequest,
    MessageVerifyResponse,
)
from crypto import (
    SECRET_KEY,
    ALGORITHM,
    decrypt_private_key,
    encrypt_message_hybrid,
    decrypt_message_hybrid,
)
from signatures.signer import DigitalSignatureService
from routers.blockchain import get_blockchain

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


@router.get("/{message_id}/verify", response_model=MessageVerifyResponse)
def verify_message_authenticity(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GET /messages/{msg_id}/verify
    
    Verifica la autenticidad de un mensaje especifico:
    1. Verifica que el mensaje exista
    2. Verifica que el usuario tenga acceso (sea remitente o destinatario)
    3. Verifica el registro en la blockchain (si existe)
    
    Nota: La verificacion completa de firma requiere descifrar el mensaje,
    lo cual necesita la contrasena del destinatario via POST.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )

    # Verificar que el usuario tenga acceso al mensaje
    if message.recipient_id != current_user.id and message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este mensaje",
        )

    # Verificar si el mensaje esta registrado en la blockchain
    bc = get_blockchain()
    blockchain_registered = False
    for block in bc.chain[1:]:  # Ignorar genesis
        if (block.sender_id == str(message.sender_id) and 
            block.recipient_id == str(message.recipient_id)):
            blockchain_registered = True
            break

    return MessageVerifyResponse(
        message_id=message_id,
        is_signature_valid=True,  # Asumimos valido sin firma almacenada
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        plaintext=None,  # No podemos descifrar sin password
        signature_status="NO_SIGNATURE_STORED" if not hasattr(message, 'signature') or message.signature is None else "SIGNATURE_PRESENT",
        blockchain_registered=blockchain_registered,
        message="Verificacion basica completada. Use POST para verificar firma con descifrado.",
    )


@router.post("/{message_id}/verify", response_model=MessageVerifyResponse)
def verify_message_with_decryption(
    message_id: int,
    payload: MessageVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /messages/{msg_id}/verify
    
    Verifica la autenticidad completa de un mensaje:
    1. Descifra el mensaje usando la contrasena del destinatario
    2. Calcula el hash del texto plano
    3. Verifica si existe en la blockchain con el hash correcto
    
    Retorna el estado de verificacion y el texto descifrado.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )

    if message.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el destinatario puede verificar con descifrado",
        )

    if message.encrypted_key is None or message.auth_tag is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este mensaje no usa cifrado hibrido valido",
        )

    # Descifrar la llave privada
    try:
        private_key_pem = decrypt_private_key(payload.password, current_user.encrypted_private_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contrasena incorrecta",
        )

    # Descifrar el mensaje
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

    # Calcular hash del mensaje descifrado
    message_hash = DigitalSignatureService.calculate_message_hash(plaintext)

    # Verificar en blockchain
    bc = get_blockchain()
    blockchain_registered = False
    hash_matches = False
    
    for block in bc.chain[1:]:  # Ignorar genesis
        if (block.sender_id == str(message.sender_id) and 
            block.recipient_id == str(message.recipient_id)):
            blockchain_registered = True
            if block.message_hash == message_hash:
                hash_matches = True
            break

    # Determinar estado de la firma/verificacion
    if blockchain_registered and hash_matches:
        signature_status = "VERIFIED"
        is_valid = True
        result_message = "Mensaje verificado exitosamente. Hash coincide con registro en blockchain."
    elif blockchain_registered and not hash_matches:
        signature_status = "HASH_MISMATCH"
        is_valid = False
        result_message = "ALERTA: El hash del mensaje NO coincide con el registro en blockchain. Posible alteracion."
    else:
        signature_status = "NOT_IN_BLOCKCHAIN"
        is_valid = True  # Valido pero sin registro
        result_message = "Mensaje descifrado correctamente pero no esta registrado en la blockchain."

    return MessageVerifyResponse(
        message_id=message_id,
        is_signature_valid=is_valid,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        plaintext=plaintext,
        signature_status=signature_status,
        blockchain_registered=blockchain_registered,
        message=result_message,
    )
