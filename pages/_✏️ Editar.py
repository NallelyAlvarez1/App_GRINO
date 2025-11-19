import os
from typing import Dict, Any, List
import streamlit as st
from datetime import datetime
import pandas as pd
import uuid
from utils.db import (
    get_supabase_client,
    get_clientes,
    get_lugares_trabajo,
    get_presupuesto_detallado,  # Mantener por si acaso
    get_presupuesto_para_editar,  # Nueva función
    get_presupuestos_para_edicion,
    save_edited_presupuesto
)
# Auth
from utils.auth import check_login, sign_out
# DB / utilidades

# PDF
from utils.pdf import generar_pdf
# Componentes
from utils.components import (
    show_resumen,
    safe_numeric_value,
    show_edited_presupuesto,
    show_trabajos_simples,
    clean_integer_input,
    ensure_ids_and_positions,
    show_cliente_lugar_selector_edicion,
    add_item_to_category
)

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

st.set_page_config(page_title="Editar", page_icon="🌱", layout="wide")
st.header("✏️ Editar presupuesto")

# ----- autenticación -----
is_logged_in = check_login()
if not is_logged_in:
    st.error("🔒 Por favor inicie sesión primero")
    st.page_link("App_principal.py", label="Ir a página de inicio")
    st.stop()

with st.sidebar:
    st.markdown("**👤 Usuario:**")
    st.markdown(f"`{st.session_state.usuario}`")

    if st.button("🚪 Cerrar Sesión", type="primary", width='stretch'):
        sign_out()
        st.toast("Sesión cerrada correctamente", icon="🌱")
        st.rerun()

# ----- constantes y session -----
EDICION_KEY = 'categorias_edicion'
HISTORIAL_PAGE = "pages/2_🕒_historial.py"

user_id = st.session_state.get('user_id')
supabase = get_supabase_client()

# ----- utilidades -----
def get_presupuestos_para_selector(user_id: int) -> List[tuple]:
    """Obtener lista de presupuestos para el selector - VERSIÓN CON DEPURACIÓN"""
    try:
        presupuestos = get_presupuestos_para_edicion(user_id)      
        if not presupuestos:
            st.info("📭 No se encontraron presupuestos")
            return []
        
        # Construir opciones simples
        opciones = []
        for presup in presupuestos:
            presup_id = presup.get('id')
            fecha = presup.get('fecha_creacion', '')
            
            if fecha:
                try:
                    if isinstance(fecha, str):
                        fecha_obj = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
                    else:
                        fecha_obj = fecha
                    fecha_str = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_str = "Fecha inválida"
            else:
                fecha_str = "Sin fecha"
            
            # Usar ID y fecha para la etiqueta
            label = f"ID: {presup_id} - Creado: {fecha_str}"
            opciones.append((presup_id, label))

        return opciones
        
    except Exception as e:
        st.error(f"❌ Error al cargar presupuestos: {e}")
        return []

def cargar_presupuesto_en_sesion(presupuesto_id: int) -> bool:
    """Cargar un presupuesto en la sesión para edición"""
    try:
        # Usar la nueva función específica para edición
        detalle = get_presupuesto_para_editar(presupuesto_id)
        if not detalle:
            st.error(f"❌ Error al cargar el detalle del presupuesto ID: {presupuesto_id}")
            return False

        # Limpiar estado anterior
        for key in [EDICION_KEY, 'categorias', 'presupuesto_cliente_id', 'presupuesto_lugar_trabajo_id', 
                   'presupuesto_descripcion', 'presupuesto_a_editar_id']:
            st.session_state.pop(key, None)

        # estructura base
        st.session_state[EDICION_KEY] = {'general': {'items': [], 'mano_obra': 0.0}}

        # metadatos
        st.session_state['presupuesto_cliente_id'] = detalle.get('cliente_id')
        st.session_state['presupuesto_lugar_trabajo_id'] = detalle.get('lugar_trabajo_id')
        st.session_state['presupuesto_descripcion'] = detalle.get('descripcion', '')
        st.session_state['presupuesto_a_editar_id'] = presupuesto_id

        # items: agrupar por categoria
        items_detalle = detalle.get('items', [])

        for item in items_detalle:
            cat_nombre = item.get('categoria') or 'Sin Categoría'
            nombre_item = (item.get('nombre') or '').strip()

            cantidad = safe_numeric_value(item.get('cantidad', 0))
            precio_unitario = safe_numeric_value(item.get('precio_unitario', 0))
            total = safe_numeric_value(item.get('total', 0))

            # Mano de obra por nombre
            if 'mano de obra' in nombre_item.lower():
                mo_key = cat_nombre if cat_nombre != 'Sin Categoría' else 'general'
                if mo_key not in st.session_state[EDICION_KEY]:
                    st.session_state[EDICION_KEY][mo_key] = {'items': [], 'mano_obra': 0.0}
                st.session_state[EDICION_KEY][mo_key]['mano_obra'] += total
                continue

            # item normal
            if cat_nombre not in st.session_state[EDICION_KEY]:
                st.session_state[EDICION_KEY][cat_nombre] = {'items': [], 'mano_obra': 0.0}

            st.session_state[EDICION_KEY][cat_nombre]['items'].append({
                'id': str(uuid.uuid4()),
                'nombre': nombre_item,
                'nombre_personalizado': nombre_item,
                'unidad': item.get('unidad', 'Unidad'),
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'total': total,
                'categoria': cat_nombre,
                'notas': item.get('notas', ''),
                'posicion': len(st.session_state[EDICION_KEY][cat_nombre]['items'])
            })

        # Sincronizar con categorías
        st.session_state['categorias'] = st.session_state[EDICION_KEY]
        ensure_ids_and_positions(st.session_state['categorias'])
        
        st.success(f"✅ Presupuesto {presupuesto_id} cargado correctamente")
        return True
        
    except Exception as e:
        st.error(f"❌ Error al cargar presupuesto en sesión: {e}")
        st.exception(e)
        return False

def calcular_total_edicion(items_data: Dict[str, Any]) -> float:
    total = 0.0
    for categoria, data in items_data.items():
        total += sum(safe_numeric_value(item.get('total', 0)) for item in data.get('items', []))
        total += safe_numeric_value(data.get('mano_obra', 0.0))
    return total

def clean_price_input(text: str) -> float:
    """Limpiar input de precio: quitar puntos/moneda y devolver float seguro."""
    if text is None:
        return 0.0
    s = str(text).replace("$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(s)
    except Exception:
        try:
            return float(s.replace(",", ""))
        except Exception:
            return 0.0

# ----- CSS compacto -----
st.markdown("""
<style>
div.stTextInput, div.stNumberInput, div.stSelectbox, div.stButton {
    margin-top: -15px !important; 
    margin-bottom: 1px !important;
}
div[data-testid="column"] { padding-top: 2px !important; padding-bottom: 2px !important; }
div[data-testid="stText"] { margin-bottom: 0px !important; margin-top: 0px !important; }
</style>
""", unsafe_allow_html=True)

# ----- SELECTOR DE PRESUPUESTO -----
st.subheader("📋 Seleccionar Presupuesto para Editar")

# Obtener lista de presupuestos
presupuestos_opciones = get_presupuestos_para_selector(user_id)

if not presupuestos_opciones:
    st.warning("No tienes presupuestos para editar.")
    st.page_link("App_principal.py", label="Crear un nuevo presupuesto")
    st.stop()

# Crear selector
opciones_dict = {label: pid for pid, label in presupuestos_opciones}
presupuesto_seleccionado_label = st.selectbox(
    "Selecciona el presupuesto a editar:",
    options=list(opciones_dict.keys()),
    index=0,
    key="selector_presupuesto"
)

# Botón para cargar el presupuesto seleccionado
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Cargar Presupuesto", type="primary", use_container_width=True):
        presupuesto_id = opciones_dict[presupuesto_seleccionado_label]
        with st.spinner("Cargando presupuesto..."):
            if cargar_presupuesto_en_sesion(presupuesto_id):
                st.success(f"✅ Presupuesto ID {presupuesto_id} cargado correctamente")
                st.rerun()
            else:
                st.error("❌ Error al cargar el presupuesto")

with col2:
    st.page_link(HISTORIAL_PAGE, label="📚 Ver todos en Historial", use_container_width=True)

st.markdown("---")

# ----- VERIFICAR SI HAY PRESUPUESTO CARGADO -----
presupuesto_id = st.session_state.get('presupuesto_a_editar_id')
if not presupuesto_id:
    st.info("👆 Selecciona un presupuesto y haz clic en 'Cargar Presupuesto' para comenzar a editar.")
    st.stop()


# ----- VERIFICAR DATOS CARGADOS -----
if 'categorias' not in st.session_state or not st.session_state['categorias']:
    st.error("❌ No hay datos de presupuesto cargados. Por favor, carga un presupuesto nuevamente.")
    if st.button("🔄 Reintentar Carga"):
        if cargar_presupuesto_en_sesion(presupuesto_id):
            st.rerun()
    st.stop()

# ----- cliente / lugar / descripcion -----
try:
    clientes = get_clientes(user_id)
    lugares = get_lugares_trabajo(user_id)
except Exception as e:
    st.error(f"Error cargando clientes/lugares: {e}")
    st.exception(e)
    st.stop()
# ----- cliente / lugar / descripcion -----

cliente_id_actualizado, cliente_nombre_actualizado, \
lugar_trabajo_id_actualizado, lugar_nombre_actualizado, \
descripcion_actualizada = show_cliente_lugar_selector_edicion(
    user_id=user_id,
    cliente_inicial_id=st.session_state.get('presupuesto_cliente_id'),
    lugar_inicial_id=st.session_state.get('presupuesto_lugar_trabajo_id'),
    descripcion_inicial=st.session_state.get('presupuesto_descripcion', '')
)


# ================================
#   NUEVO ORDEN — DOS COLUMNAS
# ================================

col_izq, col_der = st.columns([1.2, 1.5])   # Ajusta proporciones si quieres

# --------------------------------
#  COLUMNA IZQUIERDA
# --------------------------------
with col_izq:
    st.subheader("📦 Agregar Ítem Nuevo")

    if st.button("➕Nueva Categoría", key="btn_nueva_categoria"):
        st.session_state["mostrar_nueva_categoria_manual"] = True

    if st.session_state.get("mostrar_nueva_categoria_manual", False):
        nueva_categoria_nombre = st.text_input("Nombre categoría", key="nombre_categoria_manual")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Guardar Categoría", key="guardar_categoria_manual"):
                if nueva_categoria_nombre:
                    if nueva_categoria_nombre not in st.session_state["categorias"]:
                        st.session_state["categorias"][nueva_categoria_nombre] = {"items": [], "mano_obra": 0.0}
                    st.success("Categoría creada.")
                    st.session_state["mostrar_nueva_categoria_manual"] = False
                    st.rerun()
                else:
                    st.warning("Ingresa un nombre.")
        with c2:
            if st.button("Cancelar", key="cancelar_categoria_manual"):
                st.session_state["mostrar_nueva_categoria_manual"] = False
                st.rerun()



    categorias_existentes = list(st.session_state["categorias"].keys())
    categoria_sel = st.selectbox("Categoría", ["(Seleccione)"] + categorias_existentes, key="cat_item_nuevo")

    col_nombre, col_unidad = st.columns(2)
    with col_nombre:
        nombre_item = st.text_input("Nombre del Ítem:", key="nombre_item_principal", placeholder="Ej: Plantas, Tierra, etc.")
    with col_unidad:
        unidad = st.selectbox(
            "Unidad:", 
            ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"], 
            key="unidad_principal"
        )
    col_cantidad, col_precio, col_total = st.columns(3)
    with col_cantidad:
        cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1, key="cantidad_principal")
    with col_precio:
        precio_input = st.text_input("Precio Unitario:", value="0", key="precio_principal", placeholder="Solo números")
        precio_unitario = clean_integer_input(precio_input)
    with col_total:
        total = cantidad * precio_unitario
        st.text_input("Total", value=f"${total:,}", disabled=True, key="total_principal")

    if st.button("Agregar Ítem", key="btn_agregar_item_nuevo"):
        if categoria_sel == "(Seleccione)":
            st.error("Debes seleccionar una categoría.")
        elif not nombre_item:
            st.error("Debes escribir un nombre para el ítem.")
        else:
            precio_val = clean_price_input(precio_input)

            nuevo_item = {
                "id": str(uuid.uuid4()),
                "nombre": nombre_item,
                "nombre_personalizado": nombre_item,
                "unidad": unidad,
                "cantidad": cantidad,
                "precio_unitario": precio_val,
                "total": precio_val * cantidad,
                "categoria": categoria_sel,
                "posicion": len(st.session_state["categorias"][categoria_sel]["items"])
            }

            st.session_state["categorias"][categoria_sel]["items"].append(nuevo_item)
            ensure_ids_and_positions(st.session_state["categorias"])
            st.success("Ítem agregado.")
            st.rerun()

    show_trabajos_simples(st.session_state["categorias"], persist_db=False)

# --------------------------------
#  COLUMNA DERECHA — DATAFRAME
# --------------------------------
with col_der:
    items_data = st.session_state["categorias"]
    total_general_actualizado = calcular_total_edicion(items_data)
    show_resumen(items_data)

st.markdown("---")

# ================================
#   EDICIÓN AVANZADA (debajo)
# ================================
st.subheader("🛠️ Edición Avanzada")

st.subheader("📋 Ítems del Presupuesto (Editable)")
items_data = show_edited_presupuesto(user_id, is_editing=True, persist_db=False)



st.markdown("---")
st.markdown(f"### 💰 Total a Guardar: **${total_general_actualizado:,.0f}**")

# ----- BOTÓN GUARDAR -----
if st.button("💾 Guardar como Nuevo Presupuesto y Generar PDF", type="primary", key="guardar_edicion_final"):
    # (Dejas tu lógica actual completa)
    st.write("Guardando…")
