import os
import base64
import bcrypt
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

load_dotenv(Path(__file__).resolve().parent / ".env")

# ---------------------------------------------------------------------------
# Password hashing — bcrypt
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Key derivation — PBKDF2-HMAC-SHA256
# ---------------------------------------------------------------------------

PBKDF2_ITERATIONS = 600_000


def _derive_fernet_key(password: str, salt: bytes) -> bytes:
    """Deriva 32 bytes desde la contraseña usando PBKDF2, luego los
    codifica en base64-urlsafe para que Fernet los acepte."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    raw_key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(raw_key)


# ---------------------------------------------------------------------------
# RSA-2048 key pair generation + private key encryption
# ---------------------------------------------------------------------------

def generate_key_pair(password: str) -> tuple[str, str]:
    """Genera un par RSA-2048 y retorna (public_key_pem, encrypted_private_key).

    La llave privada se cifra con Fernet usando una clave derivada con PBKDF2
    de la contraseña del usuario.  El resultado se almacena como:
        <base64(salt)>.<fernet_token>
    para poder re-derivar la clave al momento de descifrar.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key_pem: str = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    private_key_pem: bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Cifrar la llave privada con clave derivada de la contraseña
    pbkdf2_salt = os.urandom(16)
    fernet_key = _derive_fernet_key(password, pbkdf2_salt)
    token = Fernet(fernet_key).encrypt(private_key_pem)

    # Serializar como "<base64_salt>.<fernet_token>"
    salt_b64 = base64.urlsafe_b64encode(pbkdf2_salt).decode()
    encrypted_private_key = f"{salt_b64}.{token.decode()}"

    return public_key_pem, encrypted_private_key


def decrypt_private_key(password: str, encrypted_private_key: str) -> bytes:
    """Descifra la llave privada almacenada."""
    salt_b64, token = encrypted_private_key.split(".", 1)
    pbkdf2_salt = base64.urlsafe_b64decode(salt_b64)
    fernet_key = _derive_fernet_key(password, pbkdf2_salt)
    return Fernet(fernet_key).decrypt(token.encode())


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)