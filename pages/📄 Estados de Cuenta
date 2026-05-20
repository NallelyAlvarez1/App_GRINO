import streamlit as st
import datetime
from utils.db import get_clientes, get_lugares_trabajo

def seccion_estados_cuenta():
    st.header("📄 Generar Estado de Cuenta Mensual")
    
    user_id = st.session_state.get('user_id')
    
    # 1. Datos del Cliente y Lugar (Reutilizando tu lógica)
    col1, col2 = st.columns(2)
    with col1:
        clientes = get_clientes(user_id)
        # Formatear para el selectbox...
        cliente_seleccionado = st.selectbox("Seleccionar Cliente", clientes, format_func=lambda x: x[1])
    
    with col2:
        lugares = get_lugares_trabajo(user_id)
        lugar_seleccionado = st.selectbox("Lugar de Trabajo", lugares, format_func=lambda x: x[1])
        
    # 2. Selección de Período (Mes y Año)
    st.subheader("📆 Período de Cobro")
    col_mes, col_ano, col_base = st.columns(3)
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ano_actual = datetime.datetime.now().year
    
    with col_mes:
        mes_cobro = st.selectbox("Mes", range(1, 13), format_func=lambda x: meses[x-1])
    with col_ano:
        ano_cobro = st.selectbox("Año", [ano_actual - 1, ano_actual, ano_actual + 1], index=1)
    with col_base:
        monto_base = st.number_input("Monto Base Mensual ($)", min_value=0, value=0, step=5000)

    # 3. Servicios Adicionales (Tabla dinámica)
    st.subheader("➕ Servicios Adicionales / Cargos Extras")
    
    # Inicializar el estado para los items extras si no existen
    if 'servicios_extras' not in st.session_state:
        st.session_state.servicios_extras = []
        
    # Formulario rápido para añadir una fila extra
    with st.expander("Añadir Servicio Adicional"):
        col_desc, col_monto, col_btn = st.columns([3, 2, 1])
        with col_desc:
            desc_extra = st.text_input("Descripción del servicio")
        with col_monto:
            monto_extra = st.number_input("Valor ($)", min_value=0, step=1000)
        with col_btn:
            st.write("<br>", unsafe_allow_html=True) # Alinear botón
            if st.button("Añadir"):
                if desc_extra:
                    st.session_state.servicios_extras.append({
                        "descripcion": desc_extra,
                        "monto": monto_extra
                    })
                    st.rerun()

    # Mostrar los servicios añadidos actualmente
    if st.session_state.servicios_extras:
        st.write("---")
        total_extras = 0
        for i, item in enumerate(st.session_state.servicios_extras):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"• {item['descripcion']}")
            c2.write(f"${item['monto']:,}".replace(",", "."))
            if c3.button("❌", key=f"del_{i}"):
                st.session_state.servicios_extras.pop(i)
                st.rerun()
            total_extras += item['monto']
        
        total_final = monto_base + total_extras
        st.markdown(f"### **Total a Cobrar:** ${total_final:,}".replace(",", "."))
    else:
        st.markdown(f"### **Total a Cobrar:** ${monto_base:,}".replace(",", "."))

    # 4. Botón de Guardar y Generar
    if st.button("💾 Guardar y Generar PDF Estado de Cuenta", type="primary"):
        # Aquí llamarías a las funciones de base de datos para guardar
        # Y posteriormente pasarías los datos al módulo de PDF
        st.success("¡Estado de cuenta generado con éxito!")