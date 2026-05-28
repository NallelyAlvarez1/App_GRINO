import streamlit as st
from utils.auth import check_login, authenticate, register_user, sign_out
from utils.db import get_supabase_client
import base64

def img_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

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

    # ------------------ ESTILOS GLOBALES: TARJETAS CUADRADAS GAMER/MODERNAS ------------------
    st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Banner de Bienvenida */
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

    .section-title {
        color: #1e293b;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* --- CONTENEDOR DE LA TARJETA (AHORA CUADRADA) --- */
    .modern-card {
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        
        /* Fuerza a que la tarjeta sea un cuadrado perfecto basado en su ancho */
        width: 100%;
        aspect-ratio: 1 / 1; 
        
        /* Distribución interna: Info arriba, fila interactiva abajo */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        box-sizing: border-box;
    }

    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    /* Colores de Fondo (Gradients intensos estilo juego) */
    .card-color-1 { background: linear-gradient(135deg, #ff3366 0%, #ff6b6b 100%); }
    .card-color-2 { background: linear-gradient(135deg, #ff9233 0%, #ffbe53 100%); }
    .card-color-3 { background: linear-gradient(135deg, #3b52f6 0%, #6366f1 100%); }
    .card-color-4 { background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%); }
    .card-color-5 { background: linear-gradient(135deg, #059669 0%, #34d399 100%); }

    /* Textos alineados arriba a la izquierda */
    .card-header-text {
        text-align: left;
    }

    /* Título GRANDE como pediste */
    .modern-card h3 {
        font-size: 1.6rem;
        font-weight: 800;
        color: white;
        margin: 0 0 4px 0;
        line-height: 1.2;
    }

    /* Texto secundario/Subtítulo (ej: 'Genera un nuevo...') */
    .modern-card p {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.85);
        margin: 0;
        font-weight: 500;
    }

    /* Fila inferior para el botón y la imagen en la esquina */
    .card-footer-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        width: 100%;
        height: 45%; /* Limita el espacio de la sección inferior */
    }

    /* Imagen posicionada abajo a la derecha de la card */
    .card-img-corner {
        width: 45%;
        height: 100%;
        display: flex;
        justify-content: flex-end;
        align-items: flex-end;
    }

    .card-img-corner img {
        max-height: 100%;
        max-width: 100%;
        object-fit: contain;
        filter: drop-shadow(0px 8px 12px rgba(0, 0, 0, 0.15));
    }

    /* Contenedor invisible para que el botón de Streamlit se posicione abajo a la izquierda */
    .button-container-left {
        width: 50%;
    }
    
    /* --- REDISEÑO DEL BOTÓN NATIVO DE STREAMLIT --- */
    div.stButton > button {
        border-radius: 20px !important; /* Bordes redondeados tipo píldora */
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        background-color: white !important;
        color: #1e293b !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease;
        width: 100%;
        padding: 8px 16px !important;
    }
    
    div.stButton > button:hover {
        background-color: #f8fafc !important;
        transform: scale(1.05);
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
        <div class="welcome-badge">🌱 GRINO APP</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. TÍTULO DE LA SECCIÓN
    st.markdown('<div class="section-title">🛠️ Funcionalidades del Sistema</div>', unsafe_allow_html=True)

    # Estructura de datos con clases de colores e íconos para el botón
    paginas = [
        {
            "titulo": "Crear Presupuesto", 
            "descripcion": "Genera un nuevo documento.", 
            "pagina": "pages/1_📄_presupuestos.py", 
            "key": "pres",
            "imagen_path": "images/imagen1.png",
            "color_class": "card-color-1",
            "btn_text": "📄 Crear"
        },
        {
            "titulo": "Historial", 
            "descripcion": "Revisa tus registros.", 
            "pagina": "pages/2_🕒_historial.py", 
            "key": "hist",
            "imagen_path": "images/imagen2.png",
            "color_class": "card-color-2",
            "btn_text": "🕒 Revisa"
        },
        {
            "titulo": "Estados de Pago", 
            "descripcion": "Control de ingresos.", 
            "pagina": "pages/5_📄_Estados_de_Pago.py", 
            "key": "est",
            "imagen_path": "images/imagen5.png",
            "color_class": "card-color-3",
            "btn_text": "💰 Ver"
        },
        {
            "titulo": "Clientes", 
            "descripcion": "Base de datos.", 
            "pagina": "pages/3_👥_clientes_y_lugares.py", 
            "key": "cli",
            "imagen_path": "images/imagen3.png",
            "color_class": "card-color-4",
            "btn_text": "👥 Clientes"
        },
        {
            "titulo": "Ajustes", 
            "descripcion": "Configura tu cuenta.", 
            "pagina": "pages/4_⚙️_perfil.py", 
            "key": "per",
            "imagen_path": "images/imagen4.png",
            "color_class": "card-color-5",
            "btn_text": "⚙️ Perfil"
        }
    ]

    # 3. RENDERIZADO EN 5 COLUMNAS
    cols = st.columns(5)

    for i, pagina in enumerate(paginas):
        with cols[i]:
            img_base64 = img_to_base64(pagina['imagen_path'])
            img_src = f"data:image/png;base64,{img_base64}" if img_base64 else "https://via.placeholder.com/120/FFFFFF/000000?text=Icon"

            # Renderizado de la estructura visual (Fondo, Título grande y la Imagen abajo a la derecha)
            st.markdown(
                f"""
                <div class="modern-card {pagina['color_class']}">
                    <div class="card-header-text">
                        <h3>{pagina['titulo']}</h3>
                        <p>{pagina['descripcion']}</p>
                    </div>
                    <div class="card-footer-row">
                        <div class="button-container-left">
                            </div>
                        <div class="card-img-corner">
                            <img src="{img_src}">
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Para superponer o colocar el botón de Streamlit exactamente abajo a la izquierda, 
            # usamos un truco de margen negativo de CSS para subirlo al contenedor vacío asignado arriba.
            st.markdown('<div style="margin-top: -65px; width: 48%; position: relative; z-index: 10;">', unsafe_allow_html=True)
            if st.button(pagina['btn_text'], key=pagina['key'], use_container_width=True):
                st.switch_page(pagina['pagina'])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Espaciador inferior para evitar roturas de layout
            st.markdown('<div style="margin-bottom: 50px;"></div>', unsafe_allow_html=True)


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