"""
Pruebas unitarias para el Modulo 3: Firmas Digitales y Mini Blockchain.
Valida firmas ECDSA validas/invalidas e integridad de la blockchain.
"""
import pytest
import sys
sys.path.insert(0, '..')

from signatures.signer import DigitalSignatureService
from blockchain.core import Blockchain
from models import BlockModel, Base
from Crypto.PublicKey import ECC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Crea una base de datos SQLite en memoria para las pruebas."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


class TestDigitalSignatureService:
    """Pruebas para el servicio de firmas digitales ECDSA."""

    @pytest.fixture
    def ecdsa_key_pair(self):
        """Genera un par de llaves ECDSA para las pruebas."""
        private_key = ECC.generate(curve='P-256')
        public_key = private_key.public_key()
        return {
            'private_pem': private_key.export_key(format='PEM'),
            'public_pem': public_key.export_key(format='PEM'),
        }

    def test_calculate_message_hash_returns_hex_string(self):
        """El hash del mensaje debe ser un string hexadecimal de 64 caracteres (SHA-256)."""
        plaintext = "Mensaje de prueba"
        
        hash_result = DigitalSignatureService.calculate_message_hash(plaintext)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 = 256 bits = 64 hex chars
        assert all(c in '0123456789abcdef' for c in hash_result)

    def test_calculate_message_hash_deterministic(self):
        """El mismo mensaje debe producir el mismo hash."""
        plaintext = "Mensaje consistente"
        
        hash1 = DigitalSignatureService.calculate_message_hash(plaintext)
        hash2 = DigitalSignatureService.calculate_message_hash(plaintext)
        
        assert hash1 == hash2

    def test_calculate_message_hash_different_messages(self):
        """Mensajes diferentes deben producir hashes diferentes."""
        hash1 = DigitalSignatureService.calculate_message_hash("Mensaje A")
        hash2 = DigitalSignatureService.calculate_message_hash("Mensaje B")
        
        assert hash1 != hash2

    def test_sign_message_returns_base64_string(self, ecdsa_key_pair):
        """La firma debe retornar un string codificado en Base64."""
        plaintext = "Mensaje a firmar"
        
        signature = DigitalSignatureService.sign_message(
            plaintext, 
            ecdsa_key_pair['private_pem']
        )
        
        assert isinstance(signature, str)
        assert len(signature) > 0
        # Verificar que es Base64 valido
        import base64
        try:
            decoded = base64.b64decode(signature)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("La firma no es un Base64 valido")

    def test_verify_valid_signature(self, ecdsa_key_pair):
        """Verificar una firma valida debe retornar True."""
        plaintext = "Mensaje confidencial del gobierno"
        
        signature = DigitalSignatureService.sign_message(
            plaintext,
            ecdsa_key_pair['private_pem']
        )
        
        is_valid = DigitalSignatureService.verify_message_signature(
            plaintext,
            signature,
            ecdsa_key_pair['public_pem']
        )
        
        assert is_valid is True

    def test_verify_invalid_signature_wrong_message(self, ecdsa_key_pair):
        """Verificar firma con mensaje alterado debe retornar False."""
        original_message = "Mensaje original"
        altered_message = "Mensaje alterado por atacante"
        
        signature = DigitalSignatureService.sign_message(
            original_message,
            ecdsa_key_pair['private_pem']
        )
        
        is_valid = DigitalSignatureService.verify_message_signature(
            altered_message,
            signature,
            ecdsa_key_pair['public_pem']
        )
        
        assert is_valid is False

    def test_verify_invalid_signature_wrong_key(self, ecdsa_key_pair):
        """Verificar firma con llave publica incorrecta debe retornar False."""
        plaintext = "Mensaje firmado"
        
        # Firmar con una llave
        signature = DigitalSignatureService.sign_message(
            plaintext,
            ecdsa_key_pair['private_pem']
        )
        
        # Generar otra llave publica diferente
        other_key = ECC.generate(curve='P-256')
        other_public_pem = other_key.public_key().export_key(format='PEM')
        
        is_valid = DigitalSignatureService.verify_message_signature(
            plaintext,
            signature,
            other_public_pem
        )
        
        assert is_valid is False

    def test_verify_corrupted_signature(self, ecdsa_key_pair):
        """Verificar una firma corrupta debe retornar False."""
        plaintext = "Mensaje seguro"
        
        signature = DigitalSignatureService.sign_message(
            plaintext,
            ecdsa_key_pair['private_pem']
        )
        
        # Corromper la firma
        corrupted_signature = signature[:-4] + "XXXX"
        
        is_valid = DigitalSignatureService.verify_message_signature(
            plaintext,
            corrupted_signature,
            ecdsa_key_pair['public_pem']
        )
        
        assert is_valid is False

    def test_sign_unicode_message(self, ecdsa_key_pair):
        """Debe firmar y verificar mensajes con caracteres unicode."""
        plaintext = "Mensaje con acentos: ñ, á, é, 日本語, emojis 🔐🔑"
        
        signature = DigitalSignatureService.sign_message(
            plaintext,
            ecdsa_key_pair['private_pem']
        )
        
        is_valid = DigitalSignatureService.verify_message_signature(
            plaintext,
            signature,
            ecdsa_key_pair['public_pem']
        )
        
        assert is_valid is True


class TestBlockchain:
    """Pruebas para la clase Blockchain usando SQLite en memoria."""

    def test_blockchain_creates_genesis_block(self, db_session):
        """La blockchain debe inicializarse con un bloque genesis."""
        Blockchain.create_genesis_block(db_session)
        chain = Blockchain.get_full_chain(db_session)
        
        assert len(chain) == 1
        genesis = chain[0]
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64

    def test_genesis_block_has_correct_structure(self, db_session):
        """El bloque genesis debe tener la estructura correcta."""
        Blockchain.create_genesis_block(db_session)
        chain = Blockchain.get_full_chain(db_session)
        genesis = chain[0]
        
        assert genesis.sender_id == "00000000-0000-0000-0000-000000000000"
        assert genesis.recipient_id == "00000000-0000-0000-0000-000000000000"
        assert genesis.message_hash == "0" * 64

    def test_add_new_transaction(self, db_session):
        """Agregar una transaccion debe crear un nuevo bloque."""
        Blockchain.create_genesis_block(db_session)
        initial_length = len(Blockchain.get_full_chain(db_session))
        
        new_block = Blockchain.add_new_transaction(
            db_session,
            sender_id="user-1",
            recipient_id="user-2",
            message_hash="abc123def456"
        )
        
        assert len(Blockchain.get_full_chain(db_session)) == initial_length + 1
        assert new_block.index == 1
        assert new_block.sender_id == "user-1"
        assert new_block.recipient_id == "user-2"
        assert new_block.message_hash == "abc123def456"

    def test_blocks_are_chained_correctly(self, db_session):
        """Cada bloque nuevo debe apuntar al hash del bloque anterior."""
        Blockchain.create_genesis_block(db_session)
        
        Blockchain.add_new_transaction(db_session, "sender1", "recipient1", "hash1")
        Blockchain.add_new_transaction(db_session, "sender2", "recipient2", "hash2")
        Blockchain.add_new_transaction(db_session, "sender3", "recipient3", "hash3")
        
        chain = Blockchain.get_full_chain(db_session)
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            assert current.previous_hash == previous.hash

    def test_is_chain_valid_returns_true_for_valid_chain(self, db_session):
        """Una cadena valida debe retornar True en is_chain_valid."""
        Blockchain.create_genesis_block(db_session)
        Blockchain.add_new_transaction(db_session, "sender1", "recipient1", "hash1")
        Blockchain.add_new_transaction(db_session, "sender2", "recipient2", "hash2")
        
        assert Blockchain.is_chain_valid(db_session) is True

    def test_is_chain_valid_detects_tampered_hash(self, db_session):
        """Debe detectar si el hash de un bloque fue alterado."""
        Blockchain.create_genesis_block(db_session)
        Blockchain.add_new_transaction(db_session, "sender1", "recipient1", "hash1")
        
        # Alterar el hash del bloque 1 (simular ataque en DB)
        block = Blockchain.get_block_by_index(db_session, 1)
        block.hash = "hash_alterado_por_atacante"
        db_session.commit()
        
        assert Blockchain.is_chain_valid(db_session) is False

    def test_is_chain_valid_detects_broken_chain(self, db_session):
        """Debe detectar si el encadenamiento de hashes fue roto."""
        Blockchain.create_genesis_block(db_session)
        Blockchain.add_new_transaction(db_session, "sender1", "recipient1", "hash1")
        Blockchain.add_new_transaction(db_session, "sender2", "recipient2", "hash2")
        
        # Alterar el previous_hash del bloque 2 (romper cadena en DB)
        block = Blockchain.get_block_by_index(db_session, 2)
        block.previous_hash = "previous_hash_incorrecto"
        db_session.commit()
        
        assert Blockchain.is_chain_valid(db_session) is False

    def test_get_latest_block(self, db_session):
        """get_latest_block debe retornar el ultimo bloque."""
        Blockchain.create_genesis_block(db_session)
        Blockchain.add_new_transaction(db_session, "sender1", "recipient1", "hash1")
        
        latest = Blockchain.get_latest_block(db_session)
        chain = Blockchain.get_full_chain(db_session)
        
        assert latest.index == 1
        assert latest.index == chain[-1].index

    def test_multiple_transactions_maintain_integrity(self, db_session):
        """Multiples transacciones deben mantener la integridad de la cadena."""
        Blockchain.create_genesis_block(db_session)
        
        # Agregar muchas transacciones
        for i in range(10):
            Blockchain.add_new_transaction(
                db_session,
                sender_id=f"sender-{i}",
                recipient_id=f"recipient-{i}",
                message_hash=f"message-hash-{i}"
            )
        
        assert len(Blockchain.get_full_chain(db_session)) == 11  # Genesis + 10 transacciones
        assert Blockchain.is_chain_valid(db_session) is True


class TestIntegrationSignaturesAndBlockchain:
    """Pruebas de integracion entre firmas digitales y blockchain."""

    def test_full_message_flow_with_signature_and_blockchain(self, db_session):
        """Simula el flujo completo: firmar mensaje y registrar en blockchain."""
        # Generar llaves ECDSA
        private_key = ECC.generate(curve='P-256')
        public_key = private_key.public_key()
        private_pem = private_key.export_key(format='PEM')
        public_pem = public_key.export_key(format='PEM')
        
        # 1. Crear mensaje
        plaintext = "Documento confidencial del gobierno"
        
        # 2. Calcular hash del mensaje
        message_hash = DigitalSignatureService.calculate_message_hash(plaintext)
        
        # 3. Firmar el mensaje
        signature = DigitalSignatureService.sign_message(plaintext, private_pem)
        
        # 4. Registrar en blockchain
        Blockchain.create_genesis_block(db_session)
        block = Blockchain.add_new_transaction(
            db_session,
            sender_id="funcionario-001",
            recipient_id="director-002",
            message_hash=message_hash
        )
        
        # 5. Verificar firma
        is_signature_valid = DigitalSignatureService.verify_message_signature(
            plaintext, signature, public_pem
        )
        
        # 6. Verificar blockchain
        is_chain_valid = Blockchain.is_chain_valid(db_session)
        
        # Assertions
        assert is_signature_valid is True
        assert is_chain_valid is True
        assert block.message_hash == message_hash
        assert len(Blockchain.get_full_chain(db_session)) == 2  # Genesis + 1 transaccion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
