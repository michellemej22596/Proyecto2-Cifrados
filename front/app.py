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
    '<div class="subtitle">Registro - Autenticación</div>',
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
tab1, tab2 = st.tabs(["📝 Registro", "🔑 Login"])

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
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Sesión actual</div>', unsafe_allow_html=True)
    st.subheader("Usuario autenticado")

    st.success("Hay una sesión activa en esta aplicación.")
    st.write(f"**Tipo de token:** {st.session_state.get('token_type', 'bearer')}")

    with st.expander("Ver token almacenado en sesión"):
        st.markdown(
            f'<div class="token-box">{st.session_state["access_token"]}</div>',
            unsafe_allow_html=True
        )

    if st.button("Cerrar sesión"):
        st.session_state["access_token"] = None
        st.session_state["token_type"] = None
        st.success("Sesión cerrada correctamente.")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">Proyecto de criptografía</div>',
    unsafe_allow_html=True
)