"""
Pruebas unitarias para el módulo crypto
"""
import os
import base64
import pytest
from datetime import timedelta
from jose import jwt
import sys
sys.path.insert(0, '..')

from crypto import (
    # Hashing
    hash_password,
    verify_password,
    # Key derivation
    #derive_key_from_password,
    PBKDF2_ITERATIONS,
    _derive_fernet_key,
    # RSA
    generate_key_pair,
    decrypt_private_key,
    encrypt_aes_key_rsa_oaep,
    decrypt_aes_key_rsa_oaep,
    # AES-GCM
    encrypt_message_aes_gcm,
    decrypt_message_aes_gcm,
    # Hybrid
    encrypt_message_hybrid,
    decrypt_message_hybrid,
    # JWT
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

class TestPasswordHashing:
    """Pruebas para el hashing de contraseñas con bcrypt."""

    def test_hash_password_returns_string(self):
        """El hash de contraseña debe retornar un string."""
        password = "mi_contraseña_segura_123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # Prefijo de bcrypt

    def test_hash_password_different_hashes(self):
        """Dos llamadas con la misma contraseña deben generar hashes diferentes (por el salt)."""
        password = "contraseña_test"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Diferentes salts = diferentes hashes

    def test_verify_password_correct(self):
        """verify_password debe retornar True para contraseña correcta."""
        password = "password123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password debe retornar False para contraseña incorrecta."""
        password = "password_correcta"
        wrong_password = "password_incorrecta"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_with_special_characters(self):
        """El hash debe funcionar con caracteres especiales y unicode."""
        password = "contraseña_ñ_áéíóú_@#$%_日本語"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


class TestKeyDerivation:
    """Pruebas para la derivación de claves con PBKDF2."""

    def test_derive_fernet_key_returns_valid_key(self):
        """La clave derivada debe tener el formato correcto para Fernet (44 bytes base64)."""
        password = "mi_password"
        salt = b"0123456789abcdef"  # 16 bytes

        key = _derive_fernet_key(password, salt)

        assert isinstance(key, bytes)
        assert len(key) == 44  # 32 bytes en base64 urlsafe = 44 caracteres

    def test_derive_fernet_key_deterministic(self):
        """La misma contraseña y salt deben producir la misma clave."""
        password = "password_test"
        salt = b"salt_fijo_16byt"

        key1 = _derive_fernet_key(password, salt)
        key2 = _derive_fernet_key(password, salt)

        assert key1 == key2

    def test_derive_fernet_key_different_salts(self):
        """Diferentes salts deben producir diferentes claves."""
        password = "mismo_password"
        salt1 = b"primer_salt_16by"
        salt2 = b"segundo_salt_16b"

        key1 = _derive_fernet_key(password, salt1)
        key2 = _derive_fernet_key(password, salt2)

        assert key1 != key2

    def test_pbkdf2_iterations_value(self):
        """Las iteraciones de PBKDF2 deben ser al menos 600,000 (recomendación OWASP)."""
        assert PBKDF2_ITERATIONS >= 600_000


class TestRSAKeyPair:
    """Pruebas para la generación y cifrado de par de llaves RSA."""

    def test_generate_key_pair_returns_tuple(self):
        """generate_key_pair debe retornar una tupla de dos strings."""
        password = "password_para_cifrar"

        result = generate_key_pair(password)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # public_key_pem
        assert isinstance(result[1], str)  # encrypted_private_key

    def test_public_key_is_valid_pem(self):
        """La llave pública debe estar en formato PEM válido."""
        password = "test_password"
        public_key_pem, _ = generate_key_pair(password)

        assert "-----BEGIN PUBLIC KEY-----" in public_key_pem
        assert "-----END PUBLIC KEY-----" in public_key_pem

    def test_encrypted_private_key_format(self):
        """La llave privada cifrada debe tener el formato 'salt.token'."""
        password = "test_password"
        _, encrypted_private_key = generate_key_pair(password)

        parts = encrypted_private_key.split(".")
        assert len(parts) == 2
        assert len(parts[0]) > 0  # salt base64
        assert len(parts[1]) > 0  # fernet token

    def test_decrypt_private_key_success(self):
        """Debe poder descifrar la llave privada con la contraseña correcta."""
        password = "mi_contraseña_secreta"
        public_key_pem, encrypted_private_key = generate_key_pair(password)

        decrypted = decrypt_private_key(password, encrypted_private_key)

        assert isinstance(decrypted, bytes)
        assert b"-----BEGIN PRIVATE KEY-----" in decrypted
        assert b"-----END PRIVATE KEY-----" in decrypted

    def test_decrypt_private_key_wrong_password_fails(self):
        """Descifrar con contraseña incorrecta debe lanzar excepción."""
        password = "contraseña_correcta"
        wrong_password = "contraseña_incorrecta"
        _, encrypted_private_key = generate_key_pair(password)

        with pytest.raises(Exception):  # Fernet.InvalidToken
            decrypt_private_key(wrong_password, encrypted_private_key)

    def test_key_pairs_are_unique(self):
        """Cada llamada debe generar un par de llaves diferente."""
        password = "mismo_password"

        public1, private1 = generate_key_pair(password)
        public2, private2 = generate_key_pair(password)

        assert public1 != public2
        assert private1 != private2


class TestIntegration:
    """Pruebas de integración del flujo completo."""

    def test_full_registration_flow(self):
        """Simula el flujo completo de registro de usuario."""
        # 1. Usuario proporciona credenciales
        username = "usuario_test"
        password = "Password123!@#"

        # 2. Hashear contraseña para almacenar
        password_hash = hash_password(password)

        # 3. Generar par de llaves
        public_key, encrypted_private_key = generate_key_pair(password)

        # 4. Verificar que se puede autenticar
        assert verify_password(password, password_hash) is True

        # 5. Verificar que se puede recuperar la llave privada
        decrypted_key = decrypt_private_key(password, encrypted_private_key)
        assert b"PRIVATE KEY" in decrypted_key

    def test_password_change_scenario(self):
        """Simula el escenario de cambio de contraseña."""
        old_password = "contraseña_vieja"
        new_password = "contraseña_nueva"

        # Registro inicial
        old_hash = hash_password(old_password)
        public_key, encrypted_private_key = generate_key_pair(old_password)

        # Descifrar con contraseña vieja
        private_key_bytes = decrypt_private_key(old_password, encrypted_private_key)

        # Re-cifrar con contraseña nueva (simulado regenerando)
        new_hash = hash_password(new_password)
        _, new_encrypted_private_key = generate_key_pair(new_password)

        # Verificar nuevo hash
        assert verify_password(new_password, new_hash) is True
        assert verify_password(old_password, new_hash) is False


class TestJWT:
    """Pruebas para la generación de tokens JWT."""

    def test_create_access_token_returns_string(self):
        """El token JWT debe ser un string válido."""
        data = {"sub": "user_123", "role": "admin"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_is_decodable(self):
        """El token debe poder decodificarse con la misma clave."""
        from jose import jwt
        from crypto import SECRET_KEY, ALGORITHM

        data = {"sub": "user_456"}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "user_456"

    def test_create_access_token_with_custom_expiry(self):
        """Debe respetar el tiempo de expiración personalizado."""
        from datetime import timedelta

        data = {"sub": "user_789"}
        token = create_access_token(data, expires_delta=timedelta(minutes=5))
        assert isinstance(token, str)

    def test_create_access_token_contains_exp_claim(self):
        """El token debe incluir el claim 'exp'."""
        from jose import jwt
        from crypto import SECRET_KEY, ALGORITHM

        token = create_access_token({"sub": "test"})
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded


class TestAESGCM:
    """Pruebas para cifrado simétrico AES-GCM."""

    def test_encrypt_message_returns_tuple(self):
        """encrypt_message_aes_gcm debe retornar (ciphertext, nonce)."""
        plaintext = "Mensaje secreto"
        result = encrypt_message_aes_gcm(plaintext)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_encrypt_decrypt_roundtrip(self):
        """El mensaje descifrado debe coincidir con el original."""
        plaintext = "Texto de prueba para cifrar"
        ciphertext, nonce = encrypt_message_aes_gcm(plaintext)
        decrypted = decrypt_message_aes_gcm(ciphertext, nonce)

        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext(self):
        """Cada cifrado debe generar un ciphertext diferente (nonce único)."""
        plaintext = "Mismo mensaje"
        ct1, nonce1 = encrypt_message_aes_gcm(plaintext)
        ct2, nonce2 = encrypt_message_aes_gcm(plaintext)

        assert ct1 != ct2
        assert nonce1 != nonce2

    def test_decrypt_with_wrong_nonce_fails(self):
        """Descifrar con nonce incorrecto debe fallar."""
        plaintext = "Mensaje"
        ciphertext, _ = encrypt_message_aes_gcm(plaintext)
        wrong_nonce = base64.urlsafe_b64encode(os.urandom(12)).decode()

        with pytest.raises(Exception):
            decrypt_message_aes_gcm(ciphertext, wrong_nonce)

    def test_encrypt_unicode_message(self):
        """Debe manejar mensajes con caracteres unicode."""
        plaintext = "Mensaje con ñ, émojis 🔐 y 日本語"
        ciphertext, nonce = encrypt_message_aes_gcm(plaintext)
        decrypted = decrypt_message_aes_gcm(ciphertext, nonce)

        assert decrypted == plaintext


class TestRSAOAEP:
    """Pruebas para cifrado de claves AES con RSA-OAEP."""

    def test_encrypt_aes_key_returns_string(self):
        """encrypt_aes_key_rsa_oaep debe retornar un string base64."""
        public_key, _ = generate_key_pair("password")
        aes_key = os.urandom(32)

        encrypted = encrypt_aes_key_rsa_oaep(public_key, aes_key)

        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

    def test_encrypt_decrypt_aes_key_roundtrip(self):
        """La clave AES descifrada debe coincidir con la original."""
        password = "test_password"
        public_key, encrypted_private = generate_key_pair(password)
        private_key = decrypt_private_key(password, encrypted_private)

        original_aes_key = os.urandom(32)
        encrypted_key = encrypt_aes_key_rsa_oaep(public_key, original_aes_key)
        decrypted_key = decrypt_aes_key_rsa_oaep(private_key, encrypted_key)

        assert decrypted_key == original_aes_key

    def test_decrypt_with_wrong_private_key_fails(self):
        """Descifrar con llave privada incorrecta debe fallar."""
        public_key1, _ = generate_key_pair("password1")
        _, encrypted_private2 = generate_key_pair("password2")
        private_key2 = decrypt_private_key("password2", encrypted_private2)

        aes_key = os.urandom(32)
        encrypted = encrypt_aes_key_rsa_oaep(public_key1, aes_key)

        with pytest.raises(Exception):
            decrypt_aes_key_rsa_oaep(private_key2, encrypted)


class TestHybridEncryption:
    """Pruebas para cifrado híbrido RSA-OAEP + AES-GCM."""

    def test_encrypt_message_hybrid_returns_dict(self):
        """encrypt_message_hybrid debe retornar un dict con las claves correctas."""
        public_key, _ = generate_key_pair("password")
        plaintext = "Mensaje híbrido"

        result = encrypt_message_hybrid(plaintext, public_key)

        assert isinstance(result, dict)
        assert "ciphertext" in result
        assert "nonce" in result
        assert "encrypted_key" in result

    def test_hybrid_encrypt_decrypt_roundtrip(self):
        """El flujo completo de cifrado/descifrado híbrido debe funcionar."""
        password = "recipient_password"
        public_key, encrypted_private = generate_key_pair(password)
        private_key = decrypt_private_key(password, encrypted_private)

        plaintext = "Mensaje confidencial para el destinatario"
        encrypted = encrypt_message_hybrid(plaintext, public_key)

        decrypted = decrypt_message_hybrid(
            private_key,
            encrypted["encrypted_key"],
            encrypted["ciphertext"],
            encrypted["nonce"],
        )

        assert decrypted == plaintext

    def test_hybrid_encryption_different_outputs(self):
        """Cada cifrado debe producir resultados diferentes."""
        public_key, _ = generate_key_pair("password")
        plaintext = "Mismo mensaje"

        enc1 = encrypt_message_hybrid(plaintext, public_key)
        enc2 = encrypt_message_hybrid(plaintext, public_key)

        assert enc1["ciphertext"] != enc2["ciphertext"]
        assert enc1["encrypted_key"] != enc2["encrypted_key"]

    def test_hybrid_with_unicode_message(self):
        """Debe funcionar con mensajes unicode."""
        password = "pass"
        public_key, encrypted_private = generate_key_pair(password)
        private_key = decrypt_private_key(password, encrypted_private)

        plaintext = "Mensaje con émojis 🔑🔒 y caracteres especiales ñáéíóú"
        encrypted = encrypt_message_hybrid(plaintext, public_key)
        decrypted = decrypt_message_hybrid(
            private_key,
            encrypted["encrypted_key"],
            encrypted["ciphertext"],
            encrypted["nonce"],
        )

        assert decrypted == plaintext


class TestSecurityEdgeCases:
    """Pruebas de seguridad y casos límite."""

    def test_empty_password_handling(self):
        """Debe manejar contraseñas vacías (aunque no recomendado)."""
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_very_long_password(self):
        """Debe manejar contraseñas muy largas."""
        password = "a" * 1000
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_empty_message_encryption(self):
        """Debe cifrar mensajes vacíos."""
        ciphertext, nonce = encrypt_message_aes_gcm("")
        decrypted = decrypt_message_aes_gcm(ciphertext, nonce)
        assert decrypted == ""

    def test_large_message_hybrid_encryption(self):
        """Debe manejar mensajes grandes."""
        password = "pass"
        public_key, encrypted_private = generate_key_pair(password)
        private_key = decrypt_private_key(password, encrypted_private)

        plaintext = "X" * 100_000  # 100KB
        encrypted = encrypt_message_hybrid(plaintext, public_key)
        decrypted = decrypt_message_hybrid(
            private_key,
            encrypted["encrypted_key"],
            encrypted["ciphertext"],
            encrypted["nonce"],
        )

        assert decrypted == plaintext


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
