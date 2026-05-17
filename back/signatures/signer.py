import base64
import hashlib
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

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
        
        :param plaintext: El texto plano original.
        :param signature_b64: La firma codificada en Base64.
        :param public_key_pem: La llave pública del remitente en formato PEM (como string).
        :return: True si es válida, False si fue alterada o la verificación falla.
        """
        try:
            key = ECC.import_key(public_key_pem)
            signature = base64.b64decode(signature_b64)
            
            hash_obj = SHA256.new(plaintext.encode('utf-8'))
            
            verifier = DSS.new(key, 'fips-186-3')
            verifier.verify(hash_obj, signature)
            return True
        except (ValueError, TypeError):
            return False
