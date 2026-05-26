"""
WebSocket Connection Manager
Mantiene las conexiones activas por user_id y permite enviar
notificaciones en tiempo real a usuarios específicos.
"""

from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # user_id → websocket activo
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, data: dict) -> None:
        """Envía un mensaje JSON al usuario si está conectado."""
        ws = self.active_connections.get(user_id)
        if ws is None:
            return
        try:
            await ws.send_json(data)
        except Exception:
            # Si falla (conexión caída), limpiar
            self.disconnect(user_id)


# Instancia global compartida entre main.py y los routers
manager = ConnectionManager()
