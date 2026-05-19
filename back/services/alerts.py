"""
Servicio de Alertas de Seguridad para VaultChain.

Este módulo maneja las alertas cuando se detectan problemas de seguridad
como firmas digitales inválidas o mensajes alterados.
"""

from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class AlertType(Enum):
    """Tipos de alertas de seguridad."""
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    HASH_MISMATCH = "HASH_MISMATCH"
    NO_SIGNATURE = "NO_SIGNATURE"
    BLOCKCHAIN_COMPROMISED = "BLOCKCHAIN_COMPROMISED"


class SecurityAlert:
    """Representa una alerta de seguridad."""
    
    def __init__(
        self,
        alert_type: AlertType,
        message_id: int,
        sender_id: Optional[int],
        recipient_id: int,
        description: str,
    ):
        self.alert_type = alert_type
        self.message_id = message_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.description = description
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.is_critical = alert_type in [AlertType.SIGNATURE_INVALID, AlertType.HASH_MISMATCH]


class AlertService:
    """
    Servicio para gestionar alertas de seguridad en VaultChain.
    
    Responsabilidades (Silvia):
    - Disparar alertas cuando una firma digital no coincide
    - Registrar alertas para auditoría
    - Notificar al usuario afectado
    """
    
    # Lista de alertas en memoria (en producción, esto sería una tabla en BD)
    _alerts: list[SecurityAlert] = []
    
    @classmethod
    def create_signature_invalid_alert(
        cls,
        message_id: int,
        sender_id: Optional[int],
        recipient_id: int,
    ) -> SecurityAlert:
        """
        Crea y dispara una alerta cuando la firma digital no coincide.
        Esta es la alerta principal del flujo de excepción de Silvia.
        """
        alert = SecurityAlert(
            alert_type=AlertType.SIGNATURE_INVALID,
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            description=(
                f"⚠️ ALERTA CRÍTICA: La firma digital del mensaje #{message_id} "
                f"NO ES VÁLIDA. El mensaje puede haber sido alterado o el remitente "
                f"no es quien dice ser. Este mensaje ha sido marcado como NO VERIFICADO."
            ),
        )
        cls._alerts.append(alert)
        cls._log_alert(alert)
        return alert
    
    @classmethod
    def create_hash_mismatch_alert(
        cls,
        message_id: int,
        sender_id: Optional[int],
        recipient_id: int,
    ) -> SecurityAlert:
        """
        Crea una alerta cuando el hash del mensaje no coincide con el blockchain.
        """
        alert = SecurityAlert(
            alert_type=AlertType.HASH_MISMATCH,
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            description=(
                f"⚠️ ALERTA: El hash del mensaje #{message_id} no coincide con "
                f"el registro en la blockchain. Posible alteración del contenido."
            ),
        )
        cls._alerts.append(alert)
        cls._log_alert(alert)
        return alert
    
    @classmethod
    def create_no_signature_alert(
        cls,
        message_id: int,
        sender_id: Optional[int],
        recipient_id: int,
    ) -> SecurityAlert:
        """
        Crea una alerta cuando un mensaje no tiene firma digital.
        """
        alert = SecurityAlert(
            alert_type=AlertType.NO_SIGNATURE,
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            description=(
                f"ADVERTENCIA: El mensaje #{message_id} no tiene firma digital. "
                f"No se puede verificar la autenticidad del remitente."
            ),
        )
        cls._alerts.append(alert)
        cls._log_alert(alert)
        return alert
    
    @classmethod
    def get_alerts_for_user(cls, user_id: int) -> list[SecurityAlert]:
        """
        Obtiene todas las alertas para un usuario específico.
        """
        return [
            alert for alert in cls._alerts
            if alert.recipient_id == user_id or alert.sender_id == user_id
        ]
    
    @classmethod
    def get_critical_alerts(cls) -> list[SecurityAlert]:
        """
        Obtiene todas las alertas críticas (firmas inválidas, hash mismatch).
        """
        return [alert for alert in cls._alerts if alert.is_critical]
    
    @classmethod
    def get_all_alerts(cls) -> list[SecurityAlert]:
        """
        Obtiene todas las alertas del sistema.
        """
        return cls._alerts.copy()
    
    @classmethod
    def clear_alerts(cls):
        """
        Limpia todas las alertas (usar con precaución).
        """
        cls._alerts.clear()
    
    @staticmethod
    def _log_alert(alert: SecurityAlert):
        """
        Registra la alerta en el log del sistema.
        En producción, esto podría enviar notificaciones por email, webhook, etc.
        """
        severity = "🚨 CRÍTICO" if alert.is_critical else "⚠️ ADVERTENCIA"
        print(f"\n{'='*60}")
        print(f"{severity} - ALERTA DE SEGURIDAD")
        print(f"{'='*60}")
        print(f"Tipo: {alert.alert_type.value}")
        print(f"Mensaje ID: {alert.message_id}")
        print(f"Remitente ID: {alert.sender_id}")
        print(f"Destinatario ID: {alert.recipient_id}")
        print(f"Timestamp: {alert.timestamp}")
        print(f"Descripción: {alert.description}")
        print(f"{'='*60}\n")
