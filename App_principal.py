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

        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
            sign_out()
            st.toast("Sesión cerrada correctamente", icon="🌱")
            st.rerun()
        st.divider()

    # ------------------ ESTILOS GLOBALES Y DE TARJETAS (ESTILO DASHBOARD MODERNO) ------------------
    st.markdown("""
    <style>
    /* Fondo general de la app para que contrasten las tarjetas */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Banner de Bienvenida principal */
    .welcome-banner {
        background: linear-gradient(135deg, #e0f2fe 0%, #f0fdf4 100%);
        border-radius: 20px;
        padding: 35px;
        margin-bottom: 30px;
        border: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .welcome-text h1 {
        color: #0f172a;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .welcome-text p {
        color: #475569;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 0;
    }
    .welcome-badge {
        background-color: #10b981;
        color: white;
        padding: 6px 16px;
        border-radius: 50px;
        font-size: 1rem;
        font-weight: 600;
    }

    /* Sección de Funcionalidades / Misiones */
    .section-title {
        color: #1e293b;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Tarjetas Modernas */
    .modern-card {
        background: white;
        border-radius: 18px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #f1f5f9;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 310px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 15px;
    }

    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #cbd5e1;
    }

    .card-img-container {
        background-color: #f8fafc;
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 16px;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .modern-card img {
        height: 90px;
        object-fit: contain;
    }

    .modern-card h3 {
        font-size: 1.15rem;
        font-weight: 600;
        color: #0f172a;
        margin: 0 0 8px 0;
    }

    .modern-card p {
        font-size: 0.85rem;
        color: #64748b;
        line-height: 1.4;
        margin: 0;
    }
    
    /* Ajuste para los botones nativos de Streamlit debajo de las tarjetas */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        background-color: #f1f5f9 !important;
        color: #334155 !important;
        border: 1px solid #e2e8f0 !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #10b981 !important;
        color: white !important;
        border-color: #10b981 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. BANNER DE BIENVENIDA (Estilo de la segunda imagen)
    st.markdown(f"""
    <div class="welcome-banner">
        <div class="welcome-text">
            <h1>¡Hola, {st.session_state.usuario}! 👋</h1>
            <p>Gestiona y optimiza tus presupuestos desde tu panel de control.</p>
        </div>
        <div class="welcome-badge">
            🌱 GRINO APP
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. TÍTULO DE LA SECCIÓN DE MÓDULOS
    st.markdown('<div class="section-title">🛠️ Funcionalidades del Sistema</div>', unsafe_allow_html=True)

    # Datos de las páginas
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
            "key": "est",
            "imagen_path": "images/imagen5.png"
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

    # 3. RENDERIZADO EN COLUMNAS CON EL NUEVO DISEÑO
    cols = st.columns(5)

    for i, pagina in enumerate(paginas):
        with cols[i]:
            try:
                img_base64 = img_to_base64(pagina['imagen_path'])
                img_src = f"data:image/png;base64,{img_base64}"
            except Exception:
                img_src = "https://via.placeholder.com/150" # Por si falla alguna ruta

            # Render de la tarjeta HTML moderna
            st.markdown(
                f"""
                <div class="modern-card">
                    <div class="card-img-container">
                        <img src="{img_src}">
                    </div>
                    <div>
                        <h3>{pagina['titulo']}</h3>
                        <p>{pagina['descripcion']}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Botón estilizado mediante CSS global
            if st.button("Acceder", key=pagina['key'], use_container_width=True):
                st.switch_page(pagina['pagina'])


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