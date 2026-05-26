import base64
import io

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import User
from schemas import (
    UserRegister,
    UserResponse,
    UserLogin,
    LoginResponse,
    MfaStatusResponse,
    MfaSetupResponse,
    MfaOtpRequest,
    MfaVerifyRequest,
    MfaMessageResponse,
)
from crypto import (
    hash_password,
    verify_password,
    generate_key_pair,
    generate_ecdsa_key_pair,
    create_access_token,
    encrypt_mfa_secret,
    decrypt_mfa_secret,
    SECRET_KEY,
    ALGORITHM,
)
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Duración del token temporal de sesión MFA (sólo permite avanzar al paso 2)
MFA_SESSION_MINUTES = 5


# ---------------------------------------------------------------------------
# Dependencia: usuario autenticado (bearer JWT)
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "mfa_session":
            raise exc  # token de sesión MFA no es un token de acceso completo
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise exc
    return user


# ---------------------------------------------------------------------------
# Helper: genera QR como data-URI PNG
# ---------------------------------------------------------------------------

def _build_qr_data_uri(uri: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado.",
        )

    password_hash = hash_password(payload.password)
    public_key_pem, encrypted_private_key = generate_key_pair(payload.password)
    ecdsa_public_key_pem, encrypted_ecdsa_private_key = generate_ecdsa_key_pair(payload.password)

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=password_hash,
        public_key_pem=public_key_pem,
        encrypted_private_key=encrypted_private_key,
        ecdsa_public_key_pem=ecdsa_public_key_pem,
        encrypted_ecdsa_private_key=encrypted_ecdsa_private_key,
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


# ---------------------------------------------------------------------------
# Login — primer factor (contraseña)
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Primer factor de autenticación.

    - Sin MFA activo  → devuelve access_token (JWT completo, token_type='bearer').
    - Con MFA activo  → devuelve mfa_session_token (JWT de 5 min, token_type='mfa_session')
                        junto a mfa_required=True. El cliente debe redirigir al paso 2.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not user.mfa_enabled:
        # Sin MFA → token completo
        token = create_access_token({"sub": str(user.id), "email": user.email})
        return LoginResponse(access_token=token, token_type="bearer", mfa_required=False)

    # Con MFA → token de sesión temporal (sólo para avanzar al paso 2)
    mfa_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "type": "mfa_session"},
        expires_delta=timedelta(minutes=MFA_SESSION_MINUTES),
    )
    return LoginResponse(
        mfa_session_token=mfa_token,
        token_type="mfa_session",
        mfa_required=True,
    )


# ---------------------------------------------------------------------------
# Login — segundo factor (TOTP)
# ---------------------------------------------------------------------------

@router.post("/mfa/verify", response_model=LoginResponse)
def mfa_verify(payload: MfaVerifyRequest, db: Session = Depends(get_db)):
    """
    Segundo factor: verifica el código TOTP y emite el JWT de acceso completo.
    Requiere el mfa_session_token obtenido en /auth/login.
    """
    exc_invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Código MFA inválido o sesión expirada",
    )
    try:
        payload_jwt = jwt.decode(payload.mfa_session_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload_jwt.get("type") != "mfa_session":
            raise exc_invalid
        user_id = int(payload_jwt.get("sub", -1))
    except (JWTError, ValueError):
        raise exc_invalid

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.mfa_enabled or not user.mfa_secret:
        raise exc_invalid

    secret = decrypt_mfa_secret(user.mfa_secret)
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.otp_code, valid_window=1):
        raise exc_invalid

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return LoginResponse(access_token=token, token_type="bearer", mfa_required=False)


# ---------------------------------------------------------------------------
# MFA — estado actual
# ---------------------------------------------------------------------------

@router.get("/mfa/status", response_model=MfaStatusResponse)
def mfa_status(current_user: User = Depends(get_current_user)):
    return MfaStatusResponse(mfa_enabled=bool(current_user.mfa_enabled))


# ---------------------------------------------------------------------------
# MFA — obtener QR para configurar la app autenticadora
# ---------------------------------------------------------------------------

@router.get("/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Genera (o regenera) el secreto TOTP del usuario y devuelve:
    - secret   : cadena Base32 para entrada manual en la app autenticadora
    - uri      : otpauth://totp/... para escanear con la cámara
    - qr_code  : data:image/png;base64,... lista para <img src="...">

    El secreto se guarda cifrado en BD pero MFA NO queda activado todavía.
    El usuario debe confirmar con POST /auth/mfa/enable + código OTP válido.
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="VaultChain")

    current_user.mfa_secret = encrypt_mfa_secret(secret)
    db.commit()

    return MfaSetupResponse(
        secret=secret,
        uri=uri,
        qr_code=_build_qr_data_uri(uri),
    )


# ---------------------------------------------------------------------------
# MFA — activar (después de escanear el QR y verificar un código)
# ---------------------------------------------------------------------------

@router.post("/mfa/enable", response_model=MfaMessageResponse)
def mfa_enable(
    payload: MfaOtpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Activa MFA para el usuario.
    Requiere que el usuario ya haya llamado GET /auth/mfa/setup para tener
    un secreto almacenado, y que el código OTP sea válido.
    """
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primero llama a GET /auth/mfa/setup para generar el secreto.",
        )

    secret = decrypt_mfa_secret(current_user.mfa_secret)
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.otp_code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código OTP incorrecto. Verifica la hora de tu dispositivo.",
        )

    current_user.mfa_enabled = True
    db.commit()
    return MfaMessageResponse(message="MFA activado exitosamente.")


# ---------------------------------------------------------------------------
# MFA — desactivar
# ---------------------------------------------------------------------------

@router.post("/mfa/disable", response_model=MfaMessageResponse)
def mfa_disable(
    payload: MfaOtpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Desactiva MFA. Requiere un código OTP válido para confirmar."""
    if not current_user.mfa_enabled or not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA no está activado en esta cuenta.",
        )

    secret = decrypt_mfa_secret(current_user.mfa_secret)
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.otp_code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código OTP incorrecto.",
        )

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()
    return MfaMessageResponse(message="MFA desactivado exitosamente.")
