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
# 1. CONFIGURACIÓN Y ESTILOS CSS AVANZADOS
# -----------------------------------------------------------
st.set_page_config(page_title="Historial", page_icon="🕒", layout="wide")

# Inyección de CSS limpio y moderno estilo "Glassmorphism" y tarjetas suaves
st.markdown("""
<style>
    /* Importación de fuente moderna si se desea cambiar globalmente */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stWidgetLabel"] {
        font-family: 'Inter', sans-serif;
    }

    /* Optimización de espacios en inputs y botones */
    .stTextInput, .stNumberInput, .stSelectbox, .stButton {
        margin-bottom: -0.1rem;
        margin-top: -0.1rem;
    }
    
    /* Reducir espacio excesivo en títulos */
    h1, h2, h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.8rem !important;
        font-weight: 600;
    }                

    /* Tarjetas de Métricas Mejoradas */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #2E7D32 !important; /* Color verde corporativo suave */
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #555555;
    }

    /* Contenedores de tarjetas con bordes suaves y sombra */
    div[data-testid="stElementContainer"] div.element-container {
        border-radius: 10px;
    }

    /* Estilos personalizados para los Badges/Etiquetas de Estado */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        text-align: center;
    }
    .badge-pagado {
        background-color: #E8F5E9;
        color: #2E7D32;
        border: 1px solid #C8E6C9;
    }
    .badge-pendiente {
        background-color: #FFEBEE;
        color: #C62828;
        border: 1px solid #FFCDD2;
    }
    
    /* Efecto Hover global para botones de acción dentro de las filas */
    button[key^="edit_"], button[key^="down_"], button[key^="pay_"], button[key^="del_"] {
        transition: all 0.2s ease-in-out !important;
    }
    button[key^="edit_"]:hover, button[key^="down_"]:hover, button[key^="pay_"]:hover {
        transform: scale(1.08);
        background-color: #F0F4F8 !important;
    }
    button[key^="del_"]:hover {
        transform: scale(1.08);
        background-color: #FFEBEE !important;
        border-color: #EF5350 !important;
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
# 2. FILTROS (Diseño limpio dentro de un Expander)
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
        # Tarjetas de métricas estilizadas automáticamente con el CSS superior
        suma_total_p = sum(safe_numeric_value(p.get('total', 0)) for p in presupuestos)
        total_p = len(presupuestos)
        avg_p = suma_total_p / total_p if total_p else 0

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Total Presupuestos", f"{total_p}")
        with c2: st.metric("Suma Total", f"${suma_total_p:,.0f}")
        with c3: st.metric("Promedio", f"${avg_p:,.0f}")

        st.markdown("---")

        # Fila de Encabezados (Estilizada con Markdown)
        with st.container():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2.5, 1.5, 1.5, 1, 2.5])
            col1.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>👤 CLIENTE</p>", unsafe_allow_html=True)
            col2.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>📍 LUGAR</p>", unsafe_allow_html=True)
            col3.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>📝 DESCRIPCIÓN</p>", unsafe_allow_html=True)
            col4.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>📅 FECHA</p>", unsafe_allow_html=True)
            col5.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>💰 TOTAL</p>", unsafe_allow_html=True)
            col6.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>📦 ÍTEMS</p>", unsafe_allow_html=True)
            col7.markdown("<p style='color:#777; font-weight:600; margin-bottom:0; text-align:center;'>⚡ ACCIONES</p>", unsafe_allow_html=True)

        for p in presupuestos:
            # Uso de container con border nativo de Streamlit, estilizado vía CSS superior
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2.5, 1.5, 1.5, 1, 2.5])
            
                total_display = safe_numeric_value(p.get('total', 0))
                notas = p.get('notas', '')
                version_str = f" <span style='color:#007BFF; font-size:0.8rem; font-weight:bold;'>({notas})</span>" if notas else ""

                col1.markdown(f"**{p.get('cliente', {}).get('nombre', 'N/A').title()}**{version_str}", unsafe_allow_html=True)
                col2.write(p.get('lugar', {}).get('nombre', 'N/A').title())
                
                descripcion = p.get('descripcion', 'Sin descripción')
                if descripcion and descripcion != 'Sin descripción' and len(descripcion) > 30:
                    col3.write(descripcion[:30] + "...")
                else:
                    col3.write(descripcion)

                fecha_str = p.get('fecha_creacion', datetime.now().isoformat())
                col4.write(fecha_str.split('T')[0] if 'T' in fecha_str else fecha_str)
                    
                col5.markdown(f"<span style='color:#2E7D32; font-weight:700;'>${total_display:,.0f}</span>", unsafe_allow_html=True)
                col6.write(f"  {p.get('num_items', 0)} uds")

                with col7:
                    b1, b2, b3, b4 = st.columns(4)
                    
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
                            st.download_button(label="⬇️", data=pdf_bytes, file_name=file_name, mime="application/pdf", key=f"down_{p['id']}", help="Descargar PDF", use_container_width=True)
                        else:
                            st.button("🚫", key=f"down_dis_{p['id']}", disabled=True, use_container_width=True)
                    
                    with b3:
                        with st.popover("👁️", use_container_width=True):
                            st.markdown("### 📋 Vista Previa del Presupuesto")
                            _show_presupuesto_detail(presupuesto_id=p['id'])

                    with b4:
                        if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar definitivo", use_container_width=True):
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
        with ec1: st.metric("Total Estados", f"{total_ec}")
        with ec2: st.metric("Saldo Pendiente", f"${suma_total_ec:,.0f}")
        with ec3: st.metric("Promedio Cobro", f"${avg_ec:,.0f}")

        st.markdown("---")

        # Fila de Encabezados de Estados de Cuenta
        with st.container():
            col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([1.8, 1.8, 1.2, 1.2, 1.2, 1.3, 1.2, 2.3])
            col_cli.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>👤 CLIENTE</p>", unsafe_allow_html=True)
            col_lug.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>📍 LUGAR</p>", unsafe_allow_html=True)
            col_fec.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>📅 EMISIÓN</p>", unsafe_allow_html=True)
            col_sub.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>BASE</p>", unsafe_allow_html=True)
            col_abo.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>ABONOS</p>", unsafe_allow_html=True)
            col_net.markdown("<p style='color:#777; font-weight:600; margin-bottom:0;'>TOTAL NETO</p>", unsafe_allow_html=True)
            col_est.markdown("<p style='color:#777; font-weight:600; margin-bottom:0; text-align:center;'>📌 ESTADO</p>", unsafe_allow_html=True)
            col_acc.markdown("<p style='color:#777; font-weight:600; margin-bottom:0; text-align:center;'>⚡ ACCIONES</p>", unsafe_allow_html=True)

        for ec in estados_cuenta:
            with st.container(border=True):
                col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([1.8, 1.8, 1.2, 1.2, 1.2, 1.3, 1.2, 2.3])
                
                cli_nom = ec.get('cliente', {}).get('nombre', 'N/A') if ec.get('cliente') else 'N/A'
                lug_nom = ec.get('lugar_trabajo', {}).get('nombre', 'N/A') if ec.get('lugar_trabajo') else 'N/A'
                
                col_cli.markdown(f"**{cli_nom.title()}**")
                col_lug.write(lug_nom.title())
                
                fec_emision = ec.get('fecha_emision', datetime.now().isoformat())
                col_fec.write(fec_emision.split('T')[0] if 'T' in fec_emision else fec_emision)
                
                col_sub.write(f"${safe_numeric_value(ec.get('monto_base', 0)):,.0f}")
                col_abo.markdown(f"<span style='color:#C62828;'>-${safe_numeric_value(ec.get('abono_monto', 0)):,.0f}</span>", unsafe_allow_html=True)
                col_net.markdown(f"**${safe_numeric_value(ec.get('total_neto', 0)):,.0f}**")
                
                # Renderizado dinámico usando badges HTML estilizados arriba
                es_pagado = ec.get('pagado', False)
                if es_pagado:
                    col_est.markdown("<div style='text-align:center;'><span class='badge badge-pagado'>🟢 Pagado</span></div>", unsafe_allow_html=True)
                else:
                    col_est.markdown("<div style='text-align:center;'><span class='badge badge-pendiente'>🔴 Pendiente</span></div>", unsafe_allow_html=True)

                # Botones de Acción unificados en tamaño
                with col_acc:
                    ba1, ba2, ba3, ba4 = st.columns(4)
                    
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
                    
                    with ba2:
                        with st.popover("👁️", use_container_width=True):
                            st.markdown("### 📄 Detalle de Estado de Cuenta")
                            st.write(f"**Documento N°:** {ec['id']:04d}")
                            st.write(f"**Fecha:** {fec_emision}")
                            st.divider()
                            st.info("Detalles adicionales del estado de cuenta.")

                    with ba3:
                        icono_pago = "💵" if not es_pagado else "🔄"
                        ayuda_pago = "Marcar como PAGADO" if not es_pagado else "Cambiar a PENDIENTE"
                        if st.button(icono_pago, key=f"pay_ec_{ec['id']}", help=ayuda_pago, use_container_width=True):
                            if toggle_estado_pago_ec(ec['id'], not es_pagado):
                                st.cache_data.clear()  
                                st.toast(f"Estado de cuenta N°{ec['id']} actualizado", icon="🌱")
                                time.sleep(0.4)
                                st.rerun()

                    with ba4:
                        if st.button("🗑️", key=f"del_ec_{ec['id']}", help="Eliminar", use_container_width=True):
                            if delete_estado_cuenta(ec['id'], user_id):
                                st.cache_data.clear()  
                                st.success("✅ Eliminado")
                                time.sleep(0.4)
                                st.rerun()