"""
Router para endpoints de la blockchain de auditoria.
Expone la cadena de bloques y permite verificar su integridad.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List

from sqlalchemy.orm import Session
from database import get_db

from blockchain.core import Blockchain

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


# ---------------------------------------------------------------------------
# Schemas de respuesta
# ---------------------------------------------------------------------------

class BlockResponse(BaseModel):
    """Schema para representar un bloque individual."""
    index: int
    timestamp: str
    sender_id: str
    recipient_id: str
    message_hash: str
    previous_hash: str
    nonce: int
    hash: str


class BlockchainResponse(BaseModel):
    """Schema para la respuesta de la cadena completa."""
    length: int
    chain: List[BlockResponse]


class BlockchainVerifyResponse(BaseModel):
    """Schema para la respuesta de verificacion de integridad."""
    is_valid: bool
    total_blocks: int
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=BlockchainResponse)
def get_full_blockchain(db: Session = Depends(get_db)):
    """
    GET /blockchain/
    
    Retorna la cadena completa de bloques en formato JSON.
    Incluye el bloque genesis y todos los bloques de transacciones.
    """
    chain = Blockchain.get_full_chain(db)
    
    chain_data = []
    for block in chain:
        chain_data.append(BlockResponse(
            index=block.index,
            timestamp=block.timestamp,
            sender_id=block.sender_id,
            recipient_id=block.recipient_id,
            message_hash=block.message_hash,
            previous_hash=block.previous_hash,
            nonce=block.nonce,
            hash=block.hash,
        ))
    
    return BlockchainResponse(
        length=len(chain),
        chain=chain_data,
    )


@router.get("/verify", response_model=BlockchainVerifyResponse)
def verify_blockchain_integrity(db: Session = Depends(get_db)):
    """
    GET /blockchain/verify
    
    Recorre la cadena completa validando:
    1. Que el hash de cada bloque coincida con su calculo actual.
    2. Que el previous_hash de cada bloque apunte al hash del bloque anterior.
    
    Retorna el estado de integridad de la blockchain.
    """
    is_valid = Blockchain.is_chain_valid(db)
    chain = Blockchain.get_full_chain(db)
    total_blocks = len(chain)
    
    if is_valid:
        message = f"La blockchain es valida. {total_blocks} bloques verificados correctamente."
    else:
        message = "ALERTA: La blockchain ha sido comprometida. Se detectaron inconsistencias en los hashes."
    
    return BlockchainVerifyResponse(
        is_valid=is_valid,
        total_blocks=total_blocks,
        message=message,
    )


@router.get("/block/{block_index}", response_model=BlockResponse)
def get_block_by_index(block_index: int, db: Session = Depends(get_db)):
    """
    GET /blockchain/block/{block_index}
    
    Retorna un bloque especifico por su indice.
    """
    block = Blockchain.get_block_by_index(db, block_index)
    
    if block is None:
        chain = Blockchain.get_full_chain(db)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bloque con indice {block_index} no encontrado. La cadena tiene {len(chain)} bloques.",
        )
    return BlockResponse(
        index=block.index,
        timestamp=block.timestamp,
        sender_id=block.sender_id,
        recipient_id=block.recipient_id,
        message_hash=block.message_hash,
        previous_hash=block.previous_hash,
        nonce=block.nonce,
        hash=block.hash,
    )
