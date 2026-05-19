from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    public_key_pem = Column(String, nullable=False)
    # Formato: "<base64_pbkdf2_salt>.<fernet_token>"
    encrypted_private_key = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ciphertext = Column(String, nullable=False)
    encrypted_key = Column(String, nullable=True)
    nonce = Column(String, nullable=False)
    auth_tag = Column(String, nullable=True)
    # Campo de firma digital (RSA-PSS o ECDSA) - Base64 encoded
    signature = Column(String, nullable=True)
    # Estado de verificación: VERIFIED, NOT_VERIFIED, PENDING
    verification_status = Column(String, nullable=True, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encrypted_group_key = Column(String, nullable=False)


class GroupMessage(Base):
    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ciphertext = Column(String, nullable=False)
    nonce = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
