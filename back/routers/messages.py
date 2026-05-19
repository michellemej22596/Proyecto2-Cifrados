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
from services.alerts import AlertService

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
    """
    Crea un mensaje cifrado hibrido (RSA-OAEP + AES-256-GCM) con firma digital.
    
    Flujo completo (Responsabilidades de Silvia):
    1. Descifra la llave privada del remitente usando su contraseña
    2. Firma el mensaje (SHA-256 + RSA-PSS) con la llave privada
    3. Calcula el hash SHA-256 del texto plano original
    4. Cifra el mensaje con cifrado híbrido para el destinatario
    5. Guarda el mensaje con la firma en la base de datos
    6. Registra automáticamente la transacción en la blockchain
    """
    # Verificar que el destinatario existe
    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    if recipient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario no encontrado",
        )

    # 1. Descifrar la llave privada del remitente para poder firmar
    try:
        sender_private_key = decrypt_private_key(payload.password, current_user.encrypted_private_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta. No se puede firmar el mensaje.",
        )

    # 2. Firmar el mensaje usando ECDSA (sign_message) - Fase 3
    try:
        signature = DigitalSignatureService.sign_message(payload.content, sender_private_key.decode('utf-8'))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al firmar el mensaje: {str(e)}",
        )

    # 3. Calcular hash del mensaje ANTES de cifrar (para registro en blockchain)
    message_hash = DigitalSignatureService.calculate_message_hash(payload.content)

    # 4. Cifrar el mensaje con cifrado híbrido para el destinatario
    encrypted = encrypt_message_hybrid(payload.content, recipient.public_key_pem)

    # 5. Crear y guardar el mensaje en la base de datos con la firma
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        ciphertext=encrypted["ciphertext"],
        nonce=encrypted["nonce"],
        auth_tag=encrypted["auth_tag"],
        encrypted_key=encrypted["encrypted_key"],
        signature=signature,  # Campo de firma digital
        verification_status="PENDING",  # Estado inicial
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    # 6. Registrar automáticamente en la blockchain (add_new_transaction)
    bc = get_blockchain()
    bc.add_new_transaction(
        sender_id=str(current_user.id),
        recipient_id=str(recipient.id),
        message_hash=message_hash,
    )

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
    
    Verifica la autenticidad básica de un mensaje específico:
    1. Verifica que el mensaje exista
    2. Verifica que el usuario tenga acceso (sea remitente o destinatario)
    3. Verifica si existe firma digital almacenada
    4. Verifica el registro en la blockchain (si existe)
    
    Nota: La verificación completa de firma requiere descifrar el mensaje,
    lo cual necesita la contraseña del destinatario via POST.
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

    # Verificar si el mensaje tiene firma almacenada
    has_signature = message.signature is not None and len(message.signature) > 0

    # Verificar si el mensaje está registrado en la blockchain
    # Mejora: Buscar específicamente si existe algún registro para este par de usuarios
    bc = get_blockchain()
    blockchain_registered = False
    for block in bc.chain[1:]:  # Ignorar genesis
        if (block.sender_id == str(message.sender_id) and 
            block.recipient_id == str(message.recipient_id)):
            blockchain_registered = True
            # Nota: No hacemos break aquí para permitir verificación más completa en el futuro
            # Por ahora solo verificamos existencia, POST hace la verificación completa del hash

    # Determinar estado
    if has_signature:
        signature_status = "SIGNATURE_PRESENT"
        status_message = "Firma digital presente. Use POST para verificar con descifrado completo."
    else:
        signature_status = "NO_SIGNATURE_STORED"
        status_message = "ADVERTENCIA: Este mensaje no tiene firma digital almacenada."

    return MessageVerifyResponse(
        message_id=message_id,
        is_signature_valid=has_signature,  # Parcialmente válido si tiene firma
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        plaintext=None,  # No podemos descifrar sin password
        signature_status=signature_status,
        blockchain_registered=blockchain_registered,
        message=status_message,
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
    
    Verifica la autenticidad completa de un mensaje (Flujo de Silvia):
    1. Descifra el mensaje usando la contraseña del destinatario
    2. Verifica la firma digital usando la llave pública del remitente
    3. Si la firma NO coincide: marca como NO VERIFICADO y dispara alerta
    4. Calcula el hash del texto plano y verifica en blockchain
    
    Retorna el estado de verificación y el texto descifrado.
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
            detail="Este mensaje no usa cifrado híbrido válido",
        )

    # Descifrar la llave privada del destinatario
    try:
        private_key_pem = decrypt_private_key(payload.password, current_user.encrypted_private_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
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

    # Obtener la llave pública del remitente para verificar la firma
    sender = db.query(User).filter(User.id == message.sender_id).first()
    if sender is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remitente no encontrado",
        )

    # Verificar la firma digital si existe usando ECDSA - Fase 3
    signature_valid = False
    if message.signature:
        signature_valid = DigitalSignatureService.verify_message_signature(
            plaintext,
            message.signature,
            sender.public_key_pem
        )

    # Calcular hash del mensaje descifrado
    message_hash = DigitalSignatureService.calculate_message_hash(plaintext)

    # Verificar en blockchain - Bug fix: el break ahora solo ocurre cuando se encuentra el hash exacto
    bc = get_blockchain()
    blockchain_registered = False
    hash_matches = False
    
    for block in bc.chain[1:]:  # Ignorar genesis
        if (block.sender_id == str(message.sender_id) and 
            block.recipient_id == str(message.recipient_id)):
            blockchain_registered = True
            if block.message_hash == message_hash:
                hash_matches = True
                break  # Solo salir cuando encontramos el hash exacto

    # Determinar estado de verificación y actualizar en BD
    # Flujo de excepción de Silvia: Si la firma NO coincide -> NO VERIFICADO + alerta
    if not message.signature:
        signature_status = "NO_SIGNATURE"
        is_valid = False
        message.verification_status = "NOT_VERIFIED"
        result_message = "ALERTA: El mensaje no tiene firma digital. No se puede verificar autenticidad."
        # Disparar alerta de seguridad
        AlertService.create_no_signature_alert(
            message_id=message_id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
        )
    elif not signature_valid:
        # ⚠️ ALERTA AL USUARIO: Firma digital no coincide
        signature_status = "SIGNATURE_INVALID"
        is_valid = False
        message.verification_status = "NOT_VERIFIED"
        result_message = "⚠️ ALERTA DE SEGURIDAD: La firma digital NO COINCIDE. El mensaje puede haber sido alterado o el remitente no es quien dice ser. NO CONFÍE en este mensaje."
        # Disparar alerta crítica de seguridad (flujo de excepción de Silvia)
        AlertService.create_signature_invalid_alert(
            message_id=message_id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
        )
    elif blockchain_registered and hash_matches:
        signature_status = "VERIFIED"
        is_valid = True
        message.verification_status = "VERIFIED"
        result_message = "✓ Mensaje verificado exitosamente. Firma válida y hash coincide con registro en blockchain."
    elif blockchain_registered and not hash_matches:
        signature_status = "HASH_MISMATCH"
        is_valid = False
        message.verification_status = "NOT_VERIFIED"
        result_message = "⚠️ ALERTA: El hash del mensaje NO coincide con el registro en blockchain. Posible alteración del contenido."
        # Disparar alerta de hash mismatch
        AlertService.create_hash_mismatch_alert(
            message_id=message_id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
        )
    else:
        # Firma válida pero no está en blockchain
        signature_status = "SIGNATURE_VALID_NO_BLOCKCHAIN"
        is_valid = True
        message.verification_status = "VERIFIED"
        result_message = "✓ Firma digital verificada correctamente. Nota: Mensaje no encontrado en blockchain."

    # Guardar el estado de verificación actualizado
    db.commit()

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


# ---------------------------------------------------------------------------
# Endpoint de Alertas de Seguridad
# ---------------------------------------------------------------------------

@router.get("/alerts/me")
def get_my_security_alerts(
    current_user: User = Depends(get_current_user),
):
    """
    GET /messages/alerts/me
    
    Obtiene todas las alertas de seguridad para el usuario actual.
    Incluye alertas de firmas inválidas, hash mismatch, etc.
    """
    alerts = AlertService.get_alerts_for_user(current_user.id)
    return {
        "user_id": current_user.id,
        "total_alerts": len(alerts),
        "critical_count": len([a for a in alerts if a.is_critical]),
        "alerts": [
            {
                "type": alert.alert_type.value,
                "message_id": alert.message_id,
                "sender_id": alert.sender_id,
                "recipient_id": alert.recipient_id,
                "description": alert.description,
                "timestamp": alert.timestamp,
                "is_critical": alert.is_critical,
            }
            for alert in alerts
        ],
    }
