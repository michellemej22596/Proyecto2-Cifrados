from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    public_key_pem: str

    model_config = {"from_attributes": True}


class PublicKeyResponse(BaseModel):
    user_id: int
    public_key_pem: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: int
    ciphertext: str
    nonce: str

    model_config = {"from_attributes": True}


class HybridMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    recipient_id: int
    password: str = Field(..., min_length=1, description="Contraseña del remitente para firmar el mensaje")


class HybridMessageResponse(BaseModel):
    id: int
    sender_id: int | None = None
    recipient_id: int | None = None
    ciphertext: str
    encrypted_key: str | None = None
    nonce: str
    auth_tag: str | None = None
    signature: str | None = None
    verification_status: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageDecryptRequest(BaseModel):
    password: str


class MessageDecryptResponse(BaseModel):
    plaintext: str

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1)
    member_names: list[str]


class GroupResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    model_config = {"from_attributes": True}


class GroupMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    password: str


class GroupMessageResponse(BaseModel):
    id: int
    group_id: int
    sender_id: int
    ciphertext: str
    nonce: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class GroupMessageDecryptRequest(BaseModel):
    password: str


class GroupMessageDecryptResponse(BaseModel):
    plaintext: str


# ---------------------------------------------------------------------------
# Message Verification Schemas
# ---------------------------------------------------------------------------

class MessageVerifyRequest(BaseModel):
    """Request para verificar autenticidad de un mensaje."""
    password: str


class MessageVerifyResponse(BaseModel):
    """Response con el resultado de verificacion de un mensaje."""
    message_id: int
    is_signature_valid: bool
    sender_id: int | None = None
    recipient_id: int | None = None
    plaintext: str | None = None
    signature_status: str
    blockchain_registered: bool = False
    message: str


# ---------------------------------------------------------------------------
# MFA Schemas
# ---------------------------------------------------------------------------

class LoginResponse(BaseModel):
    """
    Respuesta al POST /auth/login.
    - Login sin MFA   → access_token presente, mfa_required=False
    - Login con MFA   → mfa_session_token presente, mfa_required=True
    """
    access_token: str | None = None
    mfa_session_token: str | None = None
    token_type: str
    mfa_required: bool = False


class MfaStatusResponse(BaseModel):
    mfa_enabled: bool


class MfaSetupResponse(BaseModel):
    """Datos que necesita el cliente para configurar su app autenticadora."""
    secret: str           # Base32 — para entrada manual en la app
    uri: str              # otpauth://totp/... — para QR
    qr_code: str          # data:image/png;base64,... — imagen lista para <img>


class MfaOtpRequest(BaseModel):
    """Petición que solo lleva un código OTP de 6 dígitos."""
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class MfaVerifyRequest(BaseModel):
    """Segunda fase del login cuando MFA está activo."""
    mfa_session_token: str
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class MfaMessageResponse(BaseModel):
    message: str
