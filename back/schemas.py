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


class HybridMessageResponse(BaseModel):
    id: int
    sender_id: int | None = None
    recipient_id: int | None = None
    ciphertext: str
    encrypted_key: str | None = None
    nonce: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageDecryptRequest(BaseModel):
    password: str


class MessageDecryptResponse(BaseModel):
    plaintext: str

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1)
    member_ids: list[int]


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