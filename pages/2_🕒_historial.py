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
# ESTILOS CSS AVANZADOS Y MODERNOS
# -----------------------------------------------------------
st.markdown("""
<style>
    /* Importar tipografía moderna opcional si deseas */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Reducción global de espaciados de inputs */
    .stTextInput, .stNumberInput, .stSelectbox, .stButton {
        margin-bottom: -0.1rem;
        margin-top: -0.1rem;
    }
    
    /* Encabezados limpios */
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #2E4031 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }                
    
    /* Estilizar contenedores de métricas */
    div[data-testid="stMetricBlock"] {
        background-color: #f8faf9;
        border: 1px solid #eef2f0;
        border-radius: 12px;
        padding: 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* --- EFECTO TARJETA MODERNA --- */
    /* Targetea los st.container(border=True) */
    div[data-testid="element-container"] + div:has(div[data-inner-background="true"]) {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        transition: all 0.25s ease-in-out !important;
        background-color: #ffffff !important;
    }
    
    /* Efecto Hover interactivo para las filas */
    div[data-testid="element-container"] + div:has(div[data-inner-background="true"]):hover {
        border-color: #cbd5e1 !important;
        box-shadow: 0 4px 12px rgba(148, 163, 184, 0.08) !important;
        transform: translateY(-1px);
    }
    
    /* Encabezados de tabla en negrita limpia */
    .table-header {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        padding-bottom: 0.5rem;
    }
    
    /* Badges de Estado del Pago */
    .badge-pagado {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        text-align: center;
        border: 1px solid #bbf7d0;
    }
    
    .badge-pendiente {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        text-align: center;
        border: 1px solid #fecaca;
    }
    
    /* Suavizar las pestañas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
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
# 2. FILTROS
# -----------------------------------------------------------
with st.expander("🔍 Filtros de Búsqueda Avanzada", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    try:
        clientes = get_clientes(user_id) 
        lugares = get_lugares_trabajo(user_id)
        
        clientes_map = {id: nombre for id, nombre in clientes}
        lugares_map = {id: nombre for id, nombre in lugares}
        
        with col1:
            cliente_filtro_nombre = st.selectbox(
                "Filtrar por cliente:",
                options=["Todos los clientes"] + list(clientes_map.values()),
            )
            cliente_filtro_id = next((id for id, nombre in clientes_map.items() if nombre == cliente_filtro_nombre), None)
        
        with col2:
            lugar_filtro_nombre = st.selectbox(
                "Filtrar por lugar:",
                options=["Todos los lugares"] + list(lugares_map.values()),
            )
            lugar_filtro_id = next((id for id, nombre in lugares_map.items() if nombre == lugar_filtro_nombre), None)
        
        with col3:
            fecha_filtro = st.selectbox(
                "Filtrar por fecha:",
                options=["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Todos"],
                index=3
            )
            
    except Exception as e:
        st.error(f"Error al cargar filtros: {str(e)}")
        st.stop()

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

# -----------------------------------------------------------
# 3. SECCIONES EN PESTAÑAS (Tabs)
# -----------------------------------------------------------
tab_presupuestos, tab_estados_cuenta = st.tabs(["📋 Presupuestos Guardados", "📄 Estados de Cuenta Generados"])

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
        suma_total_p = sum(safe_numeric_value(p.get('total', 0)) for p in presupuestos)
        total_p = len(presupuestos)
        avg_p = suma_total_p / total_p if total_p else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Presupuestos", f"{total_p}")
        c2.metric("Suma Total Presupuestos", f"${suma_total_p:,.0f}")
        c3.metric("Promedio Presupuestos", f"${avg_p:,.0f}")

        st.write("##") # Pequeño separador visual limpio
        st.subheader("📋 Lista de Presupuestos")

        # Encabezado usando la clase CSS .table-header
        with st.container():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2.3, 2.5, 0.9, 1.8, 2, 1, 3.5])
            col1.markdown('<div class="table-header">Cliente</div>', unsafe_allow_html=True)
            col2.markdown('<div class="table-header">Lugar</div>', unsafe_allow_html=True)
            col3.markdown('<div class="table-header">Descripción</div>', unsafe_allow_html=True)
            col4.markdown('<div class="table-header">Ver.</div>', unsafe_allow_html=True)
            col5.markdown('<div class="table-header">Fecha</div>', unsafe_allow_html=True)
            col6.markdown('<div class="table-header">Total</div>', unsafe_allow_html=True)
            col7.markdown('<div class="table-header">Ítems</div>', unsafe_allow_html=True)
            col8.markdown('<div class="table-header" style="text-align: center;">Acciones</div>', unsafe_allow_html=True)

        for p in presupuestos:
            # El contenedor ahora tiene automáticamente sombra e interactividad gracias al CSS inyectado arriba
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2.3, 2.5, 0.9, 1.8, 2, 1, 3.5])
            
                total_display = safe_numeric_value(p.get('total', 0))
                notas = p.get('notas', '')

                col1.write(f"**{p.get('cliente', {}).get('nombre', 'N/A').title()}**")
                col2.write(p.get('lugar', {}).get('nombre', 'N/A').title())
                
                descripcion = p.get('descripcion', 'Sin descripción')
                if descripcion and descripcion != 'Sin descripción' and len(descripcion) > 30:
                    col3.write(descripcion[:30] + "...")
                else:
                    col3.write(descripcion)

                col4.write(f"`{notas}`" if notas else "")

                fecha_str = p.get('fecha_creacion', datetime.now().isoformat())
                col5.write(fecha_str.split('T')[0] if 'T' in fecha_str else fecha_str)
                    
                col6.write(f"**${total_display:,.0f}**")
                col7.write(str(p.get('num_items', 0)))

                with col8:
                    b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                    
                    with b1:
                        if st.button("✏️", key=f"edit_{p['id']}", help="Editar presupuesto", use_container_width=True):
                            st.session_state['presupuesto_a_editar_id'] = p['id'] 
                            st.session_state['presupuesto_cargado_automaticamente'] = False
                            st.success("🔄 Redirigiendo...")
                            time.sleep(0.5)
                            st.switch_page("pages/_✏️ Editar.py")
                    
                    with b2:
                        pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(p['id'])
                        if success and pdf_bytes:
                            st.download_button(label="⬇️", data=pdf_bytes, file_name=file_name, mime="application/pdf", key=f"down_{p['id']}", use_container_width=True)
                        else:
                            st.button("🚫", key=f"down_dis_{p['id']}", disabled=True, use_container_width=True)
                    
                    with b3:
                        with st.popover("👁️", use_container_width=True):
                            st.header("📋 Vista Previa del Presupuesto")
                            _show_presupuesto_detail(presupuesto_id=p['id'])

                    with b4:
                        if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar", use_container_width=True):
                            if delete_presupuesto(p['id'], user_id):
                                st.success("✅ Eliminado")
                                st.rerun()

# =========================================================================
# PESTAÑA B: ESTADOS DE CUENTA
# =========================================================================
with tab_estados_cuenta:
    try:
        with st.spinner("🔄 Cargando estados de cuenta..."):
            from utils.db import toggle_estado_pago_ec
            estados_cuenta = get_estados_cuenta_usuario(user_id, filtros)
    except Exception as e:
        st.error(f"❌ Error al obtener estados de cuenta: {str(e)}")
        estados_cuenta = []

    if not estados_cuenta:
        st.info("🔍 No se encontraron estados de cuenta con los filtros seleccionados.")
    else:
        suma_total_ec = sum(safe_numeric_value(ec.get('total_neto', 0)) for ec in estados_cuenta)
        total_ec = len(estados_cuenta)
        avg_ec = suma_total_ec / total_ec if total_ec else 0

        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Total Estados Generados", f"{total_ec}")
        ec2.metric("Saldo Total Pendiente", f"${suma_total_ec:,.0f}")
        ec3.metric("Promedio Cobro", f"${avg_ec:,.0f}")

        st.write("##")
        st.subheader("📋 Lista de Estados de Cuenta")

        with st.container():
            col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([2, 2, 1.4, 1.4, 1.4, 1.4, 1.4, 3])
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
                col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([2, 2, 1.4, 1.4, 1.4, 1.4, 1.4, 3])
                
                cli_nom = ec.get('cliente', {}).get('nombre', 'N/A') if ec.get('cliente') else 'N/A'
                lug_nom = ec.get('lugar_trabajo', {}).get('nombre', 'N/A') if ec.get('lugar_trabajo') else 'N/A'
                
                col_cli.write(f"**{cli_nom.title()}**")
                col_lug.write(lug_nom.title())
                
                fec_emision = ec.get('fecha_emision', datetime.now().isoformat())
                col_fec.write(fec_emision.split('T')[0] if 'T' in fec_emision else fec_emision)
                
                col_sub.write(f"${safe_numeric_value(ec.get('monto_base', 0)):,.0f}")
                col_abo.write(f"-${safe_numeric_value(ec.get('abono_monto', 0)):,.0f}")
                col_net.write(f"**${safe_numeric_value(ec.get('total_neto', 0)):,.0f}**")
                
                # Renderizar estado usando clases CSS sofisticadas (Badges estilizados)
                es_pagado = ec.get('pagado', False)
                if es_pagado:
                    col_est.markdown('<div style="text-align: center;"><span class="badge-pagado">PAGADO</span></div>', unsafe_allow_html=True)
                else:
                    col_est.markdown('<div style="text-align: center;"><span class="badge-pendiente">PENDIENTE</span></div>', unsafe_allow_html=True)

                with col_acc:
                    ba1, ba2, ba3, ba4 = st.columns([1, 1, 1, 1])
                    
                    # 1. Descarga PDF
                    with ba1:
                        pdf_b, f_name, ok = mostrar_boton_descarga_estado_cuenta(ec['id'])
                        if ok and pdf_b:
                            st.download_button(
                                label="⬇️",
                                data=pdf_b,
                                file_name=f_name,
                                mime="application/pdf",
                                key=f"down_ec_{ec['id']}",
                                help="Descargar PDF",
                                use_container_width=True
                            )
                        else:
                            st.button("🚫", key=f"down_dis_ec_{ec['id']}", disabled=True, use_container_width=True)
                    
                    # 2. Vista Previa
                    with ba2:
                        with st.popover("👁️", use_container_width=True):
                            st.header("📄 Detalle de Estado de Cuenta")
                            st.write(f"**Documento N°:** {ec['id']:04d}")
                            st.write(f"**Fecha:** {fec_emision}")
                            st.divider()
                            st.info("Detalles adicionales del estado de cuenta.")

                    # 3. Cambiar Estado de Pago
                    with ba3:
                        icono_pago = "💵" if not es_pagado else "🔄"
                        ayuda_pago = "Marcar como PAGADO" if not es_pagado else "Cambiar a PENDIENTE"
                        if st.button(icono_pago, key=f"pay_ec_{ec['id']}", help=ayuda_pago, use_container_width=True):
                            if toggle_estado_pago_ec(ec['id'], not es_pagado):
                                st.cache_data.clear()  
                                st.toast(f"Estado de cuenta N°{ec['id']} actualizado", icon="🌱")
                                time.sleep(0.4)
                                st.rerun()

                    # 4. Eliminar
                    with ba4:
                        if st.button("🗑️", key=f"del_ec_{ec['id']}", help="Eliminar", use_container_width=True):
                            if delete_estado_cuenta(ec['id'], user_id):
                                st.cache_data.clear()  
                                st.success("✅ Eliminado")
                                time.sleep(0.4)
                                st.rerun()
                            else:
                                st.error("No se pudo eliminar.")