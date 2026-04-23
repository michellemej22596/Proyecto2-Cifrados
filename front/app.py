import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Crypto Users", page_icon="🔐", layout="centered")

st.title("🔐 Crypto Users")

tab1, tab2 = st.tabs(["Registro", "Login"])

# =========================
# REGISTRO
# =========================
with tab1:
    st.subheader("Registro de usuario")

    with st.form("register_form"):
        name = st.text_input("Nombre completo", placeholder="Juan Pérez")
        email = st.text_input("Correo electrónico", placeholder="juan@ejemplo.com")
        password = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres")
        password_confirm = st.text_input("Confirmar contraseña", type="password")
        submitted = st.form_submit_button("Registrarse", use_container_width=True)

    if submitted:
        if not name or not email or not password:
            st.error("Todos los campos son obligatorios.")
        elif len(password) < 8:
            st.error("La contraseña debe tener al menos 8 caracteres.")
        elif password != password_confirm:
            st.error("Las contraseñas no coinciden.")
        else:
            with st.spinner("Registrando usuario y generando llaves RSA-2048..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/auth/register",
                        json={"name": name, "email": email, "password": password},
                        timeout=30,
                    )
                    if response.status_code == 201:
                        data = response.json()
                        st.success(f"¡Usuario registrado exitosamente! ID asignado: **{data['id']}**")
                        with st.expander("Llave pública RSA-2048 generada", expanded=True):
                            st.code(data["public_key_pem"], language="text")
                        st.info(
                            "Tu llave privada fue cifrada con una clave derivada de tu contraseña "
                            "(PBKDF2-HMAC-SHA256) y almacenada de forma segura en el servidor."
                        )
                    elif response.status_code == 409:
                        st.error("Ese correo electrónico ya está registrado.")
                    elif response.status_code == 422:
                        errors = response.json().get("detail", [])
                        for err in errors:
                            st.error(f"{err.get('loc', ['campo'])[-1]}: {err.get('msg', '')}")
                    else:
                        st.error(f"Error del servidor ({response.status_code}): {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("No se pudo conectar con el backend. ¿Está corriendo en localhost:8000?")
                except requests.exceptions.Timeout:
                    st.error("El servidor tardó demasiado en responder.")

# =========================
# LOGIN
# =========================
with tab2:
    st.subheader("Inicio de sesión")

    with st.form("login_form"):
        login_email = st.text_input("Correo electrónico", placeholder="juan@ejemplo.com", key="login_email")
        login_password = st.text_input("Contraseña", type="password", key="login_password")
        login_submitted = st.form_submit_button("Iniciar sesión", use_container_width=True)

    if login_submitted:
        if not login_email or not login_password:
            st.error("Debes ingresar correo y contraseña.")
        else:
            with st.spinner("Verificando credenciales..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/auth/login",
                        json={"email": login_email, "password": login_password},
                        timeout=15,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["access_token"] = data["access_token"]
                        st.session_state["token_type"] = data["token_type"]

                        st.success("¡Login exitoso!")
                        st.write("Token JWT generado:")
                        st.code(data["access_token"], language="text")

                    elif response.status_code == 401:
                        st.error("Credenciales inválidas.")
                    elif response.status_code == 422:
                        errors = response.json().get("detail", [])
                        for err in errors:
                            st.error(f"{err.get('loc', ['campo'])[-1]}: {err.get('msg', '')}")
                    else:
                        st.error(f"Error del servidor ({response.status_code}): {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("No se pudo conectar con el backend. ¿Está corriendo en localhost:8000?")
                except requests.exceptions.Timeout:
                    st.error("El servidor tardó demasiado en responder.")

if "access_token" in st.session_state:
    st.divider()
    st.subheader("Sesión actual")

    st.success("Hay un usuario autenticado en esta sesión.")
    st.write(f"Tipo de token: **{st.session_state.get('token_type', 'bearer')}**")

    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.success("Sesión cerrada correctamente")
        st.rerun()