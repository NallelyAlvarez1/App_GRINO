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
# DISEÑO UI Y INYECCIÓN CSS MODERNO
# -----------------------------------------------------------
st.markdown("""
<style>
    /* Importar tipografía moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stWidgetLabel"] {
        font-family: 'Inter', sans-serif;
    }

    /* Ajustes compactos generales */
    .stTextInput, .stNumberInput, .stSelectbox, .stButton {
        margin-bottom: -0.1rem;
        margin-top: -0.1rem;
    }
    
    /* Encabezados estilizados */
    h1, h2, h3 {
        color: #1E293B !important;
        font-weight: 700 !important;
    }
    
    /* Tarjetas Modernas para los Registros */
    .document-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    .document-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transform: translateY(-1px);
    }

    /* Encabezados de tabla personalizados */
    .table-header {
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding-bottom: 8px;
    }

    /* Badges de Estado Estilizados */
    .badge {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        text-align: center;
    }
    .badge-paid {
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #BBF7D0;
    }
    .badge-pending {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
    }

    /* Ajustar los Popovers y expansores */
    .stExpander {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #F8FAFC !important;
    }
    
    /* Customización de las pestañas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #64748B !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #4F46E5 !important;
        border-bottom-color: #4F46E5 !important;
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
# 2. FILTROS (Diseño más limpio)
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
        # Indicadores en la parte superior mejor formateados
        suma_total_p = sum(safe_numeric_value(p.get('total', 0)) for p in presupuestos)
        total_p = len(presupuestos)
        avg_p = suma_total_p / total_p if total_p else 0

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Presupuestos", f"{total_p}")
        with c2:
            st.metric("Suma Total", f"${suma_total_p:,.0f}")
        with c3:
            st.metric("Promedio", f"${avg_p:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Encabezados de columnas fijos
        st.markdown("""
        <div class="table-header">
            <table style="width:100%; border-collapse: collapse; table-layout: fixed;">
                <tr>
                    <td style="width: 18%;">Cliente</td>
                    <td style="width: 18%;">Lugar</td>
                    <td style="width: 20%;">Descripción</td>
                    <td style="width: 8%;">Ver.</td>
                    <td style="width: 12%;">Fecha</td>
                    <td style="width: 12%;">Total</td>
                    <td style="width: 12%;">Acciones</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        for p in presupuestos:
            # Envolvemos la fila en un contenedor HTML con nuestra clase CSS
            st.markdown('<div class="document-card">', unsafe_allow_html=True)
            col1, col2, col3, col4, col5, col6, col8 = st.columns([1.8, 1.8, 2.0, 0.8, 1.2, 1.2, 1.2])
            
            total_display = safe_numeric_value(p.get('total', 0))
            notas = p.get('notas', '')

            col1.write(p.get('cliente', {}).get('nombre', 'N/A').title())
            col2.write(p.get('lugar', {}).get('nombre', 'N/A').title())
            
            descripcion = p.get('descripcion', 'Sin descripción')
            if descripcion and descripcion != 'Sin descripción' and len(descripcion) > 25:
                col3.write(descripcion[:25] + "...")
            else:
                col3.write(descripcion)

            col4.write(f"**{notas}**")

            fecha_str = p.get('fecha_creacion', datetime.now().isoformat())
            col5.write(fecha_str.split('T')[0] if 'T' in fecha_str else fecha_str)
                
            col6.write(f"**${total_display:,.0f}**")

            with col8:
                b1, b2, b3, b4 = st.columns(4)
                
                with b1:
                    if st.button("✏️", key=f"edit_{p['id']}", help="Editar"):
                        st.session_state['presupuesto_a_editar_id'] = p['id'] 
                        st.session_state['presupuesto_cargado_automaticamente'] = False
                        st.success("🔄 Redirigiendo...")
                        time.sleep(0.5)
                        st.switch_page("pages/_✏️ Editar.py")
                
                with b2:
                    pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(p['id'])
                    if success and pdf_bytes:
                        st.download_button(label="⬇️", data=pdf_bytes, file_name=file_name, mime="application/pdf", key=f"down_{p['id']}", help="Descargar PDF")
                    else:
                        st.button("🚫", key=f"down_dis_{p['id']}", disabled=True)
                
                with b3:
                    with st.popover("👁️", use_container_width=True, help="Ver Detalle"):
                        st.header("📋 Vista Previa")
                        _show_presupuesto_detail(presupuesto_id=p['id'])

                with b4:
                    if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar"):
                        if delete_presupuesto(p['id'], user_id):
                            st.success("✅ Eliminado")
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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
        with ec1:
            st.metric("Total Estados", f"{total_ec}")
        with ec2:
            st.metric("Saldo Pendiente", f"${suma_total_ec:,.0f}")
        with ec3:
            st.metric("Promedio Cobro", f"${avg_ec:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Encabezados de columnas de Estados de Cuenta fijos
        st.markdown("""
        <div class="table-header">
            <table style="width:100%; border-collapse: collapse; table-layout: fixed;">
                <tr>
                    <td style="width: 20%;">Cliente</td>
                    <td style="width: 20%;">Lugar de Trabajo</td>
                    <td style="width: 15%;">Fecha Emisión</td>
                    <td style="width: 12%;">Monto Base</td>
                    <td style="width: 11%;">Total Neto</td>
                    <td style="width: 12%;">Estado</td>
                    <td style="width: 10%;">Acciones</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        for ec in estados_cuenta:
            # Envolvemos en nuestra tarjeta estilizada
            st.markdown('<div class="document-card">', unsafe_allow_html=True)
            col_cli, col_lug, col_fec, col_sub, col_net, col_est, col_acc = st.columns([2.0, 2.0, 1.5, 1.2, 1.1, 1.2, 1.0])
            
            cli_nom = ec.get('cliente', {}).get('nombre', 'N/A') if ec.get('cliente') else 'N/A'
            lug_nom = ec.get('lugar_trabajo', {}).get('nombre', 'N/A') if ec.get('lugar_trabajo') else 'N/A'
            
            col_cli.write(cli_nom.title())
            col_lug.write(lug_nom.title())
            
            fec_emision = ec.get('fecha_emision', datetime.now().isoformat())
            col_fec.write(fec_emision.split('T')[0] if 'T' in fec_emision else fec_emision)
            
            col_sub.write(f"${safe_numeric_value(ec.get('monto_base', 0)):,.0f}")
            col_net.write(f"**${safe_numeric_value(ec.get('total_neto', 0)):,.0f}**")
            
            # Renderizar estado visual dinámico usando clases CSS (Badges)
            es_pagado = ec.get('pagado', False)
            if es_pagado:
                col_est.markdown('<span class="badge badge-paid">🟢 Pagado</span>', unsafe_allow_html=True)
            else:
                col_est.markdown('<span class="badge badge-pending">🔴 Pendiente</span>', unsafe_allow_html=True)

            with col_acc:
                ba1, ba2, ba3, ba4 = st.columns(4)
                
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
                            help="Descargar PDF"
                        )
                    else:
                        st.button("🚫", key=f"down_dis_ec_{ec['id']}", disabled=True)
                
                # 2. Vista Previa
                with ba2:
                    with st.popover("👁️", use_container_width=True, help="Detalles"):
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
                            st.success("✅ Eliminado correctamente")
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("No se pudo eliminar.")
            st.markdown('</div>', unsafe_allow_html=True)