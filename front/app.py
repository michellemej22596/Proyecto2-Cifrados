import requests
import streamlit as st

API_BASE = "http://localhost:8000"

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="VaultChain - Mensajeria Segura",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================
# ESTILOS
# =========================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
        color: #f8fafc;
    }

    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        color: #38bdf8;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        color: #cbd5e1;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    .section-card {
        background: rgba(30, 41, 59, 0.75);
        padding: 1.4rem;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
        margin-bottom: 1rem;
    }

    .mini-card {
        background: rgba(15, 23, 42, 0.85);
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.14);
        margin-top: 0.75rem;
    }

    .badge {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(56, 189, 248, 0.15);
        color: #7dd3fc;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .badge-green {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(34, 197, 94, 0.15);
        color: #86efac;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    
    .badge-red {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    
    .badge-yellow {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(234, 179, 8, 0.15);
        color: #fde047;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #0f172a;
        border-radius: 10px;
        color: #e2e8f0;
        padding: 10px 18px;
        border: 1px solid rgba(148, 163, 184, 0.15);
    }

    .stTabs [aria-selected="true"] {
        background-color: #38bdf8 !important;
        color: #0f172a !important;
        font-weight: 700;
    }

    .stTextInput > div > div > input {
        border-radius: 12px;
        background-color: #0f172a;
        color: #f8fafc;
        border: 1px solid rgba(148, 163, 184, 0.25);
    }

    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.1em;
        border: none;
        font-weight: 700;
        background: linear-gradient(90deg, #38bdf8, #0ea5e9);
        color: #082f49;
    }

    .stButton > button:hover {
        filter: brightness(1.05);
    }

    .token-box {
        background: #020617;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 12px;
        padding: 0.9rem;
        color: #e2e8f0;
        font-size: 0.9rem;
        word-break: break-all;
    }

    .plaintext-box {
        background: #052e16;
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 12px;
        padding: 1rem;
        color: #86efac;
        font-size: 1rem;
        word-break: break-all;
    }
    
    .signature-box {
        background: #1e1b4b;
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 1rem;
        color: #c4b5fd;
        font-size: 0.85rem;
        word-break: break-all;
    }
    
    .blockchain-box {
        background: #172554;
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 1rem;
        color: #93c5fd;
        font-size: 0.85rem;
        word-break: break-all;
    }
    
    .alert-box-critical {
        background: #450a0a;
        border: 1px solid rgba(239, 68, 68, 0.5);
        border-radius: 12px;
        padding: 1rem;
        color: #fca5a5;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .alert-box-warning {
        background: #422006;
        border: 1px solid rgba(234, 179, 8, 0.5);
        border-radius: 12px;
        padding: 1rem;
        color: #fde047;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .verified-box {
        background: #052e16;
        border: 2px solid rgba(34, 197, 94, 0.5);
        border-radius: 12px;
        padding: 1rem;
        color: #86efac;
    }
    
    .not-verified-box {
        background: #450a0a;
        border: 2px solid rgba(239, 68, 68, 0.5);
        border-radius: 12px;
        padding: 1rem;
        color: #fca5a5;
    }

    .footer-note {
        text-align: center;
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown('<div class="main-title">VaultChain</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Sistema de Mensajeria Segura con Registro Inmutable</div>',
    unsafe_allow_html=True
)

# =========================
# SESSION DEFAULTS
# =========================
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

if "token_type" not in st.session_state:
    st.session_state["token_type"] = None
    
if "user_password" not in st.session_state:
    st.session_state["user_password"] = None

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}


def load_users():
    try:
        response = requests.get(f"{API_BASE}/users/list", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []


def load_groups(headers):
    try:
        response = requests.get(f"{API_BASE}/groups/", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Registro",
    "Login",
    "Enviar",
    "Mensajes",
    "Descifrar",
    "Verificar",
    "Alertas",
    "Blockchain",
])

# =========================
# REGISTRO
# =========================
with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Nuevo usuario</div>', unsafe_allow_html=True)
    st.subheader("Crear cuenta")

    st.caption("Completa tus datos para registrar un usuario y generar automaticamente su par de llaves RSA.")

    with st.form("register_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Nombre completo", placeholder="Juan Perez")

        with col2:
            email = st.text_input("Correo electronico", placeholder="juan@ejemplo.com")

        password = st.text_input("Contrasena", type="password", placeholder="Minimo 8 caracteres")
        password_confirm = st.text_input("Confirmar contrasena", type="password")

        submitted = st.form_submit_button("Registrarse")

    if submitted:
        if not name or not email or not password or not password_confirm:
            st.error("Completa todos los campos.")
        elif len(password) < 8:
            st.error("La contrasena debe tener al menos 8 caracteres.")
        elif password != password_confirm:
            st.error("Las contrasenas no coinciden.")
        else:
            with st.spinner("Registrando usuario y generando llaves RSA..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/auth/register",
                        json={
                            "name": name,
                            "email": email,
                            "password": password
                        },
                        timeout=30,
                    )

                    if response.status_code == 201:
                        data = response.json()
                        st.success(f"Usuario registrado correctamente. ID asignado: {data['id']}")

                        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                        st.markdown("**Resumen del registro**")
                        st.write(f"**Nombre:** {data['name']}")
                        st.write(f"**Correo:** {data['email']}")
                        st.write(f"**ID:** {data['id']}")
                        st.markdown('</div>', unsafe_allow_html=True)

                        with st.expander("Ver llave publica generada (RSA)"):
                            st.code(data["public_key_pem"], language="text")

                        st.info(
                            "La llave privada fue cifrada de forma segura con una clave derivada "
                            "de la contrasena usando PBKDF2-HMAC-SHA256. Esta llave se usara para firmar digitalmente tus mensajes."
                        )

                    elif response.status_code == 409:
                        st.error("Ese correo electronico ya esta registrado.")
                    elif response.status_code == 422:
                        errors = response.json().get("detail", [])
                        for err in errors:
                            campo = err.get("loc", ["campo"])[-1]
                            mensaje = err.get("msg", "Valor invalido")
                            st.error(f"{campo}: {mensaje}")
                    else:
                        st.error(f"Error del servidor ({response.status_code}): {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("No se pudo conectar con el backend. Verifica que este corriendo en localhost:8000.")
                except requests.exceptions.Timeout:
                    st.error("El backend tardo demasiado en responder.")
                except Exception as e:
                    st.error(f"Ocurrio un error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Autenticacion</div>', unsafe_allow_html=True)
    st.subheader("Iniciar sesion")

    st.caption("Ingresa tus credenciales para autenticarte y recibir un token JWT.")

    with st.form("login_form"):
        login_email = st.text_input("Correo electronico", placeholder="juan@ejemplo.com", key="login_email")
        login_password = st.text_input("Contrasena", type="password", key="login_password")

        login_submitted = st.form_submit_button("Iniciar sesion")

    if login_submitted:
        if not login_email or not login_password:
            st.error("Debes ingresar correo y contrasena.")
        else:
            with st.spinner("Validando credenciales..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/auth/login",
                        json={
                            "email": login_email,
                            "password": login_password
                        },
                        timeout=15,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["access_token"] = data["access_token"]
                        st.session_state["token_type"] = data["token_type"]
                        st.session_state["user_password"] = login_password

                        st.success("Login exitoso.")

                        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                        st.markdown("**Token JWT generado**")
                        st.markdown(
                            f'<div class="token-box">{data["access_token"]}</div>',
                            unsafe_allow_html=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)

                    elif response.status_code == 401:
                        st.error("Credenciales invalidas.")
                    elif response.status_code == 422:
                        errors = response.json().get("detail", [])
                        for err in errors:
                            campo = err.get("loc", ["campo"])[-1]
                            mensaje = err.get("msg", "Valor invalido")
                            st.error(f"{campo}: {mensaje}")
                    else:
                        st.error(f"Error del servidor ({response.status_code}): {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("No se pudo conectar con el backend. Verifica que este corriendo en localhost:8000.")
                except requests.exceptions.Timeout:
                    st.error("El backend tardo demasiado en responder.")
                except Exception as e:
                    st.error(f"Ocurrio un error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SESION ACTIVA
# =========================
if st.session_state.get("access_token"):
    with st.sidebar:
        st.markdown("### Sesion activa")
        st.success("Autenticado")
        with st.expander("Ver token"):
            st.markdown(
                f'<div class="token-box">{st.session_state["access_token"]}</div>',
                unsafe_allow_html=True
            )
        if st.button("Cerrar sesion"):
            st.session_state["access_token"] = None
            st.session_state["token_type"] = None
            st.session_state["user_password"] = None
            st.rerun()

# =========================
# ENVIAR MENSAJE (CON FIRMA DIGITAL)
# =========================
with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Firma Digital + Blockchain</div>', unsafe_allow_html=True)
    st.subheader("Enviar mensaje cifrado y firmado")
    st.caption(
        "El mensaje sera firmado digitalmente con tu llave privada RSA (RSA-PSS), "
        "cifrado con AES-256-GCM y registrado automaticamente en la blockchain."
    )

    if not st.session_state.get("access_token"):
        st.warning("Inicia sesion en la pestana **Login** para enviar mensajes.")
    else:
        with st.form("hybrid_form"):
            recipient_id = st.number_input(
                "ID del destinatario",
                min_value=1,
                step=1,
                help="El ID numerico del usuario que recibira el mensaje.",
            )
            hybrid_content = st.text_area("Mensaje", placeholder="Escribe tu mensaje...", key="hybrid_content")
            sender_password = st.text_input(
                "Tu contrasena (para firmar)",
                type="password",
                value=st.session_state.get("user_password", ""),
                help="Necesaria para desbloquear tu llave privada RSA y firmar el mensaje."
            )
            hybrid_submitted = st.form_submit_button("Firmar, Cifrar y Enviar")

        if hybrid_submitted:
            if not hybrid_content.strip():
                st.error("El mensaje no puede estar vacio.")
            elif not sender_password:
                st.error("Debes ingresar tu contrasena para firmar el mensaje.")
            else:
                with st.spinner("Firmando con RSA-PSS, cifrando con AES-256-GCM y registrando en blockchain..."):
                    try:
                        response = requests.post(
                            f"{API_BASE}/messages/hybrid/",
                            json={
                                "content": hybrid_content, 
                                "recipient_id": int(recipient_id),
                                "password": sender_password
                            },
                            headers=auth_headers(),
                            timeout=15,
                        )
                        if response.status_code == 201:
                            data = response.json()
                            st.success(f"Mensaje enviado y registrado en blockchain. ID: **{data['id']}**")
                            
                            st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                            st.markdown("**Detalles del mensaje**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Remitente ID:** {data.get('sender_id')}")
                                st.write(f"**Estado:** {data.get('verification_status', 'PENDING')}")
                            with col2:
                                st.write(f"**Destinatario ID:** {data.get('recipient_id')}")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Mostrar firma digital
                            if data.get('signature'):
                                with st.expander("Ver Firma Digital (RSA-PSS)"):
                                    st.markdown(
                                        f'<div class="signature-box">{data["signature"][:100]}...</div>',
                                        unsafe_allow_html=True
                                    )
                                    st.caption("La firma digital garantiza que el mensaje fue enviado por ti y no ha sido alterado.")
                            
                            # Mostrar datos cifrados
                            with st.expander("Ver datos cifrados"):
                                st.text(f"Ciphertext (Base64):\n{data['ciphertext'][:80]}...")
                                st.text(f"Nonce (Base64):\n{data['nonce']}")
                                st.text(f"Auth Tag (GCM):\n{data.get('auth_tag', '')}")
                                st.text(f"Clave AES cifrada (RSA-OAEP):\n{data.get('encrypted_key', '')[:80]}...")
                            
                            st.info(
                                f"El mensaje #{data['id']} ha sido registrado en la blockchain para garantizar "
                                "su trazabilidad e inmutabilidad. El destinatario puede verificar su autenticidad."
                            )
                        elif response.status_code == 404:
                            st.error("Destinatario no encontrado. Verifica el ID.")
                        elif response.status_code == 401:
                            st.error("Sesion expirada o contrasena incorrecta. Vuelve a iniciar sesion.")
                        elif response.status_code == 422:
                            st.error("Datos invalidos.")
                        else:
                            st.error(f"Error ({response.status_code}): {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("No se pudo conectar con el backend.")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# VER MENSAJES
# =========================
with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Mensajes almacenados")
    st.caption("Lista todos los mensajes cifrados con su estado de verificacion.")

    if st.button("Actualizar lista"):
        st.rerun()

    if not st.session_state.get("access_token"):
        st.warning("Inicia sesion en la pestana **Login** para ver tus mensajes.")
    else:
        try:
            response = requests.get(
                f"{API_BASE}/messages/hybrid/",
                headers=auth_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                messages = response.json()
                if not messages:
                    st.info("No hay mensajes aun. Envia uno desde la pestana Enviar.")
                else:
                    st.write(f"**{len(messages)} mensaje(s) encontrado(s)**")
                    for msg in messages:
                        # Determinar icono segun estado de verificacion
                        status = msg.get('verification_status', 'PENDING')
                        if status == 'VERIFIED':
                            status_icon = "[VERIFICADO]"
                            status_class = "badge-green"
                        elif status == 'NOT_VERIFIED':
                            status_icon = "[NO VERIFICADO]"
                            status_class = "badge-red"
                        else:
                            status_icon = "[PENDIENTE]"
                            status_class = "badge-yellow"
                        
                        label = f"Mensaje #{msg['id']} - De: {msg.get('sender_id', '?')} -> Para: {msg.get('recipient_id', '?')} {status_icon}"
                        with st.expander(label):
                            st.markdown(f'<div class="{status_class}">{status}</div>', unsafe_allow_html=True)
                            
                            if msg.get('signature'):
                                st.markdown("**Firma Digital:** Presente")
                                st.text(f"Firma (primeros 60 chars):\n{msg['signature'][:60]}...")
                            else:
                                st.markdown("**Firma Digital:** No presente")
                            
                            st.text(f"Ciphertext (Base64):\n{msg['ciphertext'][:60]}...")
                            st.text(f"Nonce (Base64):\n{msg['nonce']}")
                            st.text(f"Auth Tag (GCM):\n{msg.get('auth_tag', '')}")
            else:
                st.error(f"Error al obtener mensajes ({response.status_code}).")
        except requests.exceptions.ConnectionError:
            st.error("No se pudo conectar con el backend.")
        except Exception as e:
            st.error(f"Error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# DESCIFRAR
# =========================
with tab5:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Descifrado RSA-OAEP + AES-GCM</div>', unsafe_allow_html=True)
    st.subheader("Descifrar mensaje")
    st.caption(
        "Usa tu llave privada RSA (protegida con tu contrasena) para recuperar "
        "la clave AES efimera y descifrar el mensaje."
    )

    if not st.session_state.get("access_token"):
        st.warning("Inicia sesion en la pestana **Login** para descifrar mensajes.")
    else:
        with st.form("decrypt_form"):
            decrypt_msg_id = st.number_input(
                "ID del mensaje",
                min_value=1,
                step=1,
                help="El ID del mensaje hibrido que quieres descifrar.",
            )
            decrypt_password = st.text_input(
                "Tu contrasena",
                type="password",
                value=st.session_state.get("user_password", ""),
                help="Necesaria para desbloquear tu llave privada RSA.",
            )
            decrypt_submitted = st.form_submit_button("Descifrar")

        if decrypt_submitted:
            if not decrypt_password:
                st.error("Ingresa tu contrasena.")
            else:
                with st.spinner("Descifrando con RSA-OAEP + AES-256-GCM..."):
                    try:
                        response = requests.post(
                            f"{API_BASE}/messages/{int(decrypt_msg_id)}/decrypt",
                            json={"password": decrypt_password},
                            headers={"Authorization": f"Bearer {st.session_state['access_token']}"},
                            timeout=15,
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success("Mensaje descifrado exitosamente.")
                            st.markdown(
                                f'<div class="plaintext-box">{data["plaintext"]}</div>',
                                unsafe_allow_html=True,
                            )
                        elif response.status_code == 403:
                            st.error("No eres el destinatario de este mensaje.")
                        elif response.status_code == 401:
                            st.error("Contrasena incorrecta o sesion expirada.")
                        elif response.status_code == 404:
                            st.error("Mensaje no encontrado.")
                        elif response.status_code == 400:
                            st.error("Este mensaje no usa cifrado hibrido.")
                        else:
                            st.error(f"Error ({response.status_code}): {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("No se pudo conectar con el backend.")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# VERIFICAR FIRMA DIGITAL
# =========================
with tab6:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Verificacion de Integridad</div>', unsafe_allow_html=True)
    st.subheader("Verificar mensaje")
    st.caption(
        "Verifica la firma digital del mensaje usando la llave publica del remitente "
        "y comprueba el registro en la blockchain."
    )

    if not st.session_state.get("access_token"):
        st.warning("Inicia sesion en la pestana **Login** para verificar mensajes.")
    else:
        with st.form("verify_form"):
            verify_msg_id = st.number_input(
                "ID del mensaje a verificar",
                min_value=1,
                step=1,
                help="El ID del mensaje que deseas verificar.",
            )
            verify_password = st.text_input(
                "Tu contrasena (para descifrar y verificar)",
                type="password",
                value=st.session_state.get("user_password", ""),
                help="Necesaria para descifrar el mensaje y verificar su contenido.",
            )
            verify_submitted = st.form_submit_button("Verificar Firma y Blockchain")

        if verify_submitted:
            if not verify_password:
                st.error("Ingresa tu contrasena.")
            else:
                with st.spinner("Verificando firma digital y registro en blockchain..."):
                    try:
                        response = requests.post(
                            f"{API_BASE}/messages/{int(verify_msg_id)}/verify",
                            json={"password": verify_password},
                            headers=auth_headers(),
                            timeout=15,
                        )
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Mostrar resultado de verificacion
                            if data.get("is_signature_valid"):
                                st.markdown(
                                    '<div class="verified-box">'
                                    '<strong>VERIFICADO</strong><br>'
                                    'La firma digital es valida y el mensaje esta registrado en blockchain.'
                                    '</div>',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f'<div class="not-verified-box">'
                                    f'<strong>NO VERIFICADO</strong><br>'
                                    f'{data.get("message", "La verificacion fallo.")}'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                            
                            st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                            st.markdown("**Detalles de verificacion**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Message ID:** {data.get('message_id')}")
                                st.write(f"**Remitente ID:** {data.get('sender_id')}")
                                st.write(f"**Destinatario ID:** {data.get('recipient_id')}")
                            with col2:
                                st.write(f"**Estado firma:** {data.get('signature_status')}")
                                st.write(f"**En Blockchain:** {'Si' if data.get('blockchain_registered') else 'No'}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Mostrar mensaje descifrado si la verificacion fue exitosa
                            if data.get("plaintext"):
                                with st.expander("Ver mensaje descifrado"):
                                    st.markdown(
                                        f'<div class="plaintext-box">{data["plaintext"]}</div>',
                                        unsafe_allow_html=True
                                    )
                            
                        elif response.status_code == 403:
                            st.error("No eres el destinatario de este mensaje.")
                        elif response.status_code == 401:
                            st.error("Contrasena incorrecta o sesion expirada.")
                        elif response.status_code == 404:
                            st.error("Mensaje no encontrado.")
                        else:
                            st.error(f"Error ({response.status_code}): {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("No se pudo conectar con el backend.")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ALERTAS DE SEGURIDAD
# =========================
with tab7:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge-red">Alertas de Seguridad</div>', unsafe_allow_html=True)
    st.subheader("Centro de Alertas")
    st.caption(
        "Aqui se muestran las alertas de seguridad cuando se detectan firmas invalidas, "
        "mensajes alterados o problemas de integridad."
    )

    if not st.session_state.get("access_token"):
        st.warning("Inicia sesion en la pestana **Login** para ver tus alertas.")
    else:
        if st.button("Actualizar alertas", key="refresh_alerts"):
            st.rerun()
            
        try:
            response = requests.get(
                f"{API_BASE}/messages/alerts/me",
                headers=auth_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_alerts", 0)
                critical = data.get("critical_count", 0)
                
                if total == 0:
                    st.success("No tienes alertas de seguridad. Todos tus mensajes estan seguros.")
                else:
                    st.warning(f"Tienes **{total}** alerta(s) de seguridad, **{critical}** critica(s).")
                    
                    for alert in data.get("alerts", []):
                        alert_type = alert.get("type", "UNKNOWN")
                        is_critical = alert.get("is_critical", False)
                        
                        box_class = "alert-box-critical" if is_critical else "alert-box-warning"
                        
                        st.markdown(
                            f'<div class="{box_class}">'
                            f'<strong>{"[CRITICO]" if is_critical else "[ADVERTENCIA]"} {alert_type}</strong><br>'
                            f'Mensaje ID: {alert.get("message_id")}<br>'
                            f'Remitente ID: {alert.get("sender_id")} | Destinatario ID: {alert.get("recipient_id")}<br>'
                            f'{alert.get("description", "")}<br>'
                            f'<small>{alert.get("timestamp", "")}</small>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            else:
                st.error(f"Error al obtener alertas ({response.status_code}).")
        except requests.exceptions.ConnectionError:
            st.error("No se pudo conectar con el backend.")
        except Exception as e:
            st.error(f"Error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# BLOCKCHAIN
# =========================
with tab8:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Registro Inmutable</div>', unsafe_allow_html=True)
    st.subheader("Explorador de Blockchain")
    st.caption(
        "Visualiza la cadena de bloques que registra todas las transacciones de mensajes. "
        "Cada bloque contiene: indice, timestamp, datos de transaccion, hash anterior y nonce."
    )

    if st.button("Cargar Blockchain", key="load_blockchain"):
        try:
            response = requests.get(
                f"{API_BASE}/blockchain/",
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                chain = data.get("chain", [])
                
                st.write(f"**Longitud de la cadena:** {data.get('length', len(chain))} bloques")
                
                for block in chain:
                    block_index = block.get("index", "?")
                    is_genesis = block_index == 0
                    
                    label = f"Bloque #{block_index}" + (" (Genesis)" if is_genesis else "")
                    with st.expander(label):
                        st.markdown('<div class="blockchain-box">', unsafe_allow_html=True)
                        st.write(f"**Indice:** {block.get('index')}")
                        st.write(f"**Timestamp:** {block.get('timestamp')}")
                        st.write(f"**Nonce:** {block.get('nonce')}")
                        
                        # Mostrar datos de transaccion (cada bloque = 1 transaccion)
                        sender = block.get("sender_id", "N/A")
                        recipient = block.get("recipient_id", "N/A")
                        msg_hash = block.get("message_hash", "")
                        
                        if sender != "N/A" and sender != "0":
                            st.write(f"**Remitente ID:** {sender}")
                            st.write(f"**Destinatario ID:** {recipient}")
                            st.write(f"**Hash del mensaje:** {msg_hash[:50]}..." if len(msg_hash) > 50 else f"**Hash del mensaje:** {msg_hash}")
                        else:
                            st.write("**Transaccion:** Ninguna (bloque genesis)")
                        
                        st.text(f"Hash anterior:\n{block.get('previous_hash', '')}")
                        st.text(f"Hash actual:\n{block.get('hash', '')}")
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"Error al obtener blockchain ({response.status_code}).")
        except requests.exceptions.ConnectionError:
            st.error("No se pudo conectar con el backend.")
        except Exception as e:
            st.error(f"Error inesperado: {e}")
    
    # Verificar integridad de la cadena
    st.markdown("---")
    st.subheader("Verificar Integridad")
    st.caption("Verifica que todos los bloques de la cadena esten correctamente encadenados.")
    
    if st.button("Verificar Cadena", key="verify_chain"):
        try:
            response = requests.get(
                f"{API_BASE}/blockchain/verify",
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("is_valid"):
                    st.success(f"La blockchain es VALIDA. {data.get('total_blocks', 0)} bloques verificados correctamente.")
                    st.write(data.get("message", ""))
                else:
                    st.error("La blockchain es INVALIDA. Se ha detectado una alteracion en la cadena.")
                    st.write(data.get("message", ""))
            else:
                st.error(f"Error al verificar ({response.status_code}).")
        except requests.exceptions.ConnectionError:
            st.error("No se pudo conectar con el backend.")
        except Exception as e:
            st.error(f"Error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">VaultChain - Sistema de Mensajeria Segura con Registro Inmutable</div>',
    unsafe_allow_html=True
)
