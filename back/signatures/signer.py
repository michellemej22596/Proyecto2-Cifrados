import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

# Intentar importar pycryptodome para ECDSA (opcional)
try:
    from Crypto.PublicKey import ECC
    from Crypto.Signature import DSS
    from Crypto.Hash import SHA256
    ECDSA_AVAILABLE = True
except ImportError:
    ECDSA_AVAILABLE = False


class DigitalSignatureService:
    """
    Servicio de Firmas Digitales para garantizar la autenticidad y el no repudio
    en el sistema de mensajería segura.
    
    Soporta tanto RSA-PSS (para llaves RSA existentes) como ECDSA (P-256).
    """
    
    @staticmethod
    def calculate_message_hash(plaintext: str) -> str:
        """
        Calcula y retorna el hash SHA-256 del texto plano original del mensaje.
        
        :param plaintext: El texto plano a ser hasheado.
        :return: Representación hexadecimal del hash SHA-256.
        """
        hasher = hashlib.sha256()
        hasher.update(plaintext.encode('utf-8'))
        return hasher.hexdigest()

    # ---------------------------------------------------------------------------
    # RSA-PSS Signatures (compatible con las llaves RSA del sistema)
    # ---------------------------------------------------------------------------

    @staticmethod
    def sign_message_rsa(plaintext: str, private_key_pem: bytes) -> str:
        """
        Firma el mensaje usando RSA-PSS con SHA-256.
        Compatible con las llaves RSA-2048 generadas en el registro de usuarios.
        
        :param plaintext: El mensaje original en texto plano.
        :param private_key_pem: La llave privada RSA en formato PEM (bytes).
        :return: La firma resultante codificada en Base64.
        """
        private_key = load_pem_private_key(private_key_pem, password=None)
        
        signature = private_key.sign(
            plaintext.encode('utf-8'),
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_message_signature_rsa(plaintext: str, signature_b64: str, public_key_pem: str) -> bool:
        """
        Verifica la validez de una firma RSA-PSS usando la llave pública del remitente.
        
        :param plaintext: El texto plano original.
        :param signature_b64: La firma codificada en Base64.
        :param public_key_pem: La llave pública RSA del remitente en formato PEM.
        :return: True si es válida, False si fue alterada o la verificación falla.
        """
        try:
            public_key = load_pem_public_key(public_key_pem.encode())
            signature = base64.b64decode(signature_b64)
            
            public_key.verify(
                signature,
                plaintext.encode('utf-8'),
                asym_padding.PSS(
                    mgf=asym_padding.MGF1(hashes.SHA256()),
                    salt_length=asym_padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    # ---------------------------------------------------------------------------
    # ECDSA Signatures (requiere pycryptodome)
    # ---------------------------------------------------------------------------

    @staticmethod
    def sign_message(plaintext: str, private_key_pem: str) -> str:
        """
        Toma el hash SHA-256 del mensaje original y lo firma utilizando la llave 
        privada ECDSA (curva P-256) del remitente.
        
        NOTA: Requiere pycryptodome instalado y una llave ECC.
        Para llaves RSA, usar sign_message_rsa().
        
        :param plaintext: El mensaje original en texto plano.
        :param private_key_pem: La llave privada del remitente en formato PEM (como string).
        :return: La firma resultante codificada en Base64.
        """
        if not ECDSA_AVAILABLE:
            raise ImportError("pycryptodome no está instalado. Use sign_message_rsa() para llaves RSA.")
            
        hash_obj = SHA256.new(plaintext.encode('utf-8'))
        key = ECC.import_key(private_key_pem)
        signer = DSS.new(key, 'fips-186-3')
        
        signature = signer.sign(hash_obj)
        
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_message_signature(plaintext: str, signature_b64: str, public_key_pem: str) -> bool:
        """
        Verifica la validez matemática de la firma en Base64 utilizando la llave pública 
        ECDSA del remitente.
        
        NOTA: Requiere pycryptodome instalado y una llave ECC.
        Para llaves RSA, usar verify_message_signature_rsa().
        
        :param plaintext: El texto plano original.
        :param signature_b64: La firma codificada en Base64.
        :param public_key_pem: La llave pública del remitente en formato PEM (como string).
        :return: True si es válida, False si fue alterada o la verificación falla.
        """
        if not ECDSA_AVAILABLE:
            raise ImportError("pycryptodome no está instalado. Use verify_message_signature_rsa() para llaves RSA.")
            
        try:
            key = ECC.import_key(public_key_pem)
            signature = base64.b64decode(signature_b64)
            
            hash_obj = SHA256.new(plaintext.encode('utf-8'))
            
            verifier = DSS.new(key, 'fips-186-3')
            verifier.verify(hash_obj, signature)
            return True
        except (ValueError, TypeError):
            return False
