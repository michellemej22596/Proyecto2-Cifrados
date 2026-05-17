import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature

class DigitalSignatureService:
    """
    Servicio de Firmas Digitales para garantizar la autenticidad y el no repudio
    en el sistema de mensajería segura.
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

    @staticmethod
    def sign_message(plaintext: str, private_key_pem: str) -> str:
        """
        Toma el hash SHA-256 del mensaje original y lo firma utilizando la llave 
        privada ECDSA (curva P-256) del remitente.
        
        :param plaintext: El mensaje original en texto plano.
        :param private_key_pem: La llave privada del remitente en formato PEM (como string).
        :return: La firma resultante codificada en Base64.
        """
        private_key = load_pem_private_key(private_key_pem.encode('utf-8'), password=None)
        
        signature = private_key.sign(
            plaintext.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_message_signature(plaintext: str, signature_b64: str, public_key_pem: str) -> bool:
        """
        Verifica la validez matemática de la firma en Base64 utilizando la llave pública 
        ECDSA del remitente.
        
        :param plaintext: El texto plano original.
        :param signature_b64: La firma codificada en Base64.
        :param public_key_pem: La llave pública del remitente en formato PEM (como string).
        :return: True si es válida, False si fue alterada o la verificación falla.
        """
        try:
            public_key = load_pem_public_key(public_key_pem.encode('utf-8'))
            signature = base64.b64decode(signature_b64)
            
            public_key.verify(
                signature,
                plaintext.encode('utf-8'),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False
