from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from sqlalchemy import text, inspect

from database import engine, Base
from routers import auth, users, messages, groups, blockchain
from ws_manager import manager
from crypto import SECRET_KEY, ALGORITHM

# ---------------------------------------------------------------------------
# Crear / actualizar esquema de BD
# ---------------------------------------------------------------------------

Base.metadata.create_all(bind=engine)


def _run_migrations() -> None:
    """
    Añade columnas nuevas a tablas existentes cuando se actualiza el modelo.
    SQLite no soporta IF NOT EXISTS en ALTER TABLE, así que inspeccionamos
    las columnas antes de intentar agregarlas.
    """
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing = {col["name"] for col in inspector.get_columns("users")}

        if "mfa_secret" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN mfa_secret TEXT"))

        if "mfa_enabled" not in existing:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT 0"
            ))

        conn.commit()


_run_migrations()

# ---------------------------------------------------------------------------
# Aplicación FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Crypto Users API",
    description="Registro de usuarios con hashing de contraseñas y llaves RSA-2048.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(groups.router)
app.include_router(blockchain.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "Crypto Users API corriendo."}


# ---------------------------------------------------------------------------
# WebSocket — conexión persistente por usuario autenticado
# Ruta: ws://<host>/ws/{user_id}?token=<jwt>
# ---------------------------------------------------------------------------

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    """
    Endpoint WebSocket autenticado.
    El cliente envía su JWT como query param ?token=...
    El servidor valida que el token pertenezca al user_id reclamado.
    Una vez conectado, el servidor puede enviar eventos JSON al cliente
    (ej. new_message) sin que el cliente tenga que hacer polling.
    """
    # 1. Validar el JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Rechazar tokens de sesión MFA (no son tokens de acceso completo)
        if payload.get("type") == "mfa_session":
            await websocket.close(code=4001)
            return
        token_user_id = int(payload.get("sub", -1))
        if token_user_id != user_id:
            await websocket.close(code=4001)
            return
    except (JWTError, ValueError):
        await websocket.close(code=4001)
        return

    # 2. Registrar la conexión
    await manager.connect(websocket, user_id)

    try:
        # 3. Mantener la conexión viva; el cliente puede enviar "ping"
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(user_id)
