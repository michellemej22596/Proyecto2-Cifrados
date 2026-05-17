import hashlib

class Block:
    """
    Representa un bloque inmutable dentro del motor de trazabilidad de auditoría
    para el Ministerio de Finanzas Públicas.
    """
    
    def __init__(self, index: int, timestamp: str, sender_id: str, 
                 recipient_id: str, message_hash: str, previous_hash: str, nonce: int = 0):
        """
        Inicializa un nuevo bloque con sus propiedades obligatorias.
        """
        self.index = index
        self.timestamp = timestamp
        self.sender_id = str(sender_id)
        self.recipient_id = str(recipient_id)
        self.message_hash = message_hash
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calcula el hash del bloque actual aplicando estrictamente la fórmula del requerimiento:
        SHA-256(index + timestamp + datos + previous_hash + nonce)
        
        Los datos de la transacción consolidan de forma ordenada al remitente, destinatario 
        y el hash del mensaje.
        
        :return: Representación hexadecimal del hash SHA-256 del bloque.
        """
        # Consolidación ordenada de los datos de la transacción
        datos = f"{self.sender_id}{self.recipient_id}{self.message_hash}"
        
        # Concatenación estricta bajo la fórmula gubernamental
        block_content = f"{self.index}{self.timestamp}{datos}{self.previous_hash}{self.nonce}"
        
        hasher = hashlib.sha256()
        hasher.update(block_content.encode('utf-8'))
        return hasher.hexdigest()
