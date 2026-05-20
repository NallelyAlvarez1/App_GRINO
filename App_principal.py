import streamlit as st
from utils.auth import check_login, authenticate, register_user, sign_out
from utils.db import get_supabase_client
import base64

def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'usuario' not in st.session_state:
    st.session_state.usuario = "Invitado"

is_logged_in = check_login()


# ------------------- Contenido Principal de la App -------------------
if is_logged_in:
    supabase = get_supabase_client()

    with st.sidebar:
        st.markdown("**👤 Usuario:**")
        st.markdown(f"`{st.session_state.usuario}`")

        if st.button("🚪 Cerrar Sesión", type="primary", width='stretch'):
            sign_out()
            st.toast("Sesión cerrada correctamente", icon="🌱")
            st.rerun()
        st.divider()
        

    st.header("🌱GRINO - Gestión de Presupuestos 🛠️")
    st.subheader(f"Bienvenid@, {st.session_state.usuario}", divider="green")


    # ------------------ ESTILOS PARA LAS TARJETAS ------------------
    st.markdown("""
    <style>
    .centered-card {
        text-align: center;
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        margin: 8px 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 330px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .centered-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .centered-card img {
        width: 100%;
        height: 180px;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    .centered-card h3 {
        text-align: center;
        margin: 12px 0 8px 0;
        font-size: 1.3em;
        font-weight: 600;
        color: #1f2937;
    }

    .centered-card p {
        text-align: center;
        margin: 0;
        color: #6b7280;
        font-size: 0.9em;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

    paginas = [
        {
            "titulo": "Crear Presupuesto", 
            "descripcion": "Genera un nuevo presupuesto de trabajo detallado.", 
            "pagina": "pages/1_📄_presupuestos.py", 
            "key": "pres",
            "imagen_path": "images/imagen1.png"
        },
        {
            "titulo": "Historial", 
            "descripcion": "Revisa, edita o elimina presupuestos ya creados.", 
            "pagina": "pages/2_🕒_historial.py", 
            "key": "hist",
            "imagen_path": "images/imagen2.png"
        },
        {
            "titulo": "Estados de Pago", 
            "descripcion": "Genera estados de pago de Clientes.", 
            "pagina": "pages/5_📄_Estados_de_Pago.py", 
            "key": "cli",
            "imagen_path": "images/imagen1.png"
        },
        {
            "titulo": "Clientes Registrados", 
            "descripcion": "Revisa y/o elimina clientes registrados.", 
            "pagina": "pages/3_👥_clientes_y_lugares.py", 
            "key": "cli",
            "imagen_path": "images/imagen3.png"
        },
        {
            "titulo": "Ajustes", 
            "descripcion": "Revisa y/o actualiza los datos de tu cuenta.", 
            "pagina": "pages/4_⚙️_perfil.py", 
            "key": "per",
            "imagen_path": "images/imagen4.png"
        }
    ]

    st.markdown("""
    <style>
    .centered-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        margin-bottom: 1rem;
    }

    .card-img {
        width: 100%;
        height: 120px;
        border-radius: 10px;
        margin-bottom: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Crear columnas para las tarjetas
    cols = st.columns(4)

    # Renderizar las tarjetas en las columnas
    for i, pagina in enumerate(paginas):
        with cols[i]:
            img_base64 = img_to_base64(pagina['imagen_path'])

            st.markdown(
                f"""
                <div class="centered-card">
                    <img src="data:image/png;base64,{img_base64}" class="card-img">
                    <h3>{pagina['titulo']}</h3>
                    <p>{pagina['descripcion']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Acceder", key=pagina['key'], use_container_width=True):
                st.switch_page(pagina['pagina'])


    # --- 3. CONTENIDO PÚBLICO (USUARIO NO LOGUEADO) ---
else:
    st.subheader("Bienvenido a Grino 🧮", divider="blue")
    st.toast("Para acceder a las herramientas de gestión de presupuestos, por favor inicie sesión o regístrese.")

    tabs = st.tabs([f"🔑 Iniciar sesión", f"📝 Registrarse"])

    # ------------------- LOGIN -------------------
    with tabs[0]:
        st.markdown("##### Acceso al Sistema")
        with st.form("login_form"):
            email = st.text_input("Correo electrónico", key="login_email").strip().lower()
            password = st.text_input("Contraseña", type="password", key="login_password")
            
            if st.form_submit_button("Ingresar", type="primary", width='stretch'):
                if not email or not password:
                    st.error("⚠️ Por favor ingrese correo y contraseña.")
                else:
                    if authenticate(email, password):
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas o usuario no existe.")

    with tabs[1]:
        st.markdown("##### Crear una Cuenta")
        with st.form("register_form"):

            full_name = st.text_input("Nombre Completo", key="reg_full_name").strip()
            email_reg = st.text_input("Correo electrónico", key="reg_email").strip().lower()
            password_reg = st.text_input("Contraseña (mínimo 6 caracteres)", type="password", key="reg_password")
            password_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_confirm")

            if st.form_submit_button("Registrar", type="secondary", width='stretch'):
                if not email_reg or not password_reg or not full_name:
                    st.error("⚠️ Por favor ingrese su nombre, correo y contraseña.")
                elif password_reg != password_confirm:
                    st.error("❌ Las contraseñas no coinciden.")
                elif len(password_reg) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres.")
                elif register_user(email_reg, password_reg, full_name):
                    st.success("📩 Verifica tu email para completar el registro.")
                else:
                    st.error("❌ Error al registrar el usuario. El correo puede estar en uso.")