import os
import base64

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from database import get_db
from models import User, Group, GroupMember, GroupMessage
from schemas import (
    GroupCreate,
    GroupResponse,
    GroupMessageCreate,
    GroupMessageResponse,
    GroupMessageDecryptRequest,
    GroupMessageDecryptResponse,
)
from crypto import (
    SECRET_KEY,
    ALGORITHM,
    decrypt_private_key,
    encrypt_aes_key_rsa_oaep,
    decrypt_aes_key_rsa_oaep,
)

router = APIRouter(prefix="/groups", tags=["groups"])

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


def get_group_member(
    db: Session,
    group_id: int,
    user_id: int,
) -> GroupMember:
    member = (
        db.query(GroupMember)
        .filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
        .first()
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No perteneces a este grupo",
        )

    return member


def decrypt_group_key_for_user(
    password: str,
    current_user: User,
    member: GroupMember,
) -> bytes:
    try:
        private_key_pem = decrypt_private_key(
            password,
            current_user.encrypted_private_key,
        )

        group_key = decrypt_aes_key_rsa_oaep(
            private_key_pem,
            member.encrypted_group_key,
        )

        return group_key

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo recuperar la clave del grupo. Verifica tu contraseña.",
        )


def encrypt_group_message(content: str, group_key: bytes) -> tuple[str, str]:
    aesgcm = AESGCM(group_key)
    nonce = os.urandom(12)

    ciphertext = aesgcm.encrypt(
        nonce,
        content.encode(),
        None,
    )

    return (
        base64.urlsafe_b64encode(ciphertext).decode(),
        base64.urlsafe_b64encode(nonce).decode(),
    )


def decrypt_group_message(
    ciphertext_b64: str,
    nonce_b64: str,
    group_key: bytes,
) -> str:
    try:
        aesgcm = AESGCM(group_key)

        ciphertext = base64.urlsafe_b64decode(ciphertext_b64)
        nonce = base64.urlsafe_b64decode(nonce_b64)

        plaintext = aesgcm.decrypt(
            nonce,
            ciphertext,
            None,
        )

        return plaintext.decode()

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al descifrar el mensaje grupal",
        )


# ---------------------------------------------------------------------------
# Crear grupo con clave AES-256 compartida
# ---------------------------------------------------------------------------

@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member_names = set(payload.member_names)

    users = db.query(User).filter(User.name.in_(member_names)).all()

    if len(users) != len(member_names):
        found_names = {user.name for user in users}
        missing_names = member_names - found_names

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron estos usuarios: {', '.join(missing_names)}",
        )

    # agregar siempre al usuario actual
    if current_user not in users:
        users.append(current_user)

    group = Group(
        name=payload.name,
        owner_id=current_user.id,
    )

    db.add(group)
    db.commit()
    db.refresh(group)

    group_key = AESGCM.generate_key(bit_length=256)

    for user in users:
        encrypted_group_key = encrypt_aes_key_rsa_oaep(
            user.public_key_pem,
            group_key,
        )

        member = GroupMember(
            group_id=group.id,
            user_id=user.id,
            encrypted_group_key=encrypted_group_key,
        )

        db.add(member)

    db.commit()
    db.refresh(group)

    return group


# ---------------------------------------------------------------------------
# Listar grupos del usuario autenticado
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[GroupResponse])
def get_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    groups = (
        db.query(Group)
        .join(GroupMember, Group.id == GroupMember.group_id)
        .filter(GroupMember.user_id == current_user.id)
        .all()
    )

    return groups


# ---------------------------------------------------------------------------
# Enviar mensaje grupal cifrado con clave compartida
# ---------------------------------------------------------------------------

@router.post(
    "/{group_id}/messages",
    response_model=GroupMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group_message(
    group_id: int,
    payload: GroupMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado",
        )

    member = get_group_member(
        db=db,
        group_id=group_id,
        user_id=current_user.id,
    )

    group_key = decrypt_group_key_for_user(
        password=payload.password,
        current_user=current_user,
        member=member,
    )

    ciphertext, nonce = encrypt_group_message(
        payload.content,
        group_key,
    )

    message = GroupMessage(
        group_id=group.id,
        sender_id=current_user.id,
        ciphertext=ciphertext,
        nonce=nonce,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


# ---------------------------------------------------------------------------
# Obtener mensajes cifrados de un grupo
# ---------------------------------------------------------------------------

@router.get("/{group_id}/messages", response_model=list[GroupMessageResponse])
def get_group_messages(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado",
        )

    get_group_member(
        db=db,
        group_id=group_id,
        user_id=current_user.id,
    )

    messages = (
        db.query(GroupMessage)
        .filter(GroupMessage.group_id == group_id)
        .order_by(GroupMessage.created_at.asc())
        .all()
    )

    return messages


# ---------------------------------------------------------------------------
# Descifrar mensaje grupal
# ---------------------------------------------------------------------------

@router.post(
    "/{group_id}/messages/{message_id}/decrypt",
    response_model=GroupMessageDecryptResponse,
)
def decrypt_group_message_endpoint(
    group_id: int,
    message_id: int,
    payload: GroupMessageDecryptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado",
        )

    member = get_group_member(
        db=db,
        group_id=group_id,
        user_id=current_user.id,
    )

    message = (
        db.query(GroupMessage)
        .filter(
            GroupMessage.id == message_id,
            GroupMessage.group_id == group_id,
        )
        .first()
    )

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje grupal no encontrado",
        )

    group_key = decrypt_group_key_for_user(
        password=payload.password,
        current_user=current_user,
        member=member,
    )

    plaintext = decrypt_group_message(
        message.ciphertext,
        message.nonce,
        group_key,
    )

    return {"plaintext": plaintext}