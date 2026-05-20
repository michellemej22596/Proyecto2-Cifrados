import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from models import BlockModel

class Blockchain:
    """
    Motor inmutable para la trazabilidad de auditoría gubernamental.
    Maneja el libro mayor (ledger) de las transacciones de mensajes persistiendo en base de datos.
    """
    
    @staticmethod
    def _calculate_hash(index: int, timestamp: str, sender_id: str, recipient_id: str, message_hash: str, previous_hash: str, nonce: int) -> str:
        """
        Calcula el hash del bloque actual aplicando estrictamente la fórmula del requerimiento:
        SHA-256(index + timestamp + datos + previous_hash + nonce)
        """
        datos = f"{sender_id}{recipient_id}{message_hash}"
        block_content = f"{index}{timestamp}{datos}{previous_hash}{nonce}"
        hasher = hashlib.sha256()
        hasher.update(block_content.encode('utf-8'))
        return hasher.hexdigest()

    @staticmethod
    def create_genesis_block(db: Session):
        """
        Genera el primer bloque inmutable de la cadena si no existe.
        Obligatoriamente su previous_hash debe ser "0" * 64.
        """
        if db.query(BlockModel).first() is not None:
            return
            
        timestamp = datetime.now(timezone.utc).isoformat()
        genesis_block = BlockModel(
            index=0,
            timestamp=timestamp,
            sender_id="00000000-0000-0000-0000-000000000000",
            recipient_id="00000000-0000-0000-0000-000000000000",
            message_hash="0000000000000000000000000000000000000000000000000000000000000000",
            previous_hash="0" * 64,
            nonce=0
        )
        
        # Calcular el hash inicial
        genesis_block.hash = Blockchain._calculate_hash(
            0, genesis_block.timestamp, 
            genesis_block.sender_id, genesis_block.recipient_id, 
            genesis_block.message_hash, genesis_block.previous_hash, 0
        )
        
        db.add(genesis_block)
        db.commit()

    @staticmethod
    def get_latest_block(db: Session) -> BlockModel:
        """
        Retorna el último bloque añadido a la cadena.
        """
        Blockchain.create_genesis_block(db)
        return db.query(BlockModel).order_by(BlockModel.index.desc()).first()

    @staticmethod
    def get_full_chain(db: Session) -> List[BlockModel]:
        """
        Retorna toda la cadena de bloques desde la BD.
        """
        Blockchain.create_genesis_block(db)
        return db.query(BlockModel).order_by(BlockModel.index.asc()).all()

    @staticmethod
    def get_block_by_index(db: Session, index: int) -> Optional[BlockModel]:
        return db.query(BlockModel).filter(BlockModel.index == index).first()

    @staticmethod
    def add_new_transaction(db: Session, sender_id: str, recipient_id: str, message_hash: str) -> BlockModel:
        """
        Toma los datos de un mensaje recién enviado, los concatena con el hash del 
        bloque anterior, genera el nuevo bloque y lo guarda en la base de datos.
        """
        previous_block = Blockchain.get_latest_block(db)
        new_index = previous_block.index + 1
        timestamp = datetime.now(timezone.utc).isoformat()
        
        new_block = BlockModel(
            index=new_index,
            timestamp=timestamp,
            sender_id=str(sender_id),
            recipient_id=str(recipient_id),
            message_hash=message_hash,
            previous_hash=previous_block.hash,
            nonce=0
        )
        
        new_block.hash = Blockchain._calculate_hash(
            new_block.index, new_block.timestamp,
            new_block.sender_id, new_block.recipient_id,
            new_block.message_hash, new_block.previous_hash, new_block.nonce
        )
        
        db.add(new_block)
        db.commit()
        db.refresh(new_block)
        return new_block
        
    @staticmethod
    def is_chain_valid(db: Session) -> bool:
        """
        Recorre secuencialmente toda la cadena verificando su integridad.
        """
        chain = Blockchain.get_full_chain(db)
        
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            
            calc_hash = Blockchain._calculate_hash(
                current_block.index, current_block.timestamp,
                current_block.sender_id, current_block.recipient_id,
                current_block.message_hash, current_block.previous_hash, current_block.nonce
            )
            
            if current_block.hash != calc_hash:
                return False
                
            if current_block.previous_hash != previous_block.hash:
                return False
                
        return True
