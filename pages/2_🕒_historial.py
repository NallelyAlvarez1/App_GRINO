import time
import streamlit as st
from utils.auth import check_login, sign_out
from datetime import datetime, timedelta
from utils.db import (
    get_supabase_client, get_clientes, get_lugares_trabajo, 
    get_presupuestos_usuario, delete_presupuesto,
    _show_presupuesto_detail,
    get_estados_cuenta_usuario,  
    delete_estado_cuenta
)
from utils.components import safe_numeric_value
from utils.pdf import mostrar_boton_descarga_pdf

try:
    from utils.pdf import mostrar_boton_descarga_estado_cuenta
except ImportError:
    def mostrar_boton_descarga_estado_cuenta(id): return None, "", False

# -----------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA (Debe ser lo primero)
# -----------------------------------------------------------
st.set_page_config(page_title="Historial", page_icon="🌱", layout="wide")

# -----------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS (Estilo Dashboard Moderno)
# -----------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Configuración de fuentes globales */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Títulos limpios */
    h1, h2, h3 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }

    /* --- DISEÑO DE FILAS (TABLA MODERNA) --- */
    div[data-inner-background="true"] {
        padding: 0.8rem 1rem !important;
    }
    
    /* Contenedor de filas con bordes redondeados y efecto sutil */
    div[data-testid="element-container"] + div:has(div[data-inner-background="true"]) {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        margin-bottom: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    div[data-testid="element-container"] + div:has(div[data-inner-background="true"]):hover {
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03) !important;
        border-color: #cbd5e1 !important;
    }

    /* Cabeceras de las columnas */
    .table-header {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 700;
        padding: 10px 0;
    }

    /* --- ELEMENTOS DE TEXTO INTERNOS --- */
    .client-title {
        font-weight: 600;
        color: #0f172a;
        font-size: 0.95rem;
        margin-bottom: 2px;
    }
    
    /* Subetiqueta de versión abajo del nombre */
    .version-tag {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 4px;
    }
    
    .version-tag-empty {
        display: inline-block;
        background-color: #f1f5f9;
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 1px 6px;
        border-radius: 4px;
    }

    /* Badges para los estados de cuenta */
    .status-badge-paid {
        background-color: #dcfce7;
        color: #166534;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 6px;
        border: 1px solid #bbf7d0;
    }
    
    .status-badge-pending {
        background-color: #fee2e2;
        color: #991b1b;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 6px;
        border: 1px solid #fecaca;
    }

    /* Ajuste estético de los botones de acción */
    .stButton > button {
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

st.header("🕒 Historial General de Documentos")

is_logged_in = check_login()

if not is_logged_in:
    st.error("🔒 No has iniciado sesión. Serás redirigido al inicio en 5 segundos...")
    progress_bar = st.progress(0)
    for percent_complete in range(100):
        time.sleep(0.05)
        progress_bar.progress(percent_complete + 1)
    st.switch_page("App_principal.py")
    st.stop()

with st.sidebar:
    st.markdown("**👤 Usuario:**")
    st.markdown(f"`{st.session_state.usuario}`")

    if st.button("🚪 Cerrar Sesión", type="primary", width='stretch'):
        sign_out()
        st.toast("Sesión cerrada correctamente", icon="🌱")
        st.rerun()

user_id = st.session_state.user_id 
supabase = get_supabase_client()

# -----------------------------------------------------------
# 2. FILTROS REPRESENTADOS COMO RECUADROS DE COLORES SUPERIORES
# -----------------------------------------------------------
try:
    clientes = get_clientes(user_id) 
    lugares = get_lugares_trabajo(user_id)
    
    clientes_map = {id: nombre for id, nombre in clientes}
    lugares_map = {id: nombre for id, nombre in lugares}
    
    # Renderizamos los selectores embebidos dentro de cajas HTML con colores pastel personalizados
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        cliente_filtro_nombre = st.selectbox(
            "👤 Filtrar por cliente:",
            options=["Todos los clientes"] + list(clientes_map.values()),
        )
        cliente_filtro_id = next((id for id, nombre in clientes_map.items() if nombre == cliente_filtro_nombre), None)

    with col_f2:
        lugar_filtro_nombre = st.selectbox(
            "📍 Filtrar por lugar:",
            options=["Todos los lugares"] + list(lugares_map.values()),
        )
        lugar_filtro_id = next((id for id, nombre in lugares_map.items() if nombre == lugar_filtro_nombre), None)
  
    with col_f3:
        fecha_filtro = st.selectbox(
            "📅 Filtrar por fecha de emisión:",
            options=["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Todos"],
            index=3
        )
        
except Exception as e:
    st.error(f"Error al cargar filtros: {str(e)}")
    st.stop()

# Estructurar parámetros de filtros
filtros = {}
if cliente_filtro_id:
    filtros['cliente_id'] = cliente_filtro_id
if lugar_filtro_id:
    filtros['lugar_trabajo_id'] = lugar_filtro_id

fecha_inicio = None
if fecha_filtro == "Últimos 7 días":
    fecha_inicio = datetime.now() - timedelta(days=7)
elif fecha_filtro == "Últimos 30 días":
    datetime.now() - timedelta(days=30)
elif fecha_filtro == "Últimos 90 días":
    fecha_inicio = datetime.now() - timedelta(days=90)
    
if fecha_inicio:
    filtros['fecha_inicio'] = fecha_inicio

st.write("##") # Margen de separación limpio

# -----------------------------------------------------------
# 3. SECCIONES EN PESTAÑAS (Páginas de separación: Presupuestos vs Estados de Cuenta)
# -----------------------------------------------------------
tab_presupuestos, tab_estados_cuenta = st.tabs(["📋 Lista de Presupuestos", "📄 Estados de Cuenta"])

# =========================================================================
# PESTAÑA A: PRESUPUESTOS
# =========================================================================
with tab_presupuestos:
    try:
        presupuestos = get_presupuestos_usuario(user_id, filtros) 
    except Exception as e:
        st.error(f"❌ Error al obtener presupuestos: {str(e)}")
        presupuestos = []

    if not presupuestos:
        st.info("🔍 No se encontraron presupuestos con los filtros seleccionados.")
    else:
        # Encabezados limpios de tabla
        with st.container():
            col1, col2, col3, col5, col6, col7, col8 = st.columns([2.5, 2.3, 2.5, 1.8, 1.8, 1, 3.2])
            col1.markdown('<div class="table-header">Cliente</div>', unsafe_allow_html=True)
            col2.markdown('<div class="table-header">Lugar</div>', unsafe_allow_html=True)
            col3.markdown('<div class="table-header">Descripción</div>', unsafe_allow_html=True)
            col5.markdown('<div class="table-header">Fecha</div>', unsafe_allow_html=True)
            col6.markdown('<div class="table-header">Total</div>', unsafe_allow_html=True)
            col7.markdown('<div class="table-header">Ítems</div>', unsafe_allow_html=True)
            col8.markdown('<div class="table-header" style="text-align: center;">Acciones</div>', unsafe_allow_html=True)

        for p in presupuestos:
            with st.container(border=True):
                col1, col2, col3, col5, col6, col7, col8 = st.columns([2.5, 2.3, 2.5, 1.8, 1.8, 1, 3.2])
            
                total_display = safe_numeric_value(p.get('total', 0))
                notas = p.get('notas', '')

                # Mostrar Cliente y su versión abajo sin foto
                nombre_cliente = p.get('cliente', {}).get('nombre', 'N/A').title()
                badge_version = f'<span class="version-tag">{notas}</span>' if notas else '<span class="version-tag-empty">V1</span>'
                col1.markdown(f'<div class="client-title">{nombre_cliente}</div>{badge_version}', unsafe_allow_html=True)
                
                col2.write(p.get('lugar', {}).get('nombre', 'N/A').title())
                
                descripcion = p.get('descripcion', 'Sin descripción')
                col3.write(descripcion[:30] + "..." if len(descripcion) > 30 else descripcion)

                fecha_str = p.get('fecha_creacion', datetime.now().isoformat())
                col5.write(fecha_str.split('T')[0] if 'T' in fecha_str else fecha_str)
                    
                col6.write(f"**${total_display:,.0f}**")
                col7.write(str(p.get('num_items', 0)))

                with col8:
                    b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                    with b1:
                        if st.button("✏️", key=f"edit_{p['id']}", help="Editar", use_container_width=True):
                            st.session_state['presupuesto_a_editar_id'] = p['id'] 
                            st.session_state['presupuesto_cargado_automaticamente'] = False
                            st.switch_page("pages/_✏️ Editar.py")
                    with b2:
                        pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(p['id'])
                        if success and pdf_bytes:
                            st.download_button(label="⬇️", data=pdf_bytes, file_name=file_name, mime="application/pdf", key=f"down_{p['id']}", use_container_width=True)
                        else:
                            st.button("🚫", key=f"down_dis_{p['id']}", disabled=True, use_container_width=True)
                    with b3:
                        with st.popover("👁️", use_container_width=True):
                            _show_presupuesto_detail(presupuesto_id=p['id'])
                    with b4:
                        if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar", use_container_width=True):
                            if delete_presupuesto(p['id'], user_id):
                                st.rerun()

# =========================================================================
# PESTAÑA B: ESTADOS DE CUENTA
# =========================================================================
with tab_estados_cuenta:
    try:
        from utils.db import toggle_estado_pago_ec
        estados_cuenta = get_estados_cuenta_usuario(user_id, filtros)
    except Exception as e:
        st.error(f"❌ Error al obtener estados de cuenta: {str(e)}")
        estados_cuenta = []

    if not estados_cuenta:
        st.info("🔍 No se encontraron estados de cuenta con los filtros seleccionados.")
    else:
        with st.container():
            col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([2.5, 2, 1.4, 1.4, 1.4, 1.4, 1.5, 3])
            col_cli.markdown('<div class="table-header">Cliente</div>', unsafe_allow_html=True)
            col_lug.markdown('<div class="table-header">Lugar de Trabajo</div>', unsafe_allow_html=True)
            col_fec.markdown('<div class="table-header">Fecha Emisión</div>', unsafe_allow_html=True)
            col_sub.markdown('<div class="table-header">Monto Base</div>', unsafe_allow_html=True)
            col_abo.markdown('<div class="table-header">Abonos</div>', unsafe_allow_html=True)
            col_net.markdown('<div class="table-header">Total Neto</div>', unsafe_allow_html=True)
            col_est.markdown('<div class="table-header" style="text-align: center;">Estado</div>', unsafe_allow_html=True)
            col_acc.markdown('<div class="table-header" style="text-align: center;">Acciones</div>', unsafe_allow_html=True)

        for ec in estados_cuenta:
            with st.container(border=True):
                col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([2.5, 2, 1.4, 1.4, 1.4, 1.4, 1.5, 3])
                
                cli_nom = ec.get('cliente', {}).get('nombre', 'N/A') if ec.get('cliente') else 'N/A'
                lug_nom = ec.get('lugar_trabajo', {}).get('nombre', 'N/A') if ec.get('lugar_trabajo') else 'N/A'
                
                # Cliente sin foto en Estados de Cuenta
                col_cli.markdown(f'<div class="client-title">{cli_nom.title()}</div>', unsafe_allow_html=True)
                col_lug.write(lug_nom.title())
                
                fec_emision = ec.get('fecha_emision', datetime.now().isoformat())
                col_fec.write(fec_emision.split('T')[0] if 'T' in fec_emision else fec_emision)
                
                col_sub.write(f"${safe_numeric_value(ec.get('monto_base', 0)):,.0f}")
                col_abo.write(f"-${safe_numeric_value(ec.get('abono_monto', 0)):,.0f}")
                col_net.write(f"**${safe_numeric_value(ec.get('total_neto', 0)):,.0f}**")
                
                # Renderizado de Badge Estilizado
                es_pagado = ec.get('pagado', False)
                if es_pagado:
                    col_est.markdown('<div style="text-align: center; margin-top: 5px;"><span class="status-badge-paid">PAGADO</span></div>', unsafe_allow_html=True)
                else:
                    col_est.markdown('<div style="text-align: center; margin-top: 5px;"><span class="status-badge-pending">PENDIENTE</span></div>', unsafe_allow_html=True)

                with col_acc:
                    ba1, ba2, ba3, ba4 = st.columns([1, 1, 1, 1])
                    
                    with ba1:
                        pdf_b, f_name, ok = mostrar_boton_descarga_estado_cuenta(ec['id'])
                        if ok and pdf_b:
                            st.download_button(label="⬇️", data=pdf_b, file_name=f_name, mime="application/pdf", key=f"down_ec_{ec['id']}", use_container_width=True)
                        else:
                            st.button("🚫", key=f"down_dis_ec_{ec['id']}", disabled=True, use_container_width=True)
                    
                    with ba2:
                        with st.popover("👁️", use_container_width=True):
                            st.write(f"**Documento N°:** {ec['id']:04d}")
                            st.info("Detalles adicionales.")

                    with ba3:
                        icono_pago = "💵" if not es_pagado else "🔄"
                        if st.button(icono_pago, key=f"pay_ec_{ec['id']}", use_container_width=True):
                            if toggle_estado_pago_ec(ec['id'], not es_pagado):
                                st.cache_data.clear()  
                                st.toast(f"Estado N°{ec['id']} actualizado", icon="🌱")
                                time.sleep(0.4)
                                st.rerun()

                    with ba4:
                        if st.button("🗑️", key=f"del_ec_{ec['id']}", use_container_width=True):
                            if delete_estado_cuenta(ec['id'], user_id):
                                st.cache_data.clear()  
                                st.rerun()