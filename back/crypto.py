import os
import base64
import bcrypt
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding, ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import hashlib

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

def _load_or_create_secret_key() -> str:
    """Carga el SECRET_KEY con la siguiente prioridad:
    1. Variable de entorno SECRET_KEY (configuración explícita)
    2. Archivo persistido en el volumen Docker /app/data/.secret_key
    3. Genera uno nuevo y lo guarda en el archivo para reutilizarlo tras reinicios
    """
    # 1. Variable de entorno tiene máxima prioridad
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key

    # 2. Intentar leer desde archivo persistido en el volumen
    key_file = Path("/app/data/.secret_key")
    try:
        if key_file.exists():
            stored = key_file.read_text().strip()
            if stored:
                return stored
    except OSError:
        pass

    # 3. Generar nueva clave y persistirla para sobrevivir reinicios
    new_key = secrets.token_urlsafe(32)
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(new_key)
        # Permisos restrictivos: solo el propietario puede leer/escribir
        key_file.chmod(0o600)
    except OSError:
        # Si no se puede persistir (e.g. entorno de desarrollo sin /app/data)
        # simplemente se usa en memoria — mismo comportamiento que antes
        pass

    return new_key


SECRET_KEY = _load_or_create_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def _aes_gcm_encrypt(plaintext: str, key: bytes) -> tuple[str, str, str]:
    """Cifra con AES-256-GCM y devuelve (ciphertext_b64, nonce_b64, auth_tag_b64).

    AESGCM.encrypt() concatena ciphertext || tag (tag = últimos 16 bytes).
    Esta función los separa para que el tag quede almacenado de forma explícita.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    encrypted = aesgcm.encrypt(nonce, plaintext.encode(), None)
    ciphertext, auth_tag = encrypted[:-16], encrypted[-16:]
    return (
        base64.urlsafe_b64encode(ciphertext).decode(),
        base64.urlsafe_b64encode(nonce).decode(),
        base64.urlsafe_b64encode(auth_tag).decode(),
    )


# ---------------------------------------------------------------------------
# Cifrado híbrido: RSA-OAEP + AES-256-GCM
# ---------------------------------------------------------------------------

def encrypt_aes_key_rsa_oaep(public_key_pem: str, aes_key: bytes) -> str:
    """Cifra una clave AES con la llave pública RSA del destinatario (OAEP/SHA-256)."""
    public_key = load_pem_public_key(public_key_pem.encode())
    encrypted = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_aes_key_rsa_oaep(private_key_pem: bytes, encrypted_key_b64: str) -> bytes:
    """Recupera la clave AES usando la llave privada RSA del destinatario (OAEP/SHA-256)."""
    private_key = load_pem_private_key(private_key_pem, password=None)
    encrypted_key = base64.urlsafe_b64decode(encrypted_key_b64)
    return private_key.decrypt(
        encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def encrypt_message_hybrid(plaintext: str, recipient_public_key_pem: str) -> dict:
    """Genera una clave AES-256 efímera, cifra con _aes_gcm_encrypt,
    y cifra la clave AES con la llave pública RSA-OAEP del destinatario."""
    aes_key = os.urandom(32)
    ciphertext, nonce, auth_tag = _aes_gcm_encrypt(plaintext, aes_key)
    return {
        "ciphertext": ciphertext,
        "nonce": nonce,
        "auth_tag": auth_tag,
        "encrypted_key": encrypt_aes_key_rsa_oaep(recipient_public_key_pem, aes_key),
    }


def decrypt_message_hybrid(
    private_key_pem: bytes,
    encrypted_key_b64: str,
    ciphertext_b64: str,
    nonce_b64: str,
    auth_tag_b64: str,
) -> str:
    """Recupera la clave AES con RSA-OAEP y descifra el mensaje verificando el auth tag."""
    aes_key = decrypt_aes_key_rsa_oaep(private_key_pem, encrypted_key_b64)
    aesgcm = AESGCM(aes_key)
    nonce = base64.urlsafe_b64decode(nonce_b64)
    ciphertext = base64.urlsafe_b64decode(ciphertext_b64)
    auth_tag = base64.urlsafe_b64decode(auth_tag_b64)
    return aesgcm.decrypt(nonce, ciphertext + auth_tag, None).decode()


# ---------------------------------------------------------------------------
# ECDSA P-256 key pair generation para firmas digitales
# ---------------------------------------------------------------------------

def generate_ecdsa_key_pair(password: str) -> tuple[str, str]:
    """Genera un par de llaves ECDSA (curva P-256) para firmas digitales.
    
    La llave privada se cifra con Fernet usando una clave derivada con PBKDF2
    de la contraseña del usuario. El resultado se almacena como:
        <base64(salt)>.<fernet_token>
    
    Returns:
        tuple[str, str]: (ecdsa_public_key_pem, encrypted_ecdsa_private_key)
    """
    # Generar par de llaves ECDSA con curva P-256 (SECP256R1)
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Exportar llave pública en formato PEM
    public_key_pem: str = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    
    # Exportar llave privada en formato PEM (sin cifrar, para luego cifrar con Fernet)
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


# ---------------------------------------------------------------------------
# MFA — cifrado del secreto TOTP con clave derivada del SECRET_KEY del servidor
# ---------------------------------------------------------------------------

def _get_mfa_fernet() -> Fernet:
    """Fernet cuya clave se deriva del SECRET_KEY del servidor (SHA-256 → base64url)."""
    raw = hashlib.sha256(SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt_mfa_secret(secret: str) -> str:
    """Cifra el secreto TOTP antes de guardarlo en la BD."""
    return _get_mfa_fernet().encrypt(secret.encode()).decode()


def decrypt_mfa_secret(encrypted: str) -> str:
    """Descifra el secreto TOTP almacenado en la BD."""
    return _get_mfa_fernet().decrypt(encrypted.encode()).decode()


def decrypt_ecdsa_private_key(password: str, encrypted_private_key: str) -> bytes:
    """Descifra la llave privada ECDSA almacenada.
    
    Args:
        password: Contraseña del usuario
        encrypted_private_key: Llave cifrada en formato "<base64_salt>.<fernet_token>"
    
    Returns:
        bytes: Llave privada ECDSA en formato PEM
    """
    salt_b64, token = encrypted_private_key.split(".", 1)
    pbkdf2_salt = base64.urlsafe_b64decode(salt_b64)
    fernet_key = _derive_fernet_key(password, pbkdf2_salt)
    return Fernet(fernet_key).decrypt(token.encode())
