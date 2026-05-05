<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</p>

<h1 align="center">VaultChain</h1>

<p align="center">
  <strong>Sistema de Mensajería Segura con Registro Inmutable</strong>
</p>

<p align="center">
  <em>Universidad del Valle de Guatemala — Cifrados de Información</em>
</p>

<p align="center">
  <em>Desarrollado por: Silvia Illescas, Davis Roldán y Michelle Mejía.</em>
</p>

---

## Descripcion

**VaultChain** es un sistema de mensajería interna desarrollado para garantizar comunicaciones seguras con estándares de nivel gubernamental. El sistema proporciona:

| Garantía | Descripcion |
|----------|-------------|
| **Confidencialidad** | Solo el destinatario autorizado puede leer el mensaje |
| **Autenticidad** | Verificacion de que el mensaje proviene del remitente declarado |
| **Integridad** | Deteccion de cualquier alteracion del mensaje |
| **No Repudio** | El remitente no puede negar haber enviado el mensaje |
| **Trazabilidad** | Registro inmutable de todas las transacciones via blockchain |

---

## Arquitectura del Sistema

El sistema se compone de **cuatro capas** que se construyen de forma progresiva:

```
┌─────────────────────────────────────────────────────────────┐
│  [Capa 4] API REST + Interfaz                               │
│           Endpoints, autenticacion JWT, MFA (TOTP)          │
├─────────────────────────────────────────────────────────────┤
│  [Capa 3] Firmas Digitales + Blockchain                     │
│           ECDSA/RSA-PSS, cadena de hashes SHA-256           │
├─────────────────────────────────────────────────────────────┤
│  [Capa 2] Cifrado Hibrido                                   │
│           AES-256-GCM + RSA-OAEP / ECC                      │
├─────────────────────────────────────────────────────────────┤
│  [Capa 1] Gestion de Identidad                              │
│           Registro, hashing bcrypt, pares de llaves RSA     │
└─────────────────────────────────────────────────────────────┘
```

---

## Modulos

### Modulo 1: Gestion de Identidad y Hashing

Implementacion de funciones hash, almacenamiento seguro de credenciales y generacion de pares de llaves.

- **Registro de usuarios** con email unico y validacion
- **Hashing de contrasenas** con bcrypt (factor de trabajo 12)
- **Generacion de par de llaves RSA-2048** al registrarse
- **Proteccion de llave privada** cifrada con PBKDF2-HMAC-SHA256 (600,000 iteraciones)
- **Endpoint de llave publica** en formato PEM

```python
# Ejemplo de generacion de llaves
public_key, encrypted_private_key = generate_key_pair(user_password)
```

### Modulo 2: Cifrado Hibrido de Mensajes

Cifrado simetrico AES-GCM combinado con cifrado asimetrico RSA-OAEP.

- **Clave AES-256 efimera** generada por mensaje
- **Cifrado AES-256-GCM** para el contenido del mensaje
- **Cifrado RSA-OAEP** para proteger la clave AES
- **Soporte para mensajes grupales**

```
Flujo de Cifrado:
[Plaintext] → AES-256-GCM → [Ciphertext + Nonce + Tag]
[AES Key] → RSA-OAEP(PubKey) → [Encrypted Key]
```

### Modulo 3: Firmas Digitales y Blockchain

Firmas ECDSA y mini-blockchain para auditoria inmutable.

- **Firma SHA-256 + ECDSA/RSA-PSS** de cada mensaje
- **Verificacion automatica** al recibir mensajes
- **Mini-blockchain** con encadenamiento SHA-256
- **Proof-of-work simplificado** con nonce

```
Estructura del Bloque:
┌────────────────────────────────┐
│ index: 1                       │
│ timestamp: 2025-01-15T10:30:00 │
│ sender_id: uuid                │
│ recipient_id: uuid             │
│ message_hash: sha256(...)      │
│ previous_hash: abc123...       │
│ nonce: 12345                   │
│ hash: def456...                │
└────────────────────────────────┘
```

### Modulo 4: Integracion, MFA y Despliegue

Autenticacion multifactor y despliegue containerizado.

- **TOTP** compatible con Google Authenticator
- **JWT** con access token y refresh token
- **Flujo completo** de sesion segura
- **Docker Compose** para despliegue

---

## API REST

| Metodo | Endpoint | Descripcion | Modulo |
|--------|----------|-------------|--------|
| `POST` | `/auth/register` | Registro de nuevo usuario | 1 |
| `POST` | `/auth/login` | Inicio de sesion + JWT | 1 |
| `POST` | `/auth/mfa/enable` | Activar MFA (retorna QR TOTP) | 4 |
| `POST` | `/auth/mfa/verify` | Verificar codigo TOTP | 4 |
| `GET` | `/users/{user_id}/key` | Obtener llave publica PEM | 1 |
| `POST` | `/messages` | Enviar mensaje cifrado y firmado | 2, 3 |
| `GET` | `/messages/{user_id}` | Obtener mensajes del usuario | 2 |
| `GET` | `/messages/{msg_id}/verify` | Verificar firma de un mensaje | 3 |
| `POST` | `/groups` | Crear grupo con clave compartida | 2 |
| `GET` | `/blockchain` | Obtener cadena completa | 3 |
| `GET` | `/blockchain/verify` | Verificar integridad de la cadena | 3 |

---

## Instalacion

### Requisitos Previos

- Python 3.11+
- PostgreSQL 14+
- Docker y Docker Compose

### Configuracion Local

```bash
# Clonar el repositorio
git clone https://github.com/michellemej22596/Proyecto2-Cifrados.git
cd Proyecto2-Cifrados

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar migraciones
alembic upgrade head

# Iniciar el servidor
uvicorn src.main:app --reload
```

### Despliegue con Docker

```bash
# Construir y ejecutar
docker-compose up --build

# El servicio estara disponible en:
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## Estructura del Repositorio

```
vaultchain/
│
├── README.md                       # Documentacion principal
├── docker-compose.yml              # Orquestacion de servicios
├── .env.example                    # Variables de entorno de ejemplo
│
├── docs/
│   ├── arquitectura.md             # Documento de diseno
│   └── analisis.md                 # Respuestas a preguntas de analisis
│
│
├── backend/                        # ══════════ BACKEND (FastAPI) ══════════
│   │
│   ├── Dockerfile                  # Imagen Docker del backend
│   ├── requirements.txt            # Dependencias Python
│   ├── pyproject.toml              # Configuracion del proyecto Python
│   │
│   ├── src/
│   │   ├── main.py                 # Punto de entrada FastAPI
│   │   ├── database.py             # Configuracion de base de datos
│   │   ├── models.py               # Modelos SQLAlchemy
│   │   ├── schemas.py              # Schemas Pydantic
│   │   │
│   │   ├── auth/                   # Modulo 1: Identidad
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Endpoints de autenticacion
│   │   │   └── service.py          # Logica de negocio auth
│   │   │
│   │   ├── crypto/                 # Modulo 2: Cifrado hibrido
│   │   │   ├── __init__.py
│   │   │   ├── hashing.py          # Bcrypt, PBKDF2
│   │   │   ├── symmetric.py        # AES-256-GCM
│   │   │   ├── asymmetric.py       # RSA-OAEP / ECC
│   │   │   └── hybrid.py           # Integracion cifrado hibrido
│   │   │
│   │   ├── signatures/             # Modulo 3: Firmas digitales
│   │   │   ├── __init__.py
│   │   │   └── ecdsa.py            # ECDSA / RSA-PSS
│   │   │
│   │   ├── blockchain/             # Modulo 3: Mini blockchain
│   │   │   ├── __init__.py
│   │   │   ├── block.py            # Estructura del bloque
│   │   │   └── chain.py            # Cadena y validacion
│   │   │
│   │   └── api/                    # Endpoints REST
│   │       ├── __init__.py
│   │       ├── users.py            # CRUD usuarios, llaves publicas
│   │       ├── messages.py         # Envio/recepcion de mensajes
│   │       └── groups.py           # Gestion de grupos
│   │
│   └── tests/                      # Suite de pruebas backend
│       ├── __init__.py
│       ├── conftest.py             # Fixtures de pytest
│       ├── test_crypto.py          # Tests de criptografia
│       ├── test_auth.py            # Tests de autenticacion
│       └── test_blockchain.py      # Tests de blockchain
│
│
├── frontend/                       # ══════════ FRONTEND (Next.js) ══════════
│   │
│   ├── Dockerfile                  # Imagen Docker del frontend
│   ├── package.json                # Dependencias Node.js
│   ├── next.config.mjs             # Configuracion Next.js
│   ├── tailwind.config.ts          # Configuracion Tailwind CSS
│   ├── tsconfig.json               # Configuracion TypeScript
│   │
│   ├── public/                     # Archivos estaticos
│   │   └── images/
│   │
│   ├── app/                        # App Router (Next.js 14+)
│   │   ├── layout.tsx              # Layout principal
│   │   ├── page.tsx                # Pagina de inicio
│   │   ├── globals.css             # Estilos globales
│   │   │
│   │   ├── (auth)/                 # Grupo de rutas de autenticacion
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── register/
│   │   │   │   └── page.tsx
│   │   │   └── mfa/
│   │   │       └── page.tsx
│   │   │
│   │   ├── dashboard/              # Panel principal
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── messages/
│   │   │       └── page.tsx
│   │   │
│   │   └── api/                    # API Routes (proxy al backend)
│   │       └── [...proxy]/
│   │           └── route.ts
│   │
│   ├── components/                 # Componentes React
│   │   ├── ui/                     # Componentes base (shadcn/ui)
│   │   ├── auth/                   # Componentes de autenticacion
│   │   ├── messages/               # Componentes de mensajeria
│   │   └── blockchain/             # Visualizacion de blockchain
│   │
│   ├── lib/                        # Utilidades y configuracion
│   │   ├── utils.ts                # Funciones helper
│   │   ├── api.ts                  # Cliente API
│   │   └── auth.ts                 # Manejo de sesion
│   │
│   └── hooks/                      # Custom React hooks
│       ├── use-auth.ts
│       └── use-messages.ts
│
│
└── scripts/                        # Scripts de utilidad
    ├── seed.py                     # Datos de prueba
    └── migrate.py                  # Migraciones de BD
```


---

## Pruebas

Ejecutar la suite completa de pruebas:

```bash
# Todas las pruebas
pytest tests/ -v

# Solo pruebas de criptografia
pytest tests/test_crypto.py -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

### Pruebas Implementadas

| Categoria | Tests | Estado
|-----|-----|-----
| Hashing de contraseñas | 5 | Completado
| Derivacion de claves PBKDF2 | 4 | Completado
| Generacion RSA-2048 | 6 | Completado
| JWT (Access Tokens) | 4 | Completado
| Cifrado AES-GCM | 5 | Completado
| Cifrado RSA-OAEP | 3 | Completado
| Cifrado Hibrido | 4 | Completado
| Casos limite y seguridad | 4 | Completado
| Integracion | 2 | Completado


**Total: 37 tests**


---

## Tecnologias Utilizadas

| Categoria | Tecnologia | Proposito |
|-----------|------------|-----------|
| **Backend** | FastAPI | Framework web asincrono |
| **Base de Datos** | PostgreSQL | Almacenamiento persistente |
| **ORM** | SQLAlchemy | Mapeo objeto-relacional |
| **Criptografia** | cryptography | Primitivos criptograficos |
| **Hashing** | bcrypt | Hash de contrasenas |
| **JWT** | python-jose | Tokens de autenticacion |
| **TOTP** | pyotp | Autenticacion multifactor |
| **Contenedores** | Docker | Despliegue |

---

## Referencias

- [Presentaciones del curso](https://locano-uvg.github.io/cifrados-26/)
- [pycryptodome Documentation](https://pycryptodome.readthedocs.io)
- [PyJWT Documentation](https://pyjwt.readthedocs.io)
- [pyotp - TOTP Library](https://github.com/pyauth/pyotp)
- [RFC 7519 - JWT](https://tools.ietf.org/html/rfc7519)
- [NIST SP 800-132 - Key Derivation](https://csrc.nist.gov/publications/detail/sp/800-132/final)

---

<p align="center">
  <strong>Universidad del Valle de Guatemala</strong><br>
  Cifrados de Informacion — 2025
</p>
