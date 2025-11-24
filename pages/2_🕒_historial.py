import time
import streamlit as st
from utils.auth import check_login, sign_out
from datetime import datetime, timedelta
from utils.db import (
    get_supabase_client, get_clientes, get_lugares_trabajo, 
    get_presupuestos_usuario, delete_presupuesto,
    _show_presupuesto_detail
)
from utils.components import safe_numeric_value

from utils.pdf import mostrar_boton_descarga_pdf

st.markdown("""
<style>
.stTextInput, .stNumberInput, .stSelectbox, .stButton {
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


# -----------------------------------------------------------
# 1. SEGURIDAD Y CONFIGURACIÓN
# -----------------------------------------------------------
st.set_page_config(page_title="Historial", page_icon="🌱", layout="wide")
st.header("🕒 Historial de Presupuestos")

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

# -----------------------------------------------------------
# CONTENIDO DE HISTORIAL
# -----------------------------------------------------------

user_id = st.session_state.user_id 
supabase = get_supabase_client()

# -----------------------------------------------------------
# 2. FILTROS
# -----------------------------------------------------------
with st.expander("🔍 Filtros", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    try:
        # Obtener clientes y lugares filtrados por el usuario
        clientes = get_clientes(user_id) 
        lugares = get_lugares_trabajo(user_id)
        
        # Mapeo para facilitar la búsqueda de ID a partir del nombre en el selectbox
        clientes_map = {id: nombre for id, nombre in clientes}
        lugares_map = {id: nombre for id, nombre in lugares}
        
        # --- Filtro Cliente ---
        with col1:
            cliente_filtro_nombre = st.selectbox(
                "Filtrar por cliente:",
                options=["Todos los clientes"] + list(clientes_map.values()),
            )
            # Obtiene el ID del cliente o None si es "Todos los clientes"
            cliente_filtro_id = next((id for id, nombre in clientes_map.items() if nombre == cliente_filtro_nombre), None)
        
        # --- Filtro Lugar ---
        with col2:
            lugar_filtro_nombre = st.selectbox(
                "Filtrar por lugar:",
                options=["Todos los lugares"] + list(lugares_map.values()),
            )
            # Obtiene el ID del lugar o None si es "Todos los lugares"
            lugar_filtro_id = next((id for id, nombre in lugares_map.items() if nombre == lugar_filtro_nombre), None)
        
        # --- Filtro Fecha ---
        with col3:
            fecha_filtro = st.selectbox(
                "Filtrar por fecha:",
                options=["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Todos"],
                index=3
            )
            
    except Exception as e:
        st.error(f"Error al cargar filtros: {str(e)}")
        st.stop()
        
# -----------------------------------------------------------
# 3. APLICAR FILTROS Y OBTENER PRESUPUESTOS
# -----------------------------------------------------------
filtros = {}
if cliente_filtro_id:
    filtros['cliente_id'] = cliente_filtro_id
if lugar_filtro_id:
    filtros['lugar_trabajo_id'] = lugar_filtro_id

fecha_inicio = None
if fecha_filtro == "Últimos 7 días":
    fecha_inicio = datetime.now() - timedelta(days=7)
elif fecha_filtro == "Últimos 30 días":
    fecha_inicio = datetime.now() - timedelta(days=30)
elif fecha_filtro == "Últimos 90 días":
    fecha_inicio = datetime.now() - timedelta(days=90)
    
if fecha_inicio:
    filtros['fecha_inicio'] = fecha_inicio

try:
    with st.spinner("🔄 Cargando presupuestos..."):
        presupuestos = get_presupuestos_usuario(user_id, filtros) 
        
except Exception as e:
    st.error(f"❌ Error al obtener presupuestos: {str(e)}")
    with st.expander("🔧 Diagnóstico detallado del error"):
        st.exception(e)
    st.stop()

if not presupuestos:
    st.info("🔍 No se encontraron presupuestos con los filtros seleccionados.")
    if st.button("📋 Crear mi primer presupuesto"):
        # Asegúrate de que el nombre del archivo de la página de creación sea el correcto
        st.switch_page("App_principal.py") 
    st.stop()

# -----------------------------------------------------------
# 4. MOSTRAR PRESUPUESTOS (Métricas y Lista)
# -----------------------------------------------------------

# Resumen estadístico
suma_total = sum(safe_numeric_value(p.get('total', 0)) for p in presupuestos)
total_presupuestos = len(presupuestos)
avg_total = suma_total / total_presupuestos if total_presupuestos else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Presupuestos", f"{total_presupuestos}")
with col2:
    st.metric("Suma Total", f"${suma_total:,.0f}")
with col3:
    st.metric("Promedio", f"${avg_total:,.0f}")

st.subheader("📋 Lista de Presupuestos")

# Encabezado tipo tabla
with st.container():
    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 3])
    col1.markdown("**Cliente**")
    col2.markdown("**Lugar**")
    col3.markdown("**Fecha**")
    col4.markdown("**Total**")
    col5.markdown("**Ítems**")
    col6.markdown("**Acciones**")

# Filas tipo tabla
for i, p in enumerate(presupuestos):
    
    total_display = safe_numeric_value(p.get('total', 0))
    
    with st.container(border=True):
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 3])

        # --- Datos de la Fila ---
        cliente_nombre = p.get('cliente', {}).get('nombre', 'N/A')
        col1.write(cliente_nombre.title() if cliente_nombre else 'N/A')
            
        lugar_nombre = p.get('lugar', {}).get('nombre', 'N/A')
        col2.write(lugar_nombre.title() if lugar_nombre else 'N/A')
            
        fecha_str = p.get('fecha_creacion', datetime.now().isoformat())
        try:
            fecha_dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')) # Manejo de formato ISO
            col3.write(fecha_dt.strftime('%Y-%m-%d'))
        except Exception:
            col3.write(fecha_str.split('T')[0] if 'T' in fecha_str else fecha_str)
            
        col4.write(f"**${total_display:,.2f}**")
        col5.write(str(p.get('num_items', 0)))

        # --- Botones de Acción ---
        with col6:
            b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
            
            state_key = f"expander_toggle_{p['id']}"
            if state_key not in st.session_state:
                st.session_state[state_key] = False

            with b1: # BOTÓN EDITAR
                if st.button("✏️ Editar", key=f"edit_{p['id']}", help="Editar este presupuesto", use_container_width=True):
                    st.session_state['presupuesto_a_editar_id'] = p['id'] 
                    st.session_state['presupuesto_cargado_automaticamente'] = False  # Resetear para carga fresca
                    st.success(f"🔄 Redirigiendo para editar presupuesto ID: {p['id']}")
                    time.sleep(1)  # Pequeña pausa para que se vea el mensaje
                    st.switch_page("pages/_✏️ Editar.py")
            
            with b2: # BOTÓN DESCARGA (Placeholder)
                pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(p['id'])
                if success and pdf_bytes:
                    st.download_button(
                        label="⬇️",
                        data=pdf_bytes,
                        file_name=file_name,
                        mime="application/pdf",
                        key=f"down_{p['id']}",
                        help="Descargar PDF"
                    )
                else:
                    st.button("🚫", key=f"down_{p['id']}_disabled", disabled=True, help="PDF no disponible")
            
            with b3: # BOTÓN VISTA PREVIA (Toggle del expander)
                if st.button("👁️", key=f"view_{p['id']}", help="Ver Presupuesto"):
                    st.session_state[state_key] = not st.session_state[state_key]
                    st.rerun()

            with b4: # BOTÓN ELIMINAR
                if st.button("🗑️", key=f"del_{p['id']}", type="secondary", help="Eliminar"):
                    if delete_presupuesto(p['id'], user_id):
                        st.success("Presupuesto eliminado correctamente")
                        st.rerun()
                    else:
                        st.error("No se pudo eliminar el presupuesto.")
        
        # --- Detalle del Presupuesto ---
        if st.session_state.get(state_key, False):
            with st.expander(f"Detalle Presupuesto ID: {p['id']}", expanded=True):
                _show_presupuesto_detail(presupuesto_id=p['id'])