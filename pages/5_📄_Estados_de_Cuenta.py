import streamlit as st
import datetime
from utils.db import get_clientes, get_lugares_trabajo, get_supabase_client

st.header("📄 Generar Estado de Cuenta Mensual")

user_id = st.session_state.get('user_id')

if not user_id:
    st.warning("⚠️ Debes iniciar sesión para acceder a este módulo.")
    st.stop()

# 1. Datos del Cliente y Lugar (Reutilizando tu lógica)
col1, col2 = st.columns(2)
with col1:
    clientes = get_clientes(user_id)
    if clientes:
        cliente_seleccionado = st.selectbox("Seleccionar Cliente", clientes, format_func=lambda x: x[1])
    else:
        st.error("No tienes clientes registrados.")
        st.stop()

with col2:
    lugares = get_lugares_trabajo(user_id)
    if lugares:
        lugar_seleccionado = st.selectbox("Lugar de Trabajo", lugares, format_func=lambda x: x[1])
    else:
        st.error("No tienes lugares de trabajo registrados.")
        st.stop()
        
# 2. Selección de Período, Monto Base y Abonos
st.subheader("📆 Período de Cobro y Valores")
col_mes, col_ano, col_base, col_abono = st.columns(4)

meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
ano_actual = datetime.datetime.now().year

with col_mes:
    mes_cobro = st.selectbox("Mes Cobrado", range(1, 13), format_func=lambda x: meses[x-1], index=datetime.datetime.now().month - 1)
with col_ano:
    ano_cobro = st.selectbox("Año Cobrado", [ano_actual - 1, ano_actual, ano_actual + 1], index=1)
with col_base:
    monto_base = st.number_input("Monto Base Mensual ($)", min_value=0, value=0, step=5000)
with col_abono:
    abono_monto = st.number_input("Abono / Pago Recibido ($)", min_value=0, value=0, step=5000)

# 3. Servicios Adicionales (Tabla dinámica)
st.subheader("➕ Servicios Adicionales / Cargos Extras")

# Inicializar el estado para los items extras si no existen
if 'servicios_extras' not in st.session_state:
    st.session_state.servicios_extras = []
    
# Formulario rápido para añadir una fila extra
with st.expander("Añadir Servicio Adicional"):
    col_desc, col_monto, col_btn = st.columns([3, 2, 1])
    with col_desc:
        desc_extra = st.text_input("Descripción del servicio", key="input_desc_extra")
    with col_monto:
        monto_extra = st.number_input("Valor ($)", min_value=0, step=1000, key="input_monto_extra")
    with col_btn:
        st.write("<br>", unsafe_allow_html=True) # Alinear botón
        if st.button("Añadir", width=100):
            if desc_extra:
                st.session_state.servicios_extras.append({
                    "descripcion": desc_extra,
                    "monto": monto_extra
                })
                st.rerun()

# Calcular Totales en tiempo real
total_extras = sum(item['monto'] for item in st.session_state.servicios_extras)
total_final = (monto_base + total_extras) - abono_monto

# Mostrar los servicios añadidos actualmente si existen
if st.session_state.servicios_extras:
    st.markdown("#### Desglose de Servicios Extra:")
    for i, item in enumerate(st.session_state.servicios_extras):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"• {item['descripcion']}")
        c2.write(f"${item['monto']:,}".replace(",", "."))
        if c3.button("❌", key=f"del_{i}"):
            st.session_state.servicios_extras.pop(i)
            st.rerun()
    st.write("---")

# Cuadro resumen informativo
st.markdown(f"""
### Resumen del Saldo
* **Mantención Base:** ${monto_base:,}
* **Total Servicios Extras:** ${total_extras:,}
* **Abonos Aplicados:** -${abono_monto:,}
### **Total Saldo Pendiente:** ${total_final:,}
""".replace(",", "."))

# 4. Botón de Guardar y Procesar en la Base de Datos
if st.button("💾 Guardar Estado de Cuenta", type="primary", use_container_width=True):
    supabase = get_supabase_client()
    
    try:
        # Preparar inserción cabecera
        estado_cuenta_data = {
            "user_id": user_id,
            "cliente_id": cliente_seleccionado[0],
            "lugar_trabajo_id": lugar_seleccionado[0],
            "mes_num": mes_cobro,
            "anio_num": ano_cobro,
            "monto_base": monto_base,
            "abono_monto": abono_monto,
            "total_neto": total_final,
            "fecha_emision": datetime.date.today().isoformat()
        }
        
        # Insertar cabecera en 'estados_cuenta'
        response = supabase.table("estados_cuenta").insert(estado_cuenta_data).execute()
        
        if response.data:
            nuevo_id = response.data[0]['id']
            
            # Insertar los servicios adicionales si existen
            if st.session_state.servicios_extras:
                items_a_insertar = []
                for item in st.session_state.servicios_extras:
                    items_a_insertar.append({
                        "estado_cuenta_id": nuevo_id,
                        "descripcion": item['descripcion'],
                        "monto": item['monto']
                    })
                supabase.table("detalles_estado_cuenta").insert(items_a_insertar).execute()
            
            st.success(f"✅ Estado de cuenta N° {nuevo_id} guardado correctamente en Supabase.")
            
            # Limpiar servicios del estado tras un guardado exitoso
            st.session_state.servicios_extras = []
            st.rerun()
        else:
            st.error("❌ No se pudo guardar el registro principal.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar en la Base de Datos: {str(e)}")