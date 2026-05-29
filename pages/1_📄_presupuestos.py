from typing import Any, Dict
import streamlit as st
import os
import time
import uuid
from utils.pdf import generar_pdf, mostrar_boton_descarga_pdf
from utils.auth import check_login, sign_out
from utils.components import (
    show_cliente_lugar_selector,
    show_items_presupuesto,
    show_trabajos_simples,
    show_edited_presupuesto,
    show_resumen,
    safe_numeric_value
)
from utils.db import save_presupuesto_completo
from utils.autosave import AutoSaveManager, capture_current_state, restore_draft_state

# Configuración de página (Debe ser lo primero)
st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")

# ------------------ ESTILOS VISUALES LIMPIOS Y CORREGIDOS ------------------
st.markdown("""
<style>
/* Fondo general de la aplicación */
.stApp {
    background-color: #f8fafc;
}

/* Reducir espacios por defecto en inputs y títulos */
.stTextInput, .stNumberInput, .stSelectbox, .stButton, .stTextArea {
    margin-bottom: -0.2rem;
    margin-top: -0.2rem;
}
h2, h3, h4 {
    margin-top: 0.2rem !important;
    margin-bottom: 0.4rem !important;
}

/* --- Rediseño de Inputs de Streamlit (Estilo Plano y Elegante) --- */
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    transition: all 0.2s ease;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #10b981 !important; 
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
}

/* --- CONTENEDORES PROPIOS (Evita el bug de sub-cards en las columnas) --- */
.main-work-card {
    background-color: #ffffff;
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    height: 100%;
}

.resumen-work-card {
    background: linear-gradient(180deg, #ffffff 0%, #fdfdfd 100%);
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #10b981; /* Acento verde minimalista */
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    height: 100%;
}

/* --- BARRA DE ACCIONES SUPERIOR (Plana, limpia y sin doble caja) --- */
.status-bar-container {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 25px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}

/* --- BOTÓN DE GUARDADO PRINCIPAL --- */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 12px 24px !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15) !important;
    transition: all 0.2s ease;
    width: 100%;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 15px rgba(16, 185, 129, 0.25) !important;
}

/* --- BOTONES SECUNDARIOS (Limpiar, Agregar) --- */
div.stButton > button[kind="secondary"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
    background-color: #f1f5f9 !important;
    color: #475569 !important;
    border: 1px solid #e2e8f0 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #e2e8f0 !important;
    color: #1e293b !important;
}
</style>
""", unsafe_allow_html=True)


def calcular_total(items_data: Dict[str, Any]) -> float:
    """Calcula el total general del presupuesto, usando la utilidad de valores seguros."""
    total = 0
    if not items_data or not isinstance(items_data, dict):
        return 0
        
    for categoria, data in items_data.items():
        if not isinstance(data, dict):
            continue
        items = data.get('items', [])
        if isinstance(items, list):
            total += sum(safe_numeric_value(item.get('total', 0)) for item in items)
        total += safe_numeric_value(data.get('mano_obra', 0))
    return total


# VERIFICAR LOGIN PRIMERO
is_logged_in = check_login()

if 'persistent_session_id' not in st.session_state:
    st.session_state['persistent_session_id'] = str(uuid.uuid4())

user_id = st.session_state.get('user_id')
autosave_manager = AutoSaveManager(user_id, "draft_presupuesto_principal")

# --- VERIFICAR BORRADOR ---
if autosave_manager.has_draft() and not st.session_state.get('draft_restored', False):
    draft = autosave_manager.load_draft()
    if draft:
        draft_age = autosave_manager.get_draft_age()
        
        warning_container = st.empty()
        with warning_container.container():
            st.warning(f"📝 Se encontró un borrador guardado {draft_age}")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🔄 Cargar Borrador", use_container_width=True, key="load_draft_main"):
                    restore_draft_state(draft)
            with col2:
                if st.button("👀 Ver Vista Previa", use_container_width=True, key="preview_draft_main"):
                    with st.expander("Vista previa del borrador", expanded=True):
                        st.json(draft)
            with col3:
                if st.button("🗑️ Descartar", use_container_width=True, key="discard_draft_main"):
                    autosave_manager.clear_draft()
                    st.rerun()

if not is_logged_in:
    st.error("🔒 No has iniciado sesión. Serás redirigido al inicio...")
    st.stop()

# SIDEBAR NATIVO
with st.sidebar:
    st.markdown("**👤 Usuario:**")
    st.markdown(f"`{st.session_state.usuario}`")
    
    with st.expander("🔧 Debug", expanded=False):
        if st.button("📊 Ver Estado Actual"):
            st.write("Session State:", {k: v for k, v in st.session_state.items() if not k.startswith('_')})
    
    if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
        sign_out()
        st.rerun()

# --- HEADER PREMIUM ---
st.markdown("""
<div style="
    background: linear-gradient(135deg, #e6f4ea 0%, #f4fbf7 100%);
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #a7f3d0;
    margin-bottom: 22px;
">
    <h1 style="color: #065f46; margin: 0; font-size: 1.8rem; font-weight: 800;">📑 Generador de Presupuestos</h1>
    <p style="color: #047857; margin: 4px 0 0 0; font-size: 0.95rem; font-weight: 500;">Estructura cotizaciones y cálculos limpios para tus clientes.</p>
</div>
""", unsafe_allow_html=True)

# ========== BARRA DE CONTROL SUPERIOR (CORREGIDA, SIN CAJAS RARAS) ==========
st.markdown('<div class="status-bar-container">', unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    if st.button("🧹 Limpiar / Nuevo presupuesto", type="secondary", use_container_width=True):
        keys_to_delete = [
            "categorias", "descripcion", "items_data", "cliente_id",
            "cliente_nombre", "lugar_trabajo_id", "lugar_nombre",
            "trabajos_simples", "total_general", "draft_restored"
        ]
        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]
        autosave_manager.clear_draft()
        st.rerun()

with col_btn2:
    if autosave_manager.has_draft():
        draft_age = autosave_manager.get_draft_age()
        st.markdown(f"<div style='color: #64748b; font-size: 0.85rem; margin-bottom: 4px;'>💾 Último autoguardado: <b>{draft_age}</b></div>", unsafe_allow_html=True)
        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("💾 Guardar Borrador", key="manual_save_main", use_container_width=True):
                current_state = capture_current_state()
                if autosave_manager.save_draft(current_state):
                    st.toast("✅ Borrador guardado!")
        with col_clear:
            if st.button("🗑️ Eliminar Borrador", key="clear_draft_main", use_container_width=True):
                autosave_manager.clear_draft()
                st.rerun()
    else:
        st.markdown("<div style='padding-top: 10px; color: #94a3b8; font-size: 0.9rem;'>💾 Borrador automático listo e inactivo</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ========== SECCIÓN SELECTORES (Se ven limpios y nativos ahora) ==========
cliente_id, cliente_nombre, lugar_trabajo_id, lugar_nombre, descripcion = show_cliente_lugar_selector(user_id)

st.session_state['cliente_id'] = cliente_id
st.session_state['cliente_nombre'] = cliente_nombre
st.session_state['lugar_trabajo_id'] = lugar_trabajo_id
st.session_state['lugar_nombre'] = lugar_nombre
st.session_state['descripcion'] = descripcion

# ========== SECCIÓN DE TRABAJO (DIVIDIDA CORRECTAMENTE) ==========
st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
col_left, col_right = st.columns([10, 10], gap="large")

with col_left:
    # Envolvemos los ítems de forma limpia con HTML personalizado, no con selectores globales de columna
    st.markdown('<div class="main-work-card">', unsafe_allow_html=True)
    st.subheader("📦 Items del Presupuesto", divider="blue")
    
    initial_items = st.session_state.get('items_data', None)
    items_data = show_items_presupuesto(user_id, initial_data=initial_items)
    
    if items_data:
        st.session_state['items_data'] = items_data

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🛠️ Añadir trabajo rápido")
    show_trabajos_simples(items_data)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="resumen-work-card">', unsafe_allow_html=True)
    st.subheader("📊 Resumen del Presupuesto", divider="blue")
    total_general = show_resumen(items_data)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== SECCIÓN EDICIÓN ===========
if items_data and any(len(data.get('items', [])) > 0 for data in items_data.values()):
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    st.subheader("✏️ Editar Items Agregados", divider="blue")
    items_data = show_edited_presupuesto(user_id)
    if items_data:
        st.session_state['items_data'] = items_data

# ========== ACCIÓN DE GUARDADO FINAL ==========
if items_data and any(len(data.get('items', [])) > 0 for data in items_data.values()) and total_general > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Guardar e Imprimir Presupuesto", type="primary", use_container_width=True):
        if not cliente_id or not lugar_trabajo_id:
            st.error("❌ Debe seleccionar un cliente y lugar de trabajo")
            st.stop()

        with st.spinner("Guardando presupuesto..."):
            try:
                presupuesto_id = save_presupuesto_completo(
                    user_id=user_id, cliente_id=cliente_id,
                    lugar_trabajo_id=lugar_trabajo_id, descripcion=descripcion,
                    items_data=items_data, total=total_general
                )

                if presupuesto_id:
                    st.toast(f"✅ Presupuesto #{presupuesto_id} guardado!")
                    pdf_path = generar_pdf(
                        cliente_nombre=cliente_nombre, lugar_cliente=lugar_nombre,       
                        categorias=items_data, descripcion=descripcion
                    )

                    if open(pdf_path, "rb"):
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        os.unlink(pdf_path)

                    autosave_manager.clear_draft()

                    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                    col_action1, col_action2, col_action3 = st.columns(3)

                    with col_action1:
                        pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(presupuesto_id)
                        if success and pdf_bytes:
                            st.download_button(
                                label="⬇️ Descargar Presupuesto PDF", data=pdf_bytes,
                                file_name=file_name, mime="application/pdf", use_container_width=True
                            )
                    with col_action2:
                        if st.button("🔄 Crear otro presupuesto", use_container_width=True):
                            for key in ['categorias', 'descripcion', 'items_data']:
                                if key in st.session_state: del st.session_state[key]
                            st.rerun()
                    with col_action3:
                        st.page_link("pages/2_🕒_historial.py", label="📋 Ver Historial Completo", use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")