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
# IMPORTAR LAS FUNCIONES DE AUTOSAVE
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
        # Verificar que data tenga la estructura esperada
        if not isinstance(data, dict):
            continue
            
        # Sumar items (usando safe_numeric_value)
        items = data.get('items', [])
        if isinstance(items, list):
            total += sum(safe_numeric_value(item.get('total', 0)) for item in items)
        total += safe_numeric_value(data.get('mano_obra', 0))
    return total

st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")
is_logged_in = check_login()

if not is_logged_in:
    st.error("❌ Acceso denegado. Por favor, inicia sesión en la página principal.")
    st.switch_page("App_principal.py")
    st.stop()

with st.sidebar:
    st.markdown("**👤 Usuario:**")
    st.markdown(f"`{st.session_state.usuario}`")

    if st.button("🚪 Cerrar Sesión", type="primary", width='stretch'):
        sign_out()
        st.toast("Sesión cerrada correctamente", icon="🌱")
        st.rerun()

# --- INICIALIZAR AUTOSAVE ---
user_id = st.session_state.get('user_id')
autosave_manager = AutoSaveManager(user_id, "draft_presupuesto_principal")

# --- VERIFICAR BORRADOR AL INICIAR ---
if autosave_manager.has_draft() and 'categorias' not in st.session_state:
    draft = autosave_manager.load_draft()
    if draft:
        draft_age = autosave_manager.get_draft_age()
        
        st.warning(f"📝 Se encontró un borrador guardado {draft_age}")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔄 Cargar Borrador", use_container_width=True, key="load_draft_main"):
                restore_draft_state(draft)
                st.rerun()
        with col2:
            if st.button("👀 Ver Vista Previa", use_container_width=True, key="preview_draft_main"):
                with st.expander("Vista previa del borrador", expanded=True):
                    st.json(draft)
        with col3:
            if st.button("🗑️ Descartar", use_container_width=True, key="discard_draft_main"):
                autosave_manager.clear_draft()
                st.rerun()

# --- FUNCIÓN DE AUTOGUARDADO ---
def autosave_with_debounce():
    """Autoguardado con control de frecuencia"""
    current_time = time.time()
    last_save = getattr(st.session_state, '_last_autosave_main', 0)
    
    # Guardar máximo cada 30 segundos
    if current_time - last_save > 30:
        current_state = capture_current_state()
        if autosave_manager.save_draft(current_state):
            st.session_state._last_autosave_main = current_time
            st.toast("💾 Guardado automáticamente", icon="💾")

# --- CONTENIDO PROTEGIDO (SOLO SI EL USUARIO ESTÁ LOGUEADO) ---
st.header("📑 Generador de Presupuestos", divider="blue")

# === BOTÓN PARA LIMPIAR TODO ===
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🧹 Limpiar / Nuevo presupuesto", type="secondary", use_container_width=True):
        keys_to_delete = [
            "categorias",
            "descripcion", 
            "items_data",
            "cliente_id",
            "cliente_nombre",
            "lugar_trabajo_id",
            "lugar_nombre",
            "trabajos_simples",
            "total_general"
        ]

        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]

        # Limpiar también el borrador
        autosave_manager.clear_draft()
        st.rerun()

with col2:
    # Panel de control de autoguardado
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

# Obtener user_id para usar en los componentes
user_id = st.session_state.get('user_id')

# ========== SECCIÓN CLIENTE, LUGAR y TRABAJO A REALIZAR ==========
cliente_id, cliente_nombre, lugar_trabajo_id, lugar_nombre, descripcion = show_cliente_lugar_selector(user_id)

# Autoguardado cuando cambian cliente/lugar/descripción
if any([cliente_id != st.session_state.get('cliente_id'),
        lugar_trabajo_id != st.session_state.get('lugar_trabajo_id'), 
        descripcion != st.session_state.get('descripcion')]):
    autosave_with_debounce()

# Actualizar session state
st.session_state['cliente_id'] = cliente_id
st.session_state['lugar_trabajo_id'] = lugar_trabajo_id  
st.session_state['descripcion'] = descripcion

# ========== SECCIÓN PRINCIPAL CON COLUMNAS ==========
col1, col2, col3 = st.columns([8,0.5,12])

with col1:
    st.subheader("📦 Items del Presupuesto", divider="blue")
    items_data = show_items_presupuesto(user_id)
    
    # Autoguardado después de agregar/modificar items
    if st.session_state.get('_items_modified', False):
        autosave_with_debounce()
        st.session_state['_items_modified'] = False

    # ========== SECCIÓN MANO DE OBRA ===============
    st.markdown(" ")
    st.markdown("#### 🛠️Añadir trabajo")
    show_trabajos_simples(items_data)

with col2:
    st.text(" ")

with col3:
    st.subheader("📊 Resumen del Presupuesto", divider="blue")
    total_general = show_resumen(items_data)

# ========== SECCIÓN EDICIÓN DE ITEMS ===========
# Solo mostrar edición si hay items
if items_data and any(len(data.get('items', [])) > 0 for data in items_data.values()):
    st.subheader("✏️ Editar Items", divider="blue")
    items_data = show_edited_presupuesto(user_id)
    
    # Autoguardado después de edición avanzada
    if st.session_state.get('_items_modified', False):
        autosave_with_debounce()
        st.session_state['_items_modified'] = False

# ========== GUARDADO ==========
# Solo mostrar botón de guardar si hay items y total > 0
if items_data and any(len(data.get('items', [])) > 0 for data in items_data.values()) and total_general > 0:
    if st.button("💾 Guardar Presupuesto", type="primary", width='stretch',
                help="Revise todos los datos antes de guardar"):
        
        # Validaciones finales
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

                    # CORRECCIÓN: Generar PDF con parámetros correctos
                    pdf_path = generar_pdf(
                        cliente_nombre=cliente_nombre,    
                        lugar_cliente=lugar_nombre,       
                        categorias=items_data,
                        descripcion=descripcion
                    )

                    # Validar PDF
                    if not pdf_path or not os.path.exists(pdf_path):
                        st.error("❌ Error generando PDF: archivo no creado.")
                        st.stop()

                    st.toast("🎉 Presupuesto guardado correctamente. ¿Qué deseas hacer ahora?")

                    # Botón de descarga PDF
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    # Limpiar archivo temporal
                    try:
                        os.unlink(pdf_path)
                    except Exception:
                        pass

                    # LIMPIAR BORRADOR DESPUÉS DE GUARDADO EXITOSO
                    autosave_manager.clear_draft()

                    # Mostrar opciones
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
                            # Limpiar session state
                            for key in ['categorias', 'descripcion']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            # Limpiar borrador
                            autosave_manager.clear_draft()
                            st.rerun()
                    
                    with col3:
                        st.page_link("pages/2_🕒_historial.py", label="📋 Ver Historial", use_container_width=True)

                else:
                    st.error("❌ Error al crear el presupuesto en la base de datos")

            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")
                st.exception(e)