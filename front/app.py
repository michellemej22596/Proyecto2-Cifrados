import requests
import streamlit as st

API_BASE = "http://localhost:8000"

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Crypto Users",
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
st.markdown('<div class="main-title">🔐 Crypto Users</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Registro - Autenticación - Mensajería cifrada</div>',
    unsafe_allow_html=True
)

# =========================
# SESSION DEFAULTS
# =========================
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

if "token_type" not in st.session_state:
    st.session_state["token_type"] = None

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Registro",
    "🔑 Login",
    "📨 Enviar mensaje",
    "📬 Ver mensajes",
    "🔓 Descifrar",
])

# =========================
# REGISTRO
# =========================
with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Nuevo usuario</div>', unsafe_allow_html=True)
    st.subheader("Crear cuenta")

    st.caption("Completa tus datos para registrar un usuario y generar automáticamente su par de llaves.")

    with st.form("register_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Nombre completo", placeholder="Juan Pérez")

        with col2:
            email = st.text_input("Correo electrónico", placeholder="juan@ejemplo.com")

        password = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres")
        password_confirm = st.text_input("Confirmar contraseña", type="password")

        submitted = st.form_submit_button("Registrarse")

    if submitted:
        if not name or not email or not password or not password_confirm:
            st.error("Completa todos los campos.")
        elif len(password) < 8:
            st.error("La contraseña debe tener al menos 8 caracteres.")
        elif password != password_confirm:
            st.error("Las contraseñas no coinciden.")
        else:
            with st.spinner("Registrando usuario y generando llaves..."):
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

                        with st.expander("Ver llave pública generada"):
                            st.code(data["public_key_pem"], language="text")

                        st.info(
                            "La llave privada fue cifrada de forma segura con una clave derivada "
                            "de la contraseña usando PBKDF2-HMAC-SHA256."
                        )

                    elif response.status_code == 409:
                        st.error("Ese correo electrónico ya está registrado.")
                    elif response.status_code == 422:
                        errors = response.json().get("detail", [])
                        for err in errors:
                            campo = err.get("loc", ["campo"])[-1]
                            mensaje = err.get("msg", "Valor inválido")
                            st.error(f"{campo}: {mensaje}")
                    else:
                        st.error(f"Error del servidor ({response.status_code}): {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("No se pudo conectar con el backend. Verifica que esté corriendo en localhost:8000.")
                except requests.exceptions.Timeout:
                    st.error("El backend tardó demasiado en responder.")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Autenticación</div>', unsafe_allow_html=True)
    st.subheader("Iniciar sesión")

    st.caption("Ingresa tus credenciales para autenticarte y recibir un token JWT.")

    with st.form("login_form"):
        login_email = st.text_input("Correo electrónico", placeholder="juan@ejemplo.com", key="login_email")
        login_password = st.text_input("Contraseña", type="password", key="login_password")

        login_submitted = st.form_submit_button("Iniciar sesión")

    if login_submitted:
        if not login_email or not login_password:
            st.error("Debes ingresar correo y contraseña.")
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

                        st.success("Login exitoso.")

                        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                        st.markdown("**Token JWT generado**")
                        st.markdown(
                            f'<div class="token-box">{data["access_token"]}</div>',
                            unsafe_allow_html=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)

                    elif response.status_code == 401:
                        st.error("Credenciales inválidas.")
                    elif response.status_code == 422:
                        errors = response.json().get("detail", [])
                        for err in errors:
                            campo = err.get("loc", ["campo"])[-1]
                            mensaje = err.get("msg", "Valor inválido")
                            st.error(f"{campo}: {mensaje}")
                    else:
                        st.error(f"Error del servidor ({response.status_code}): {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("No se pudo conectar con el backend. Verifica que esté corriendo en localhost:8000.")
                except requests.exceptions.Timeout:
                    st.error("El backend tardó demasiado en responder.")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SESIÓN ACTIVA
# =========================
if st.session_state.get("access_token"):
    with st.sidebar:
        st.markdown("### Sesión activa")
        st.success("Autenticado")
        with st.expander("Ver token"):
            st.markdown(
                f'<div class="token-box">{st.session_state["access_token"]}</div>',
                unsafe_allow_html=True
            )
        if st.button("Cerrar sesión"):
            st.session_state["access_token"] = None
            st.session_state["token_type"] = None
            st.rerun()

# =========================
# ENVIAR MENSAJE
# =========================
with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Enviar mensaje cifrado")

    inner_tab1, inner_tab2 = st.tabs(["🔒 AES compartido", "🔐 Híbrido RSA-OAEP"])

    # ---- AES compartido (sin auth) ----
    with inner_tab1:
        st.markdown('<div class="badge">Sin autenticación requerida</div>', unsafe_allow_html=True)
        st.caption("Cifra el mensaje con AES-256-GCM usando la clave compartida del servidor.")

        with st.form("aes_form"):
            aes_content = st.text_area("Mensaje", placeholder="Escribe tu mensaje...", key="aes_content")
            aes_submitted = st.form_submit_button("Enviar")

        if aes_submitted:
            if not aes_content.strip():
                st.error("El mensaje no puede estar vacío.")
            else:
                with st.spinner("Cifrando con AES-256-GCM..."):
                    try:
                        response = requests.post(
                            f"{API_BASE}/messages/",
                            json={"content": aes_content},
                            timeout=15,
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"Mensaje enviado. ID: **{data['id']}**")
                            st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                            st.markdown("**Detalles del cifrado**")
                            st.text(f"Ciphertext (Base64):\n{data['ciphertext']}")
                            st.text(f"Nonce (Base64):\n{data['nonce']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif response.status_code == 422:
                            st.error("Datos inválidos.")
                        else:
                            st.error(f"Error ({response.status_code}): {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("No se pudo conectar con el backend.")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")

    # ---- Híbrido RSA-OAEP (con auth) ----
    with inner_tab2:
        st.markdown('<div class="badge">Requiere sesión activa</div>', unsafe_allow_html=True)
        st.caption(
            "Genera una clave AES-256 efímera, cifra el mensaje con AES-256-GCM "
            "y cifra la clave con la llave pública RSA-OAEP del destinatario."
        )

        if not st.session_state.get("access_token"):
            st.warning("Inicia sesión en la pestaña **Login** para usar el cifrado híbrido.")
        else:
            with st.form("hybrid_form"):
                recipient_id = st.number_input(
                    "ID del destinatario",
                    min_value=1,
                    step=1,
                    help="El ID numérico del usuario que recibirá el mensaje.",
                )
                hybrid_content = st.text_area("Mensaje", placeholder="Escribe tu mensaje...", key="hybrid_content")
                hybrid_submitted = st.form_submit_button("Cifrar y enviar")

            if hybrid_submitted:
                if not hybrid_content.strip():
                    st.error("El mensaje no puede estar vacío.")
                else:
                    with st.spinner("Generando clave efímera y cifrando con RSA-OAEP..."):
                        try:
                            response = requests.post(
                                f"{API_BASE}/messages/hybrid/",
                                json={"content": hybrid_content, "recipient_id": int(recipient_id)},
                                headers={"Authorization": f"Bearer {st.session_state['access_token']}"},
                                timeout=15,
                            )
                            if response.status_code == 201:
                                data = response.json()
                                st.success(f"Mensaje híbrido enviado. ID: **{data['id']}**")
                                st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                                st.markdown("**Detalles del cifrado**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Remitente ID:** {data.get('sender_id')}")
                                with col2:
                                    st.write(f"**Destinatario ID:** {data.get('recipient_id')}")
                                st.text(f"Ciphertext (Base64):\n{data['ciphertext']}")
                                st.text(f"Nonce (Base64):\n{data['nonce']}")
                                st.text(f"Clave AES cifrada (RSA-OAEP):\n{data.get('encrypted_key', '')}")
                                st.markdown('</div>', unsafe_allow_html=True)
                                st.info(
                                    f"Guarda el ID **{data['id']}** para que el destinatario pueda descifrar "
                                    "el mensaje en la pestaña Descifrar."
                                )
                            elif response.status_code == 404:
                                st.error("Destinatario no encontrado. Verifica el ID.")
                            elif response.status_code == 401:
                                st.error("Sesión expirada. Vuelve a iniciar sesión.")
                            elif response.status_code == 422:
                                st.error("Datos inválidos.")
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
    st.caption("Lista todos los mensajes cifrados guardados en el servidor.")

    if st.button("Actualizar lista"):
        st.rerun()

    try:
        response = requests.get(f"{API_BASE}/messages/", timeout=10)
        if response.status_code == 200:
            messages = response.json()
            if not messages:
                st.info("No hay mensajes aún. Envía uno desde la pestaña Enviar mensaje.")
            else:
                st.write(f"**{len(messages)} mensaje(s) encontrado(s)**")
                for msg in messages:
                    with st.expander(f"Mensaje #{msg['id']}"):
                        st.text(f"Ciphertext (Base64):\n{msg['ciphertext']}")
                        st.text(f"Nonce (Base64):\n{msg['nonce']}")
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
    st.markdown('<div class="badge">Requiere sesión activa</div>', unsafe_allow_html=True)
    st.subheader("Descifrar mensaje híbrido")
    st.caption(
        "Usa tu llave privada RSA (protegida con tu contraseña) para recuperar "
        "la clave AES efímera y descifrar el mensaje."
    )

    if not st.session_state.get("access_token"):
        st.warning("Inicia sesión en la pestaña **Login** para descifrar mensajes.")
    else:
        with st.form("decrypt_form"):
            decrypt_msg_id = st.number_input(
                "ID del mensaje",
                min_value=1,
                step=1,
                help="El ID del mensaje híbrido que quieres descifrar.",
            )
            decrypt_password = st.text_input(
                "Tu contraseña",
                type="password",
                help="Necesaria para desbloquear tu llave privada RSA.",
            )
            decrypt_submitted = st.form_submit_button("Descifrar")

        if decrypt_submitted:
            if not decrypt_password:
                st.error("Ingresa tu contraseña.")
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
                                f'<div class="plaintext-box">📩 {data["plaintext"]}</div>',
                                unsafe_allow_html=True,
                            )
                        elif response.status_code == 403:
                            st.error("No eres el destinatario de este mensaje.")
                        elif response.status_code == 401:
                            st.error("Contraseña incorrecta o sesión expirada.")
                        elif response.status_code == 404:
                            st.error("Mensaje no encontrado.")
                        elif response.status_code == 400:
                            st.error("Este mensaje no usa cifrado híbrido.")
                        else:
                            st.error(f"Error ({response.status_code}): {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("No se pudo conectar con el backend.")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">Proyecto de criptografía</div>',
    unsafe_allow_html=True
)
