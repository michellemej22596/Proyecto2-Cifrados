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
