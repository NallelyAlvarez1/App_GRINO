import time
import streamlit as st
from utils.auth import check_login, sign_out
from datetime import datetime, timedelta
from utils.db import (
    get_supabase_client, get_clientes, get_lugares_trabajo, 
    get_presupuestos_usuario, delete_presupuesto,
    _show_presupuesto_detail,
    get_estados_cuenta_usuario,  # Importación limpia y directa
    delete_estado_cuenta
)
from utils.components import safe_numeric_value
from utils.pdf import mostrar_boton_descarga_pdf

try:
    from utils.pdf import mostrar_boton_descarga_estado_cuenta
except ImportError:
    def mostrar_boton_descarga_estado_cuenta(id): return None, "", False

st.markdown("""
<style>
.stTextInput, .stNumberInput, .stSelectbox, .stButton {
    margin-bottom: -0.3rem;
    margin-top: -0.4rem;
}
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
with st.expander("🔍 Filtros de Búsqueda", expanded=True):
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
        suma_total_p = sum(safe_numeric_value(p.get('total', 0)) for p in presupuestos)
        total_p = len(presupuestos)
        avg_p = suma_total_p / total_p if total_p else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Presupuestos", f"{total_p}")
        c2.metric("Suma Total Presupuestos", f"${suma_total_p:,.0f}")
        c3.metric("Promedio Presupuestos", f"${avg_p:,.0f}")

        st.subheader("📋 Lista de Presupuestos")

        with st.container():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2.5, 2.5, 1, 2, 2, 1, 3])
            col1.markdown("**Cliente**")
            col2.markdown("**Lugar**")
            col3.markdown("**Descripción**")
            col4.markdown("**Ver.**")
            col5.markdown("**Fecha**")
            col6.markdown("**Total**")
            col7.markdown("**Ítems**")
            col8.markdown("**Acciones**")

        for p in presupuestos:
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2.5, 2.5, 1, 2, 2, 1, 3])
            
                total_display = safe_numeric_value(p.get('total', 0))
                notas = p.get('notas', '')

                col1.write(p.get('cliente', {}).get('nombre', 'N/A').title())
                col2.write(p.get('lugar', {}).get('nombre', 'N/A').title())
                
                descripcion = p.get('descripcion', 'Sin descripción')
                if descripcion and descripcion != 'Sin descripción' and len(descripcion) > 30:
                    col3.write(descripcion[:30] + "...")
                else:
                    col3.write(descripcion)

                col4.write(f"**{notas}**")

                fecha_val = p.get('fecha_creacion')
                if isinstance(fecha_val, datetime):
                    fecha_display = fecha_val.strftime('%Y-%m-%d')
                elif isinstance(fecha_val, str):
                    fecha_display = fecha_val.split('T')[0] if 'T' in fecha_val else fecha_val
                else:
                    fecha_display = "N/A"

                col5.write(fecha_display)
                    
                col6.write(f"**${total_display:,.0f}**")
                col7.write(str(p.get('num_items', 0)))

                with col8:
                    b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                    
                    with b1:
                        if st.button("✏️", key=f"edit_{p['id']}", help="Editar presupuesto"):
                            st.session_state['presupuesto_a_editar_id'] = p['id'] 
                            st.session_state['presupuesto_cargado_automaticamente'] = False
                            st.success("🔄 Redirigiendo...")
                            time.sleep(0.5)
                            st.switch_page("pages/_✏️ Editar.py")
                    
                    with b2:
                        pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(p['id'])
                        if success and pdf_bytes:
                            st.download_button(label="⬇️", data=pdf_bytes, file_name=file_name, mime="application/pdf", key=f"down_{p['id']}")
                        else:
                            st.button("🚫", key=f"down_dis_{p['id']}", disabled=True)
                    
                    with b3:
                        with st.popover("👁️", use_container_width=True):
                            st.header("📋 Vista Previa del Presupuesto")
                            _show_presupuesto_detail(presupuesto_id=p['id'])

                    with b4:
                        if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar"):
                            if delete_presupuesto(p['id'], user_id):
                                st.success("✅ Eliminado")
                                st.rerun()

# =========================================================================
# PESTAÑA B: ESTADOS DE CUENTA
# =========================================================================
with tab_estados_cuenta:
    try:
        with st.spinner("🔄 Cargando estados de cuenta desde Supabase..."):
            # Importa la función de forma segura al momento de usarla si es necesario
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

        st.subheader("📋 Lista de Estados de Cuenta")

        # Modificación del encabezado: Agregamos columna Estado
        with st.container():
            col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5, 1.2, 2.8])
            col_cli.markdown("**Cliente**")
            col_lug.markdown("**Lugar de Trabajo**")
            col_fec.markdown("**Fecha Emisión**")
            col_sub.markdown("**Monto Base**")
            col_abo.markdown("**Abonos**")
            col_net.markdown("**Total Neto**")
            col_est.markdown("**Estado**")  # <-- Nueva Columna
            col_acc.markdown("**Acciones**")

        for ec in estados_cuenta:
            with st.container(border=True):
                col_cli, col_lug, col_fec, col_sub, col_abo, col_net, col_est, col_acc = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5, 1.2, 2.8])
                
                cli_nom = ec.get('cliente', {}).get('nombre', 'N/A') if ec.get('cliente') else 'N/A'
                lug_nom = ec.get('lugar_trabajo', {}).get('nombre', 'N/A') if ec.get('lugar_trabajo') else 'N/A'
                
                col_cli.write(cli_nom.title())
                col_lug.write(lug_nom.title())
                
                fec_emision = ec.get('fecha_emision', datetime.now().isoformat())
                col_fec.write(fec_emision.split('T')[0] if 'T' in fec_emision else fec_emision)
                
                col_sub.write(f"${safe_numeric_value(ec.get('monto_base', 0)):,.0f}")
                col_abo.write(f"-${safe_numeric_value(ec.get('abono_monto', 0)):,.0f}")
                col_net.write(f"**${safe_numeric_value(ec.get('total_neto', 0)):,.0f}**")
                
                # Renderizar estado visual dinámico (Columna Estado)
                es_pagado = ec.get('pagado', False)
                if es_pagado:
                    col_est.markdown("🟢 **Pagado**")
                else:
                    col_est.markdown("🔴 **Pendiente**")

                # Botones de Acción Modificados para incluir el Cambio de Estado
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
                                help="Descargar PDF"
                            )
                        else:
                            st.button("🚫", key=f"down_dis_ec_{ec['id']}", disabled=True)
                    
                    # 2. Vista Previa
                    with ba2:
                        with st.popover("👁️", use_container_width=True):
                            st.header("📄 Detalle de Estado de Cuenta")
                            st.write(f"**Documento N°:** {ec['id']:04d}")
                            st.write(f"**Fecha:** {fec_emision}")
                            st.divider()
                            st.info("Detalles adicionales del estado de cuenta.")

                    # 3. NUEVO BOTÓN: Cambiar Estado de Pago
                    with ba3:
                        icono_pago = "💵" if not es_pagado else "🔄"
                        ayuda_pago = "Marcar como PAGADO" if not es_pagado else "Cambiar a PENDIENTE"
                        if st.button(icono_pago, key=f"pay_ec_{ec['id']}", help=ayuda_pago, use_container_width=True):
                            if toggle_estado_pago_ec(ec['id'], not es_pagado):
                                st.cache_data.clear()  # <--- CRUCIAL: Limpia la caché para forzar la lectura del dato nuevo
                                st.toast(f"Estado de cuenta N°{ec['id']} actualizado", icon="🌱")
                                time.sleep(0.4)
                                st.rerun()

                    # 4. Eliminar
                    with ba4:
                        if st.button("🗑️", key=f"del_ec_{ec['id']}", help="Eliminar", use_container_width=True):
                            if delete_estado_cuenta(ec['id'], user_id):
                                st.cache_data.clear()  # <--- CRUCIAL: Limpia la caché al eliminar
                                st.success("✅ Eliminado correctamente")
                                time.sleep(0.4)
                                st.rerun()
                            else:
                                st.error("No se pudo eliminar.")