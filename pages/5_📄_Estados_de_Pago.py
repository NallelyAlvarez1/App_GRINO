import streamlit as st
import datetime
import time
from utils.auth import check_login, sign_out
from utils.db import get_clientes, get_lugares_trabajo, get_supabase_client
from utils.pdf import generar_pdf_estado_cuenta

st.header("📄 Generar Estado de Cuenta Mensual")

user_id = st.session_state.get('user_id')

# ----- autenticación -----
is_logged_in = check_login()

if not is_logged_in:
    st.error("🔒 No has iniciado sesión. Serás redirigido al inicio en 5 segundos...")
    progress_bar = st.progress(0)
    for percent_complete in range(100):
        time.sleep(0.05)
        progress_bar.progress(percent_complete + 1)
    st.switch_page("🌱_App_principal.py")
    st.stop()

# Inicializar contenedor de ítems múltiples en el estado de la sesión
if 'items_estado_cuenta' not in st.session_state:
    st.session_state.items_estado_cuenta = []

# 1. Datos del Cliente y Lugar
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

st.write("---")

# 2. Agregar Conceptos (Añadir múltiples meses o extras)
st.subheader("➕ Agregar Cargos al Estado de Cuenta")
tab_mes, tab_servicio = st.tabs(["📆 Agregar Mes de Mantención", "🛠️ Agregar Servicio Adicional"])

meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
ano_actual = datetime.datetime.now().year

with tab_mes:
    col_m, col_a, col_b, col_btn_m = st.columns([2, 2, 2, 1])
    with col_m:
        mes_cobro = st.selectbox("Mes", range(1, 13), format_func=lambda x: meses[x-1], key="sel_mes")
    with col_a:
        ano_cobro = st.selectbox("Año", [ano_actual - 1, ano_actual, ano_actual + 1], index=1, key="sel_ano")
    with col_b:
        monto_base = st.number_input("Monto Base ($)", min_value=0, value=0, step=5000, key="num_base")
    with col_btn_m:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Añadir Mes", key="btn_add_mes"):
            desc_mes = f"Mantención Mensual Base - {meses[mes_cobro-1]} {ano_cobro}"
            st.session_state.items_estado_cuenta.append({
                "tipo": "mes_base",
                "descripcion": desc_mes,
                "monto": monto_base,
                "mes_num": mes_cobro,
                "anio_num": ano_cobro
            })
            st.rerun()

with tab_servicio:
    col_desc, col_monto, col_btn_s = st.columns([4, 2, 1])
    with col_desc:
        desc_extra = st.text_input("Descripción del Servicio Extra", key="input_desc_extra")
    with col_monto:
        monto_extra = st.number_input("Valor ($)", min_value=0, step=1000, key="input_monto_extra")
    with col_btn_s:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Añadir Servicio", key="btn_add_servicio"):
            if desc_extra:
                st.session_state.items_estado_cuenta.append({
                    "tipo": "servicio_extra",
                    "descripcion": desc_extra,
                    "monto": monto_extra,
                    "mes_num": None,
                    "anio_num": None
                })
                st.rerun()

# 3. Listado y Resumen
if st.session_state.items_estado_cuenta:
    st.write("---")
    st.subheader("📋 Detalle del Estado de Cuenta Actual")
    
    total_cargos = 0
    for i, item in enumerate(st.session_state.items_estado_cuenta):
        c1, c2, c3 = st.columns([4, 2, 1])
        prefix = "📆" if item["tipo"] == "mes_base" else "🛠️"
        c1.write(f"{prefix} {item['descripcion']}")
        c2.write(f"${item['monto']:,}".replace(",", "."))
        if c3.button("❌", key=f"del_{i}"):
            st.session_state.items_estado_cuenta.pop(i)
            st.rerun()
        total_cargos += item['monto']
        
    st.write("---")
    col_space, col_abono_field = st.columns([4, 3])
    with col_abono_field:
        abono_monto = st.number_input("Abono / Pago Recibido a Descontar ($)", min_value=0, value=0, step=5000)
        
    total_final = total_cargos - abono_monto
    
    st.markdown(f"""
    ### Resumen del Saldo
    * **Subtotal Cargos Añadidos:** ${total_cargos:,}
    * **Abonos Aplicados:** -${abono_monto:,}
    ### **Total Saldo Pendiente:** ${total_final:,}
    """.replace(",", "."))
    
    # 4. Procesar Guardado y habilitar el PDF
    if st.button("💾 Guardar y Generar PDF", type="primary", use_container_width=True):
        supabase = get_supabase_client()
        try:
            # Extraer primer mes y año disponible para guardar como referencia en campos de cabecera
            primer_mes = next((x["mes_num"] for x in st.session_state.items_estado_cuenta if x["mes_num"]), datetime.datetime.now().month)
            primer_ano = next((x["anio_num"] for x in st.session_state.items_estado_cuenta if x["anio_num"]), datetime.datetime.now().year)
            
            estado_cuenta_data = {
                "user_id": user_id,
                "cliente_id": cliente_seleccionado[0],
                "lugar_trabajo_id": lugar_seleccionado[0],
                "mes_num": primer_mes,
                "anio_num": primer_ano,
                "monto_base": next((x["monto"] for x in st.session_state.items_estado_cuenta if x["tipo"] == "mes_base"), 0),
                "abono_monto": abono_monto,
                "total_neto": total_final,
                "fecha_emision": datetime.date.today().isoformat()
            }
            
            response = supabase.table("estados_cuenta").insert(estado_cuenta_data).execute()
            
            if response.data:
                nuevo_id = response.data[0]['id']
                
                # Insertar los ítems múltiples del desglose
                items_a_insertar = []
                for item in st.session_state.items_estado_cuenta:
                    items_a_insertar.append({
                        "estado_cuenta_id": nuevo_id,
                        "descripcion": item['descripcion'],
                        "monto": item['monto']
                    })
                supabase.table("detalles_estado_cuenta").insert(items_a_insertar).execute()
                
                # Generar el PDF usando el nuevo diseño idéntico al presupuesto
                pdf_bytes, file_name = generar_pdf_estado_cuenta(
                    id_documento=nuevo_id,
                    cliente_nombre=cliente_seleccionado[1],
                    lugar_nombre=lugar_seleccionado[1],
                    items=st.session_state.items_estado_cuenta,
                    abono=abono_monto,
                    total=total_final
                )
                
                st.success(f"✅ Estado de Cuenta N° {nuevo_id} guardado correctamente.")
                
                # Desplegar botón de descarga nativo con el diseño aplicado
                st.download_button(
                    label="📥 Descargar PDF Estado de Cuenta",
                    data=pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Vaciar la lista tras procesamiento exitoso
                st.session_state.items_estado_cuenta = []
                
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
else:
    st.info("💡 Comienza agregando meses de mantención o servicios adicionales para conformar el Estado de Cuenta.")