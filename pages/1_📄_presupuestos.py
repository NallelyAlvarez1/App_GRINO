from typing import Any, Dict
import streamlit as st
import os
import time
import uuid
from utils.pdf import generar_pdf
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

st.markdown("""
<style>
.stTextInput, .stNumberInput, .stSelectbox, .stButton, .stTextArea{
    margin-bottom: -0.3rem;
    margin-top: -0.4rem;
            
/* Reducir espacio en subheaders */
h2, h3, h4 {
    margin-top: 0.4rem !important;
    margin-bottom: 0.4rem !important;
    padding-top: 0.4rem !important;
    padding-bottom: 0.4rem !important;
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

st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")

# VERIFICAR LOGIN PRIMERO
is_logged_in = check_login()

# SIEMPRE crear persistent session ID
if 'persistent_session_id' not in st.session_state:
    st.session_state['persistent_session_id'] = str(uuid.uuid4())

# Obtener user_id (puede ser None)
user_id = st.session_state.get('user_id')

# Crear manager SIEMPRE (incluso sin login)
autosave_manager = AutoSaveManager(user_id, "draft_presupuesto_principal")

# --- VERIFICAR BORRADOR (INCLUSO SIN LOGIN) ---
if autosave_manager.has_draft() and not st.session_state.get('draft_restored', False):
    draft = autosave_manager.load_draft()
    if draft:
        draft_age = autosave_manager.get_draft_age()
        
        # Usar un container para el mensaje que no desaparezca
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

# AHORA VERIFICAR ACCESO
if not is_logged_in:
    st.error("❌ Acceso denegado. Por favor, inicia sesión en la página principal.")
    st.info("💡 El borrador se ha guardado y estará disponible cuando inicies sesión.")
    if st.button("🔐 Ir a inicio de sesión"):
        st.switch_page("App_principal.py")
    st.stop()

# CONTINUAR CON LA APP (USUARIO LOGUEADO)
with st.sidebar:
    st.markdown("**👤 Usuario:**")
    st.markdown(f"`{st.session_state.usuario}`")
    
    # Botón de debug opcional
    with st.expander("🔧 Debug", expanded=False):
        if st.button("📊 Ver Estado Actual"):
            st.write("Session State:", {
                k: v for k, v in st.session_state.items() 
                if not k.startswith('_') and k not in ['usuario', 'user_id']
            })
        
        if st.button("📁 Ver Borrador Guardado"):
            draft = autosave_manager.load_draft()
            st.json(draft if draft else "No hay borrador")
    
    if st.button("🚪 Cerrar Sesión", type="primary", width='stretch'):
        sign_out()
        st.toast("Sesión cerrada correctamente", icon="🌱")
        st.rerun()

# Si se restauró un borrador, asegurar estructura de datos
if st.session_state.get('draft_restored', False):
    if 'items_data' in st.session_state:
        items_data = st.session_state['items_data']
        for cat_name, cat_data in items_data.items():
            if isinstance(cat_data, dict):
                if 'items' not in cat_data:
                    cat_data['items'] = []
                if 'mano_obra' not in cat_data:
                    cat_data['mano_obra'] = 0
    # Limpiar flag después de procesar
    # st.session_state['draft_restored'] = False  # Comentado para mantener el flag

# --- FUNCIÓN DE AUTOGUARDADO ---
def autosave_with_debounce():
    """Autoguardado con control de frecuencia"""
    current_time = time.time()
    last_save = getattr(st.session_state, '_last_autosave_main', 0)
    
    if current_time - last_save > 30:
        current_state = capture_current_state()
        if autosave_manager.save_draft(current_state):
            st.session_state._last_autosave_main = current_time
            st.toast("💾 Guardado automáticamente", icon="💾")

# --- CONTENIDO PROTEGIDO ---
st.header("📑 Generador de Presupuestos", divider="blue")

# === BOTÓN PARA LIMPIAR TODO ===
col1, col2 = st.columns([1, 1])
with col1:
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

with col2:
    if autosave_manager.has_draft():
        draft_age = autosave_manager.get_draft_age()
        st.caption(f"💾 Último guardado: {draft_age}")
        
        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("💾 Guardar", key="manual_save_main", use_container_width=True):
                current_state = capture_current_state()
                if autosave_manager.save_draft(current_state):
                    st.toast("✅ Borrador guardado manualmente")
        with col_clear:
            if st.button("🗑️ Limpiar", key="clear_draft_main", use_container_width=True):
                autosave_manager.clear_draft()
                st.rerun()
    else:
        st.caption("💾 No hay borradores guardados")

# ========== SECCIÓN CLIENTE, LUGAR y TRABAJO ==========
# Siempre mostrar el selector completo (como funcionaba antes)
cliente_id, cliente_nombre, lugar_trabajo_id, lugar_nombre, descripcion = show_cliente_lugar_selector(user_id)

# Guardar en session_state
st.session_state['cliente_id'] = cliente_id
st.session_state['cliente_nombre'] = cliente_nombre
st.session_state['lugar_trabajo_id'] = lugar_trabajo_id
st.session_state['lugar_nombre'] = lugar_nombre
st.session_state['descripcion'] = descripcion

# Verificar cambios y autoguardar
if any([
    cliente_id != st.session_state.get('_last_cliente_id'),
    lugar_trabajo_id != st.session_state.get('_last_lugar_id'),
    descripcion != st.session_state.get('_last_desc')
]):
    autosave_with_debounce()

st.session_state['_last_cliente_id'] = cliente_id
st.session_state['_last_lugar_id'] = lugar_trabajo_id
st.session_state['_last_desc'] = descripcion

# ========== SECCIÓN PRINCIPAL ==========
col1, col2, col3 = st.columns([8,0.5,12])

with col1:
    st.subheader("📦 Items del Presupuesto", divider="blue")
    
    # Pasar initial_data si existe
    initial_items = st.session_state.get('items_data', None)
    items_data = show_items_presupuesto(user_id, initial_data=initial_items)
    
    if items_data:
        st.session_state['items_data'] = items_data
    
    if st.session_state.get('_items_modified', False):
        autosave_with_debounce()
        st.session_state['_items_modified'] = False

    st.markdown(" ")
    st.markdown("#### 🛠️Añadir trabajo")
    show_trabajos_simples(items_data)

with col2:
    st.text(" ")

with col3:
    st.subheader("📊 Resumen del Presupuesto", divider="blue")
    total_general = show_resumen(items_data)

# ========== SECCIÓN EDICIÓN ===========
if items_data and any(len(data.get('items', [])) > 0 for data in items_data.values()):
    st.subheader("✏️ Editar Items", divider="blue")
    items_data = show_edited_presupuesto(user_id)
    
    if items_data:
        st.session_state['items_data'] = items_data
    
    if st.session_state.get('_items_modified', False):
        autosave_with_debounce()
        st.session_state['_items_modified'] = False

# ========== GUARDADO ==========
if items_data and any(len(data.get('items', [])) > 0 for data in items_data.values()) and total_general > 0:
    if st.button("💾 Guardar Presupuesto", type="primary", width='stretch'):
        
        if not cliente_id or not lugar_trabajo_id:
            st.error("❌ Debe seleccionar un cliente y lugar de trabajo")
            st.stop()
            
        if total_general <= 0:
            st.error("❌ El total del presupuesto debe ser mayor a cero")
            st.stop()

        with st.spinner("Guardando presupuesto..."):
            try:
                presupuesto_id = save_presupuesto_completo(
                    user_id=user_id,
                    cliente_id=cliente_id,
                    lugar_trabajo_id=lugar_trabajo_id,
                    descripcion=descripcion,
                    items_data=items_data,
                    total=total_general
                )

                if presupuesto_id:
                    st.toast(f"✅ Presupuesto #{presupuesto_id} guardado!", icon="✅")
                    
                    pdf_path = generar_pdf(
                        cliente_nombre=cliente_nombre,    
                        lugar_cliente=lugar_nombre,       
                        categorias=items_data,
                        descripcion=descripcion
                    )

                    if not pdf_path or not os.path.exists(pdf_path):
                        st.error("❌ Error generando PDF: archivo no creado.")
                        st.stop()

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    try:
                        os.unlink(pdf_path)
                    except Exception:
                        pass

                    autosave_manager.clear_draft()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            "📄 Descargar PDF",
                            pdf_bytes,
                            file_name=f"presupuesto_{presupuesto_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with col2:
                        if st.button("🔄 Crear otro presupuesto", use_container_width=True):
                            for key in ['categorias', 'descripcion', 'items_data']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            autosave_manager.clear_draft()
                            st.rerun()
                    with col3:
                        st.page_link("pages/2_🕒_historial.py", label="📋 Ver Historial", use_container_width=True)

                else:
                    st.error("❌ Error al crear el presupuesto en la base de datos")

            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")
                st.exception(e)