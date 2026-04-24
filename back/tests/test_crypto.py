"""
Pruebas unitarias para el módulo crypto
"""

import pytest
import sys
sys.path.insert(0, '..')

from crypto import (
    hash_password,
    verify_password,
    generate_key_pair,
    decrypt_private_key,
    _derive_fernet_key,
    PBKDF2_ITERATIONS,
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
