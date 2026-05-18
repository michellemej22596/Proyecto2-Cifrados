"""
Pruebas unitarias para el Modulo 3: Firmas Digitales y Mini Blockchain.
Valida firmas ECDSA validas/invalidas e integridad de la blockchain.
"""
import pytest
import sys
sys.path.insert(0, '..')

from signatures.signer import DigitalSignatureService
from blockchain.core import Block, Blockchain
from Crypto.PublicKey import ECC


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


class TestBlock:
    """Pruebas para la clase Block."""

    def test_block_creation(self):
        """Un bloque debe crearse con todos sus atributos."""
        block = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            sender_id="sender-123",
            recipient_id="recipient-456",
            message_hash="abc123def456",
            previous_hash="0" * 64,
            nonce=0
        )
        
        assert block.index == 1
        assert block.sender_id == "sender-123"
        assert block.recipient_id == "recipient-456"
        assert block.message_hash == "abc123def456"
        assert block.previous_hash == "0" * 64
        assert isinstance(block.hash, str)
        assert len(block.hash) == 64

    def test_block_hash_is_deterministic(self):
        """El mismo bloque debe producir el mismo hash."""
        params = {
            'index': 1,
            'timestamp': "2024-01-01T00:00:00Z",
            'sender_id': "sender",
            'recipient_id': "recipient",
            'message_hash': "hash123",
            'previous_hash': "0" * 64,
            'nonce': 0
        }
        
        block1 = Block(**params)
        block2 = Block(**params)
        
        assert block1.hash == block2.hash

    def test_block_hash_changes_with_data(self):
        """Cambiar los datos del bloque debe cambiar el hash."""
        block1 = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            sender_id="sender",
            recipient_id="recipient",
            message_hash="hash123",
            previous_hash="0" * 64,
        )
        
        block2 = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            sender_id="sender_diferente",  # Cambiado
            recipient_id="recipient",
            message_hash="hash123",
            previous_hash="0" * 64,
        )
        
        assert block1.hash != block2.hash


class TestBlockchain:
    """Pruebas para la clase Blockchain."""

    def test_blockchain_creates_genesis_block(self):
        """La blockchain debe inicializarse con un bloque genesis."""
        bc = Blockchain()
        
        assert len(bc.chain) == 1
        genesis = bc.chain[0]
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64

    def test_genesis_block_has_correct_structure(self):
        """El bloque genesis debe tener la estructura correcta."""
        bc = Blockchain()
        genesis = bc.chain[0]
        
        assert genesis.sender_id == "00000000-0000-0000-0000-000000000000"
        assert genesis.recipient_id == "00000000-0000-0000-0000-000000000000"
        assert genesis.message_hash == "0" * 64

    def test_add_new_transaction(self):
        """Agregar una transaccion debe crear un nuevo bloque."""
        bc = Blockchain()
        initial_length = len(bc.chain)
        
        new_block = bc.add_new_transaction(
            sender_id="user-1",
            recipient_id="user-2",
            message_hash="abc123def456"
        )
        
        assert len(bc.chain) == initial_length + 1
        assert new_block.index == 1
        assert new_block.sender_id == "user-1"
        assert new_block.recipient_id == "user-2"
        assert new_block.message_hash == "abc123def456"

    def test_blocks_are_chained_correctly(self):
        """Cada bloque nuevo debe apuntar al hash del bloque anterior."""
        bc = Blockchain()
        
        bc.add_new_transaction("sender1", "recipient1", "hash1")
        bc.add_new_transaction("sender2", "recipient2", "hash2")
        bc.add_new_transaction("sender3", "recipient3", "hash3")
        
        for i in range(1, len(bc.chain)):
            current = bc.chain[i]
            previous = bc.chain[i - 1]
            assert current.previous_hash == previous.hash

    def test_is_chain_valid_returns_true_for_valid_chain(self):
        """Una cadena valida debe retornar True en is_chain_valid."""
        bc = Blockchain()
        bc.add_new_transaction("sender1", "recipient1", "hash1")
        bc.add_new_transaction("sender2", "recipient2", "hash2")
        
        assert bc.is_chain_valid() is True

    def test_is_chain_valid_detects_tampered_hash(self):
        """Debe detectar si el hash de un bloque fue alterado."""
        bc = Blockchain()
        bc.add_new_transaction("sender1", "recipient1", "hash1")
        
        # Alterar el hash del bloque 1 (simular ataque)
        bc.chain[1].hash = "hash_alterado_por_atacante"
        
        assert bc.is_chain_valid() is False

    def test_is_chain_valid_detects_broken_chain(self):
        """Debe detectar si el encadenamiento de hashes fue roto."""
        bc = Blockchain()
        bc.add_new_transaction("sender1", "recipient1", "hash1")
        bc.add_new_transaction("sender2", "recipient2", "hash2")
        
        # Alterar el previous_hash del bloque 2 (romper cadena)
        bc.chain[2].previous_hash = "previous_hash_incorrecto"
        
        assert bc.is_chain_valid() is False

    def test_get_latest_block(self):
        """get_latest_block debe retornar el ultimo bloque."""
        bc = Blockchain()
        bc.add_new_transaction("sender1", "recipient1", "hash1")
        
        latest = bc.get_latest_block()
        
        assert latest.index == 1
        assert latest == bc.chain[-1]

    def test_multiple_transactions_maintain_integrity(self):
        """Multiples transacciones deben mantener la integridad de la cadena."""
        bc = Blockchain()
        
        # Agregar muchas transacciones
        for i in range(10):
            bc.add_new_transaction(
                sender_id=f"sender-{i}",
                recipient_id=f"recipient-{i}",
                message_hash=f"message-hash-{i}"
            )
        
        assert len(bc.chain) == 11  # Genesis + 10 transacciones
        assert bc.is_chain_valid() is True


class TestIntegrationSignaturesAndBlockchain:
    """Pruebas de integracion entre firmas digitales y blockchain."""

    def test_full_message_flow_with_signature_and_blockchain(self):
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
        bc = Blockchain()
        block = bc.add_new_transaction(
            sender_id="funcionario-001",
            recipient_id="director-002",
            message_hash=message_hash
        )
        
        # 5. Verificar firma
        is_signature_valid = DigitalSignatureService.verify_message_signature(
            plaintext, signature, public_pem
        )
        
        # 6. Verificar blockchain
        is_chain_valid = bc.is_chain_valid()
        
        # Assertions
        assert is_signature_valid is True
        assert is_chain_valid is True
        assert block.message_hash == message_hash
        assert len(bc.chain) == 2  # Genesis + 1 transaccion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
