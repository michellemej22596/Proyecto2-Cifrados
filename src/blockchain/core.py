import hashlib
from datetime import datetime, timezone
from typing import List

class Block:

    
    def __init__(self, index: int, timestamp: str, sender_id: str, 
                 recipient_id: str, message_hash: str, previous_hash: str, nonce: int = 0):
   
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
        datos = f"{self.sender_id}{self.recipient_id}{self.message_hash}"
        
        block_content = f"{self.index}{self.timestamp}{datos}{self.previous_hash}{self.nonce}"
        
        hasher = hashlib.sha256()
        hasher.update(block_content.encode('utf-8'))
        return hasher.hexdigest()


class Blockchain:
    """
    Motor inmutable para la trazabilidad de auditoría gubernamental.
    Maneja el libro mayor (ledger) de las transacciones de mensajes.
    """
    
    def __init__(self):
        self.chain: List[Block] = []
        self.create_genesis_block()
        
    def create_genesis_block(self):
        """
        Genera el primer bloque inmutable de la cadena (bloque génesis).
        Obligatoriamente su previous_hash debe ser "0" * 64.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        genesis_block = Block(
            index=0,
            timestamp=timestamp,
            sender_id="SISTEMA_GOB",
            recipient_id="MINISTERIO_FINANZAS",
            message_hash="0000000000000000000000000000000000000000000000000000000000000000",
            previous_hash="0" * 64,
            nonce=0
        )
        self.chain.append(genesis_block)
        
    def get_latest_block(self) -> Block:
        """
        Retorna el último bloque añadido a la cadena.
        """
        return self.chain[-1]
        
    def add_new_transaction(self, sender_id: str, recipient_id: str, message_hash: str) -> Block:
        """
        Toma los datos de un mensaje recién enviado, los concatena con el hash del 
        bloque anterior, genera el nuevo bloque y lo añade a la cadena de forma dinámica.
        
        :param sender_id: Identificador/UUID del remitente.
        :param recipient_id: Identificador/UUID del destinatario.
        :param message_hash: El hash SHA-256 del texto plano original del mensaje.
        :return: El bloque generado e insertado en la cadena.
        """
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1
        timestamp = datetime.now(timezone.utc).isoformat()
        
        new_block = Block(
            index=new_index,
            timestamp=timestamp,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_hash=message_hash,
            previous_hash=previous_block.hash,
            nonce=0
        )
        
        self.chain.append(new_block)
        return new_block
        
    def is_chain_valid(self) -> bool:
        """
        Recorre secuencialmente toda la cadena verificando:
        1) Que el hash guardado de cada bloque coincida con su cálculo matemático actual.
        2) Que el previous_hash de un bloque apunte de manera exacta al hash del bloque predecesor.
        
        :return: True si la cadena mantiene su integridad inmutable, False si fue alterada.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
                
            if current_block.previous_hash != previous_block.hash:
                return False
                
        return True
