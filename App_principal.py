import streamlit as st
from utils.auth import check_login, authenticate, register_user, sign_out
from utils.db import get_supabase_client
import base64

def img_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'usuario' not in st.session_state:
    st.session_state.usuario = "Invitado"

# Assuming you have a check_login function, using a dummy for this example
# Replace with: is_logged_in = check_login()
# For demonstration, I will force login:
is_logged_in = True 


# ------------------- Contenido Principal de la App -------------------
if is_logged_in:
    # supabase = get_supabase_client() # Uncomment for your database

    with st.sidebar:
        st.markdown("**👤 Usuario:**")
        st.markdown(f"`{st.session_state.usuario}`")

        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
            # sign_out()
            st.toast("Sesión cerrada correctamente", icon="🌱")
            # st.rerun()
        st.divider()

    # ------------------ ESTILOS GLOBALES Y DE TARJETAS (ESTILO DASHBOARD COLORIDO) ------------------
    # The key is to add unique classes for colors and re-style the Streamlit buttons.
    st.markdown("""
    <style>
    /* Fondo general de la app para que contrasten las tarjetas */
    .stApp {
        background-color: #f1f5f9; /* Lighter background for pop */
    }
    
    /* Banner de Bienvenida principal - updated to match the original gradient suggestion */
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
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* ********************************************************** */
    /* Tarjetas Modernas COLORIDAS (Estilo de la imagen de referencia) */
    /* ********************************************************** */
    .modern-card {
        border-radius: 20px;
        padding: 30px;
        text-align: left; /* Left alignment like the ref */
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 380px; /* Increased height */
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* Space out content and button */
        margin-bottom: 15px;
        border: none; /* Removed border, using shadow and gradient */
        position: relative;
        overflow: hidden; /* For inner gradient overflow */
    }

    /* Hover effect */
    .modern-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 10px 10px -5px rgba(0, 0, 0, 0.08);
    }

    /* Specific Card Color Gradients (like the ref image) */
    .card-color-1 { background: linear-gradient(135deg, #f53d7a 0%, #f77062 100%); } /* Pink/Orange */
    .card-color-2 { background: linear-gradient(135deg, #f9a03c 0%, #fbc27b 100%); } /* Orange/Gold */
    .card-color-3 { background: linear-gradient(135deg, #626cfb 0%, #a4a9fe 100%); } /* Blue/Purple */
    .card-color-4 { background: linear-gradient(135deg, #9154f3 0%, #c4a1fe 100%); } /* Purple/Lavender */
    .card-color-5 { background: linear-gradient(135deg, #10b981 0%, #a7f3d0 100%); } /* Green/Mint */

    /* Contenedor de la imagen: Cleaned up, no background box */
    .card-img-container {
        display: flex;
        justify-content: center; /* Center image horizontally */
        align-items: center;
        margin-top: 10px;
        margin-bottom: 20px;
        flex-grow: 1; /* Allow image to take available space */
    }

    .modern-card img {
        height: 120px; /* Larger images */
        max-width: 90%;
        object-fit: contain;
        /* Optional: drop shadow for icons to stand out on dark gradient */
        filter: drop-shadow(0px 4px 4px rgba(0, 0, 0, 0.25)); 
    }

    /* Text styling inside cards */
    .modern-card .card-text {
        text-align: left;
        margin-bottom: 10px;
    }

    .modern-card h3 {
        font-size: 1.4rem;
        font-weight: 700;
        color: white; /* All text becomes white */
        margin: 0 0 5px 0;
    }

    .modern-card p {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.85); /* Slightly transparent white */
        line-height: 1.4;
        margin: 0;
    }
    
    /* ********************************************************** */
    /* AJUSTE PARA BOTONES ST.BUTTON (Estilo 'Play Now' de la referencia) */
    /* ********************************************************** */
    div.stButton > button {
        border-radius: 30px !important; /* Fully rounded like the ref */
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 10px 24px !important;
        transition: all 0.3s;
        text-transform: none; /* Kept text case */
        letter-spacing: 0.5px;
        width: 100%;
        margin-top: auto; /* Push to the bottom */
        display: block;
    }

    /* Native button look (white background, dark icon/text) */
    div.stButton > button {
        background-color: white !important;
        color: #0f172a !important; /* Dark text/icon */
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }

    /* Hover effect for the white button */
    div.stButton > button:hover {
        background-color: #f1f5f9 !important; /* Slight gray on hover */
        transform: scale(1.03); /* Subtle pop on hover */
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }

    /* Customizing the Streamlit generic button icons (like the st.button icon) */
    div.stButton > button span:first-child {
        margin-right: 8px; /* Space between icon and text */
        color: #0f172a !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # 1. BANNER DE BIENVENIDA
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

    # Datos de las páginas. Added 'color_class' for unique backgrounds
    paginas = [
        {
            "titulo": "Crear Presupuesto", 
            "descripcion": "Genera un nuevo presupuesto detallado.", 
            "pagina": "pages/1_📄_presupuestos.py", 
            "key": "pres",
            "imagen_path": "images/imagen1.png",
            "color_class": "card-color-1",
            "icon": "📄" # Added emoji icons to st.button like the ref
        },
        {
            "titulo": "Historial", 
            "descripcion": "Revisa, edita o elimina presupuestos.", 
            "pagina": "pages/2_🕒_historial.py", 
            "key": "hist",
            "imagen_path": "images/imagen2.png",
            "color_class": "card-color-2",
            "icon": "🕒"
        },
        {
            "titulo": "Estados de Pago", 
            "descripcion": "Genera estados de pago de Clientes.", 
            "pagina": "pages/5_📄_Estados_de_Pago.py", 
            "key": "est",
            "imagen_path": "images/imagen5.png",
            "color_class": "card-color-3",
            "icon": "💰"
        },
        {
            "titulo": "Clientes Registrados", 
            "descripcion": "Revisa y/o elimina clientes registrados.", 
            "pagina": "pages/3_👥_clientes_y_lugares.py", 
            "key": "cli",
            "imagen_path": "images/imagen3.png",
            "color_class": "card-color-4",
            "icon": "👥"
        },
        {
            "titulo": "Ajustes", 
            "descripcion": "Revisa y actualiza tus datos.", 
            "pagina": "pages/4_⚙️_perfil.py", 
            "key": "per",
            "imagen_path": "images/imagen4.png",
            "color_class": "card-color-5",
            "icon": "⚙️"
        }
    ]

    # 3. RENDERIZADO EN COLUMNAS CON EL NUEVO DISEÑO COLORIDO
    cols = st.columns(5)

    for i, pagina in enumerate(paginas):
        with cols[i]:
            # Convert image to base64 or use placeholder
            img_base64 = img_to_base64(pagina['imagen_path'])
            if img_base64:
                img_src = f"data:image/png;base64,{img_base64}"
            else:
                # Use a placeholder if file not found, you could use URL or different logic
                img_src = "https://via.placeholder.com/150/FFFFFF/CCCCCC?text=Ícono" 

            # Render of the colorful HTML card structure
            # Note the use of pagina['color_class'] in the outer div
            st.markdown(
                f"""
                <div class="modern-card {pagina['color_class']}">
                    <div class="card-text">
                        <h3>{pagina['titulo']}</h3>
                        <p>{pagina['descripcion']}</p>
                    </div>
                    <div class="card-img-container">
                        <img src="{img_src}">
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Botón estilizado mediante CSS global - added emoji icon and title
            if st.button(f"{pagina['icon']} Acceder", key=pagina['key'], use_container_width=True):
                # st.switch_page(pagina['pagina'])
                st.write(f"Accediendo a {pagina['titulo']}")


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