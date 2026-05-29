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

    # ------------------ ESTILOS GLOBALES: TARJETAS CUADRADAS GAMER ------------------
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

    /* Frase de llamado a la acción */
    .section-title {
        color: #0f172a;
        font-size: 1.7rem;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }

    /* --- TARJETA CUADRADA --- */
    .modern-card {
        border-radius: 24px;
        padding: 5px;
        box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        
        width: 100%;
        aspect-ratio: 1 / 1; /* Cuadrado perfecto */
        
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        box-sizing: border-box;
    }

    .modern-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 30px -8px rgba(0, 0, 0, 0.15);
    }

    /* Gradiantes vibrantes estilo juego */
    .card-color-1 { background: linear-gradient(135deg, #f43f5e 0%, #fda4af 90%); }
    .card-color-2 { background: linear-gradient(135deg, #f97316 0%, #fde047 90%); }
    .card-color-3 { background: linear-gradient(135deg, #2563eb 0%, #38bdf8 90%); }
    .card-color-4 { background: linear-gradient(135deg, #7c3aed 0%, #c084fc 90%); }
    .card-color-5 { background: linear-gradient(135deg, #059669 0%, #34d399 90%); }

    /* Título arriba a la izquierda */
    .card-top-title {
        text-align: center;
        width: 100%;
    }
    .modern-card h3 {
        font-size: 1.2rem;
        text-align: center;
        font-weight: 700;
        color: white;
        margin: 0;
        line-height: 1;
    }

    /* TEXTO DESCRIPTIVO CENTRADO EN EL ESPACIO MEDIO */
    .card-center-desc {
        flex-grow: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 1px;
    }
    .modern-card p {
        font-size: 0.95rem;
        color: rgba(255, 255, 255, 0.95);
        font-weight: 600;
        margin: 0;
        line-height: 1;
        text-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);
    }

    /* FILA INFERIOR (Botón izquierdo, PNG derecho) */
    .card-bottom-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        width: 100%;
        height: 35%; /* Controla el alto de la zona del botón/imagen */
    }

    /* Espacio reservado del botón para que no colisione con el PNG */
    .button-spacer {
        width: 52%;
    }

    /* Contenedor del PNG en la esquina inferior derecha */
    .card-img-container {
        width: 50%;
        height: 110%; /* Sobresale un poco hacia arriba para mejor look gamer */
        display: flex;
        justify-content: flex-end;
        align-items: flex-end;
        pointer-events: none; /* No interfiere con clics */
    }
    .card-img-container img {
        max-height: 100%;
        max-width: 100%;
        object-fit: contain;
        /* Sombra suave para despegar el PNG del fondo */
        filter: drop-shadow(2px 6px 8px rgba(0, 0, 0, 0.15)); 
    }

    /* --- BOTÓN ESTILO "PLAY NOW" (SUBIDO CON MARGEN NEGATIVO) --- */
    .st-btn-wrapper {
        margin-top: -52px; /* Sube el botón nativo exactamente al espacio izquierdo reservado */
        width: 52%; 
        position: relative; 
        z-index: 10;
    }
    
    div.stButton > button {
        border-radius: 40px !important; /* Píldora perfecta */
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        background-color: white !important;
        color: #0f172a !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12) !important;
        transition: all 0.2s ease;
        width: 100%;
        padding: 8px 12px !important;
    }
    
    div.stButton > button:hover {
        background-color: #f8fafc !important;
        transform: scale(1.05);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.18) !important;
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

    # 2. NUEVA FRASE DE LLAMADO A LA ACCIÓN
    st.markdown('<div class="section-title">🚀 ¿Qué quieres hacer hoy? </div>', unsafe_allow_html=True)

    # Estructura de datos limpia
    paginas = [
        {
            "titulo": "Presupuestos", 
            "descripcion": "Genera un nuevo presupuesto detallado para tus trabajos.", 
            "pagina": "pages/1_📄_presupuestos.py", 
            "key": "pres",
            "imagen_path": "images/imagen1.png",
            "color_class": "card-color-1",
            "btn_text": "✏️ Crear"
        },
        {
            "titulo": "Historial", 
            "descripcion": "Revisa, edita o elimina los presupuestos anteriores.", 
            "pagina": "pages/2_🕒_historial.py", 
            "key": "hist",
            "imagen_path": "images/imagen2.png",
            "color_class": "card-color-2",
            "btn_text": "🔍 Ver"
        },
        {
            "titulo": "Estados de Pago", 
            "descripcion": "Controla y gestiona las cuentas de tus clientes.", 
            "pagina": "pages/5_📄_Estados_de_Pago.py", 
            "key": "est",
            "imagen_path": "images/imagen5.png",
            "color_class": "card-color-3",
            "btn_text": "💰 Pagos"
        },
        {
            "titulo": "Clientes", 
            "descripcion": "Administra el registro y datos de tus clientes.", 
            "pagina": "pages/3_👥_clientes_y_lugares.py", 
            "key": "cli",
            "imagen_path": "images/imagen3.png",
            "color_class": "card-color-4",
            "btn_text": "👥 Lista"
        },
        {
            "titulo": "Ajustes", 
            "descripcion": "Actualiza la información y preferencias de tu cuenta.", 
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

            # Render HTML de la tarjeta con la descripción centrada e imagen abajo a la derecha
            st.markdown(
                f"""
                <div class="modern-card {pagina['color_class']}">
                    <div class="card-top-title">
                        <h3>{pagina['titulo']}</h3>
                    </div>
                    <div class="card-center-desc">
                        <p>{pagina['descripcion']}</p>
                    </div>
                    <div class="card-bottom-row">
                        <div class="button-spacer"></div>
                        <div class="card-img-container">
                            <img src="{img_src}">
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Inyección limpia del botón en el área inferior izquierda
            st.markdown('<div class="st-btn-wrapper">', unsafe_allow_html=True)
            if st.button(pagina['btn_text'], key=pagina['key'], use_container_width=True):
                st.switch_page(pagina['pagina'])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Margen inferior de seguridad para separar el layout de lo que pongas abajo
            st.markdown('<div style="margin-bottom: 40px;"></div>', unsafe_allow_html=True)

else:
    # --- LOGIN / REGISTRO ---
    st.subheader("Bienvenido a Grino 🧮", divider="blue")
    st.toast("Por favor, inicia sesión para continuar.")
    tabs = st.tabs(["🔑 Iniciar sesión", "📝 Registrarse"])

    with tabs[0]:
        st.markdown("##### Acceso al Sistema")
        with st.form("login_form"):
            email = st.text_input("Correo electrónico", key="login_email").strip().lower()
            password = st.text_input("Contraseña", type="password", key="login_password")
            if st.form_submit_button("Ingresar", type="primary"):
                if authenticate(email, password):
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")

    with tabs[1]:
        st.markdown("##### Crear una Cuenta")
        with st.form("register_form"):
            full_name = st.text_input("Nombre Completo", key="reg_full_name").strip()
            email_reg = st.text_input("Correo electrónico", key="reg_email").strip().lower()
            password_reg = st.text_input("Contraseña", type="password", key="reg_password")
            password_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_confirm")

            if st.form_submit_button("Registrar", type="secondary"):
                if password_reg != password_confirm:
                    st.error("❌ Las contraseñas no coinciden.")
                elif register_user(email_reg, password_reg, full_name):
                    st.success("📩 Cuenta creada. Verifica tu email.")
                else:
                    st.error("❌ Error al registrar.")