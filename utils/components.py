import streamlit as st
import pandas as pd
import uuid
from functools import partial
from typing import Any, Dict, List, Tuple, Optional
# 🚨 IMPORTANTE: Asegúrate que el nombre del archivo de la DB sea 'db.py'
from utils.db import (
    create_categoria, 
    get_categorias, 
    get_clientes, 
    create_cliente, 
    get_lugares_trabajo, 
    create_lugar_trabajo
)

# ==================== UTILIDADES DE COMPONENTES ====================
def _call_db_upsert(item: Dict[str, Any]) -> None:
    try:
        from utils.db import upsert_item
        upsert_item(item)
    except Exception:
        # no hay upsert_item o falla: ignorar (estado en memoria seguirá)
        pass

def _call_db_delete(item_id: Any) -> None:
    try:
        from utils.db import delete_item
        delete_item(item_id)
    except Exception:
        pass

def _call_db_reindex(presupuesto_id: Optional[int], all_items: List[Dict[str, Any]]) -> None:
    try:
        from utils.db import reindex_items
        reindex_items(presupuesto_id, all_items)
    except Exception:
        pass

def safe_numeric_value(value):
    """Convierte un valor a float de forma segura, o devuelve 0 si falla. Útil para totales."""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0
# ----------------------------
# UTIL: asegurar ids y posicion en todas las categorias
# ----------------------------
def ensure_ids_and_positions(categorias: Dict[str, Any]) -> None:
    """
    Asegura que cada item tenga 'id' y 'posicion'. Modifica in-place.
    """
    for cat_nombre, data in categorias.items():
        items = data.setdefault('items', [])
        # Asignar IDs y posiciones si faltan
        for i, item in enumerate(items):
            if 'id' not in item:
                item['id'] = str(uuid.uuid4())
            if 'posicion' not in item:
                item['posicion'] = i
        # Ordenar por posicion
        items.sort(key=lambda it: int(it.get('posicion', 0)))

# ----------------------------
# FUNCION: agregar item normal (se llama desde UI de agregar)
# ----------------------------
def add_item_to_category(categorias: Dict[str, Any], categoria_nombre: str, nuevo_item: Dict[str, Any], persist_db: bool = False) -> None:
    """
    Inserta nuevo_item al final de la categoria y actualiza posiciones.
    nuevo_item debe contener: nombre_personalizado, unidad (o None), cantidad (or None), precio_unitario (or None), total, notas, tipo
    """
    if categoria_nombre not in categorias:
        categorias[categoria_nombre] = {'categoria_id': None, 'items': [], 'mano_obra': 0}
    items = categorias[categoria_nombre]['items']
    # asignar id y posicion
    if 'id' not in nuevo_item:
        nuevo_item['id'] = str(uuid.uuid4())
    nuevo_item['posicion'] = len(items)
    items.append(nuevo_item)
    # persistir si corresponde
    if persist_db:
        try:
            _call_db_upsert(nuevo_item)
        except Exception:
            pass

def safe_numeric_value(value: Any) -> float:
    """Convierte un valor a float de forma segura"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def clean_integer_input(value: str) -> int:
    """Limpia el input para que solo contenga números enteros"""
    if value is None:
        return 0
    cleaned = ''.join(filter(str.isdigit, str(value)))
    return int(cleaned) if cleaned else 0

def _selector_entidad(datos: List[Tuple[int, str]], label: str, key: str, btn_nuevo: str, modal_title: str, placeholder_nombre: str, funcion_creacion: callable, user_id: str, mostrar_boton: bool = True) -> Optional[int]:
    """Componente genérico para seleccionar/crear entidades con popover siempre activo."""
    
    if not user_id:
        st.error("❌ Error interno: ID de usuario no disponible.")
        return None
    
    opciones_display = ["(Seleccione)"] + [nombre for _, nombre in datos]
    
    # 1. Selector principal
    entidad_nombre_seleccionada = st.selectbox(
        label=label.capitalize(),
        options=opciones_display,
        key=f"{key}_selector",
        label_visibility="collapsed",
    )
    
    entidad_id = None
    if entidad_nombre_seleccionada and entidad_nombre_seleccionada != "(Seleccione)":
        # Buscar el ID basado en el nombre seleccionado
        entidad_id = next((id for id, nombre in datos if nombre == entidad_nombre_seleccionada), None)
    
    # 2. Popover SIEMPRE ACTIVO - sin botón para abrirlo/cerrarlo
    with st.popover(modal_title, width='stretch'):
        st.write(f"Crear nuevo {label}")
        nombre_nuevo = st.text_input(placeholder_nombre, key=f"new_{key}_name")
        
        if st.button("💾 Crear", type="primary", key=f"save_{key}", width='stretch'):
            if nombre_nuevo.strip():
                new_id = funcion_creacion(nombre=nombre_nuevo.strip(), user_id=user_id)
                if new_id:
                    st.cache_data.clear()
                    st.toast("Creado Correctamente!", icon="✅")
                    st.rerun()  # Recargar para que el nuevo item aparezca en la lista
                else:
                    st.error(f"❌ Error al crear {label}")
            else:
                st.error(f"⚠️ El nombre de {label} no puede estar vacío.")

    return entidad_id
# ==================== SECCIÓN CLIENTE - LUGAR DE TRABAJO ====================

def show_cliente_lugar_selector_edicion(user_id: str, cliente_inicial_id: int = None, 
                                      lugar_inicial_id: int = None, descripcion_inicial: str = ""):
    """
    Selector de cliente y lugar para edición - CORREGIDO sin st.modal
    """
    import streamlit as st
    from utils.db import get_clientes, get_lugares_trabajo, crear_cliente, crear_lugar_trabajo
    
    # Obtener listas actuales
    clientes = get_clientes(user_id)
    lugares = get_lugares_trabajo(user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("👤 Cliente")
        
        # Selector de cliente existente
        cliente_opciones = ["Seleccionar cliente"] + [nombre for _, nombre in clientes]
        cliente_ids = [None] + [id for id, _ in clientes]
        
        cliente_index = 0
        if cliente_inicial_id and cliente_inicial_id in cliente_ids:
            cliente_index = cliente_ids.index(cliente_inicial_id)
        
        cliente_seleccionado_nombre = st.selectbox(
            "Cliente:",
            options=cliente_opciones,
            index=cliente_index,
            key="cliente_select_edicion"
        )
        
        cliente_id_actual = cliente_ids[cliente_opciones.index(cliente_seleccionado_nombre)] if cliente_seleccionado_nombre != "Seleccionar cliente" else None
        
        # REEMPLAZAR MODAL CON POPOVER O EXPANDER
        with st.popover("➕ Crear nuevo cliente"):  # Cambia st.modal por st.popover
            st.write("**Nuevo Cliente**")
            nuevo_cliente_nombre = st.text_input("Nombre del cliente:", key="nuevo_cliente_edicion")
            if st.button("Guardar", key="guardar_cliente_nuevo"):
                if nuevo_cliente_nombre:
                    created = crear_cliente(user_id, nuevo_cliente_nombre)  # Asegúrate que se llame 'crear_cliente' no 'create_cliente'
                    if created:
                        st.success(f"Cliente '{nuevo_cliente_nombre}' creado")
                        st.rerun()
                else:
                    st.error("Ingresa un nombre para el cliente")
    
    with col2:
        st.subheader("📍 Lugar de Trabajo")
        
        # Selector de lugar existente
        lugar_opciones = ["Seleccionar lugar"] + [nombre for _, nombre in lugares]
        lugar_ids = [None] + [id for id, _ in lugares]
        
        lugar_index = 0
        if lugar_inicial_id and lugar_inicial_id in lugar_ids:
            lugar_index = lugar_ids.index(lugar_inicial_id)
        
        lugar_seleccionado_nombre = st.selectbox(
            "Lugar de trabajo:",
            options=lugar_opciones,
            index=lugar_index,
            key="lugar_select_edicion"
        )
        
        lugar_id_actual = lugar_ids[lugar_opciones.index(lugar_seleccionado_nombre)] if lugar_seleccionado_nombre != "Seleccionar lugar" else None
        
        # REEMPLAZAR MODAL CON POPOVER O EXPANDER
        with st.popover("➕ Crear nuevo lugar"):  # Cambia st.modal por st.popover
            st.write("**Nuevo Lugar de Trabajo**")
            nuevo_lugar_nombre = st.text_input("Nombre del lugar:", key="nuevo_lugar_edicion")
            if st.button("Guardar", key="guardar_lugar_nuevo"):
                if nuevo_lugar_nombre:
                    created = crear_lugar_trabajo(user_id, nuevo_lugar_nombre)
                    if created:
                        st.success(f"Lugar '{nuevo_lugar_nombre}' creado")
                        st.rerun()
                else:
                    st.error("Ingresa un nombre para el lugar")
    
    with col3:
        st.subheader("📝 Descripción")
        descripcion_actual = st.text_area(
            "Descripción del trabajo:",
            value=descripcion_inicial,
            placeholder="Describa el trabajo a realizar...",
            key="descripcion_edicion",
            height=100
        )
    
    # Obtener nombres para retornar
    cliente_nombre_actual = cliente_seleccionado_nombre if cliente_seleccionado_nombre != "Seleccionar cliente" else ""
    lugar_nombre_actual = lugar_seleccionado_nombre if lugar_seleccionado_nombre != "Seleccionar lugar" else ""
    
    return cliente_id_actual, cliente_nombre_actual, lugar_id_actual, lugar_nombre_actual, descripcion_actual

def show_cliente_lugar_selector_edicion(
    user_id: str,
    cliente_inicial_id: int,
    lugar_inicial_id: int,
    descripcion_inicial: str
):
    """Selector de cliente/lugar/descripcion adaptado para edición de presupuestos."""

    try:
        clientes = get_clientes(user_id)
        lugares = get_lugares_trabajo(user_id)
    except Exception as e:
        st.error(f"❌ Error cargando datos de entidades: {e}")
        return None, "", None, "", ""

    # Obtener nombres iniciales
    cliente_inicial_nombre = next((n for i, n in clientes if i == cliente_inicial_id), "")
    lugar_inicial_nombre = next((n for i, n in lugares if i == lugar_inicial_id), "")

    col1, col2, col3 = st.columns(3)

    # ---------------- CLIENTE ----------------
    with col1:
        st.markdown("#### 👤 Cliente")

        opciones_clientes = [n for i, n in clientes]
        # asegurar que el inicial exista en lista
        idx_cliente = opciones_clientes.index(cliente_inicial_nombre) if cliente_inicial_nombre in opciones_clientes else 0

        cliente_nombre_sel = st.selectbox(
            "Cliente",
            options=opciones_clientes,
            index=idx_cliente,
            key="edit_cliente_selector",
            label_visibility="collapsed"
        )

        cliente_id = next((i for i, n in clientes if n == cliente_nombre_sel), cliente_inicial_id)

        # Botón para nuevo cliente
        if st.button("➕ Nuevo cliente", key="btn_new_cliente"):
            with st.modal("Nuevo Cliente"):
                nuevo = st.text_input("Nombre del cliente", key="nuevo_cliente_nombre")
                if st.button("Guardar", key="guardar_cliente_nuevo"):
                    created = create_cliente(user_id, nuevo)
                    if created:
                        st.success("Cliente creado")
                        st.rerun()

    # ---------------- LUGAR ----------------
    with col2:
        st.markdown("#### 📍 Lugar de Trabajo")

        opciones_lugares = [n for i, n in lugares]
        idx_lugar = opciones_lugares.index(lugar_inicial_nombre) if lugar_inicial_nombre in opciones_lugares else 0

        lugar_nombre_sel = st.selectbox(
            "Lugar",
            options=opciones_lugares,
            index=idx_lugar,
            key="edit_lugar_selector",
            label_visibility="collapsed"
        )

        lugar_id = next((i for i, n in lugares if n == lugar_nombre_sel), lugar_inicial_id)

        # Botón para nuevo lugar
        if st.button("➕ Nuevo lugar", key="btn_new_lugar"):
            with st.modal("Nuevo Lugar de Trabajo"):
                nuevo = st.text_input("Nombre del lugar", key="nuevo_lugar_nombre")
                if st.button("Guardar", key="guardar_lugar_nuevo"):
                    created = create_lugar_trabajo(user_id, nuevo)
                    if created:
                        st.success("Lugar creado")
                        st.rerun()

    # ---------------- DESCRIPCIÓN ----------------
    with col3:
        st.markdown("#### 📝 Descripción")
        descripcion = st.text_area(
            "Trabajo a realizar",
            value=descripcion_inicial,
            key="edit_descripcion_area",
            label_visibility="collapsed",
            height=80
        )

    return (
        cliente_id,
        cliente_nombre_sel,
        lugar_id,
        lugar_nombre_sel,
        descripcion
    )


# ==================== SECCIÓN ITEMS Y CATEGORÍAS ====================
def selector_categoria(user_id: str, mostrar_label: bool = True, requerido: bool = True, key_suffix: str = "", mostrar_boton_externo: bool = False) -> Tuple[Optional[int], Optional[str], bool]:
    """
    Selector simplificado de categorías.
    """
    if not user_id:
        st.error("❌ No autenticado")
        if requerido: st.stop()
        return None, None, False

    try:
        categorias = get_categorias(user_id)
    except Exception as e:
        st.error(f"❌ Error cargando categorías: {e}")
        if requerido: st.stop()
        return None, None, False

    if mostrar_label:
        st.markdown("#### 📂 Categoría")

    # Usar _selector_entidad actualizada
    categoria_id = _selector_entidad(
        datos=categorias,
        label="categoría",  # Cambié esto para que coincida con el formato
        key=f"categoria_{key_suffix}",
        btn_nuevo="",  # No se usa ya que el popover está siempre activo
        modal_title="Nueva Categoría",
        placeholder_nombre="Nombre de la categoría",
        funcion_creacion=create_categoria,
        user_id=user_id,
        mostrar_boton=False  # No mostrar botón ya que el popover está siempre activo
    )
    
    categoria_nombre = next((n for i, n in categorias if i == categoria_id), "Sin Categoría (General)")
    
    return categoria_id, categoria_nombre, False  # Siempre devolvemos False para modal_abierto ya que no usamos esa lógica

def show_items_presupuesto(user_id: str, is_editing: bool = False, persist_db: bool = False) -> Dict[str, Any]:
    """
    Interfaz para agregar ítems (normales). Devuelve st.session_state['categorias'] actualizado.
    persist_db: intenta persistir cada ítem creado con utils.db.upsert_item si existe.
    """
    if 'categorias' not in st.session_state:
        st.session_state['categorias'] = {}

    ensure_ids_and_positions(st.session_state['categorias'])

    with st.container():
        st.markdown("#### 1️⃣ 📂 Categoría")
        # selector_categoria debe devolver (categoria_id, categoria_nombre, modal_abierto)
        categoria_id, categoria_nombre, modal_abierto = selector_categoria(
            user_id=user_id,
            mostrar_label=False,
            requerido=False,
            key_suffix="principal",
            mostrar_boton_externo=True
        )

        if not categoria_id and not modal_abierto:
            st.warning("⚠️ Selecciona o crea una categoría para agregar ítems")
            return st.session_state['categorias']

        st.markdown(f"#### 2️⃣ 📦 Agregar Ítems")
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

        if st.button("➕ Agregar Ítem", type="primary", width='stretch', key="btn_add_item_principal"):
            if not nombre_item.strip():
                st.error("❌ Nombre del ítem es requerido")
            elif not categoria_nombre or categoria_nombre == "Sin Categoría (General)":
                st.error("❌ Debe seleccionar una categoría válida")
            else:
                # construir nuevo_item en formato DB-friendly
                nuevo_item = {
                    'nombre_personalizado': nombre_item.strip(),
                    'unidad': unidad,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'total': total,
                    'categoria': categoria_nombre,
                    'categoria_id': categoria_id,
                    'notas': '',
                    'tipo': 'normal'  # normal o trabajo_simple
                }
                add_item_to_category(st.session_state['categorias'], categoria_nombre, nuevo_item, persist_db=persist_db)
                ensure_ids_and_positions(st.session_state['categorias'])
                st.success(f"✅ Ítem '{nombre_item.strip()}' agregado a '{categoria_nombre}'")
                st.rerun()

    return st.session_state['categorias']
def show_edited_presupuesto(user_id: str, is_editing: bool = False, persist_db: bool = False) -> Dict[str, Any]:
    """
    Editor avanzado (Opción A) - CORREGIDO
    """
    import math

    if 'categorias' not in st.session_state:
        st.session_state['categorias'] = {}

    ensure_ids_and_positions(st.session_state['categorias'])
    categorias_a_mostrar = [cat for cat in st.session_state['categorias'] if st.session_state['categorias'][cat]['items']]

    if not categorias_a_mostrar:
        with st.expander("📝 Editar/Eliminar Ítems", expanded=False):
            st.info("📭 No hay ítems para editar")
        return st.session_state['categorias']

    with st.expander("📝 Editar/Eliminar Ítems", expanded=True):
        categoria_options = list(st.session_state['categorias'].keys()) + ["GENERAL"]

        for cat_nombre in categoria_options:
            data = st.session_state['categorias'].get(cat_nombre)
            if not data:
                continue
            items_cat = data.get('items', [])
            if not items_cat:
                continue

            st.write(f"### {cat_nombre}")
            # encabezados
            col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([2.5,1,1.2,1.2,1.2,1,1.8,0.7])
            col_h1.write("**Descripción**"); col_h2.write("**Unidad**"); col_h3.write("**Cant.**")
            col_h4.write("**P.Unit**"); col_h5.write("**Total**"); col_h6.write("**Orden**"); col_h7.write("**Mover**"); col_h8.write("**Borrar**")

            items_cat.sort(key=lambda it: int(it.get('posicion', 0)))
            
            for idx, item in enumerate(list(items_cat)):
                if "id" not in item or item["id"] in [None, "", 0]:
                    item["id"] = str(uuid.uuid4())

                item_id = item["id"]
                
                # GENERAR UN SUFIJO ÚNICO PARA TODAS LAS KEYS
                unique_suffix = f"{cat_nombre}_{item_id}_{idx}"

                # INICIALIZACIÓN CORREGIDA DE TODOS LOS VALORES
                # --------------------------------------------------
                
                # Nombre - INICIALIZACIÓN MEJORADA
                name_key = f"name_{unique_suffix}"
                nombre_valor = item.get('nombre_personalizado') or item.get('nombre', '')
                if name_key not in st.session_state:
                    st.session_state[name_key] = nombre_valor
                elif st.session_state[name_key] != nombre_valor and nombre_valor:
                    st.session_state[name_key] = nombre_valor

                # Asegurar que el item tenga el campo 'nombre' (REQUERIDO PARA LA BD)
                if 'nombre' not in item or not item['nombre']:
                    item['nombre'] = nombre_valor  # Usar el valor existente como nombre por defecto

                # Unidad - INICIALIZACIÓN MEJORADA
                unidad_key = f"unidad_{unique_suffix}"
                unidad_valor = item.get('unidad', 'Unidad')
                if unidad_key not in st.session_state:
                    st.session_state[unidad_key] = unidad_valor
                elif st.session_state[unidad_key] != unidad_valor:
                    st.session_state[unidad_key] = unidad_valor

                # Cantidad - INICIALIZACIÓN MEJORADA
                cant_key = f"cant_{unique_suffix}"
                cant_valor = int(item.get('cantidad') or 0)
                if cant_key not in st.session_state:
                    st.session_state[cant_key] = cant_valor
                elif st.session_state[cant_key] != cant_valor:
                    st.session_state[cant_key] = cant_valor

                # Precio - INICIALIZACIÓN MEJORADA
                pre_key = f"pre_{unique_suffix}"
                pre_valor = int(item.get('precio_unitario') or 0)
                if pre_key not in st.session_state:
                    st.session_state[pre_key] = pre_valor

                # Total - INICIALIZACIÓN MEJORADA
                total_key = f"total_{unique_suffix}"
                total_valor = int(item.get('total') or 0)
                if total_key not in st.session_state:
                    st.session_state[total_key] = total_valor

                # --------------------------------------------------
                # RENDERIZADO DE COLUMNAS (igual pero con unique_suffix en todas las keys)
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2.5,1.5,1.2,1.5,1.5,0.8,0.8,0.8])

                # NOMBRE - CORREGIDO
                new_name = col1.text_input(
                    "Descripción",
                    value=st.session_state[name_key],
                    key=f"name_input_{unique_suffix}",  # USAR unique_suffix
                    label_visibility="collapsed"
                )
                if new_name != st.session_state[name_key]:
                    st.session_state[name_key] = new_name
                    item['nombre_personalizado'] = new_name
                    # Asegurar que también se actualice el campo 'nombre' requerido
                    item['nombre'] = new_name
                    if persist_db:
                        _call_db_upsert(item)

                # Si después de la edición todavía no hay nombre, establecer uno por defecto
                if not item.get('nombre') and new_name:
                    item['nombre'] = new_name
                elif not item.get('nombre'):
                    item['nombre'] = "Ítem sin nombre"  # Valor por defecto

                if item.get('tipo', 'normal') != 'trabajo_simple':
                    # UNIDAD
                    unidad_opts = ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"]
                    current_unidad = st.session_state[unidad_key]
                    new_unidad = col2.selectbox(
                        "Unidad",
                        unidad_opts,
                        index=unidad_opts.index(current_unidad) if current_unidad in unidad_opts else 2,
                        key=f"unidad_select_{unique_suffix}",  # USAR unique_suffix
                        label_visibility="collapsed"
                    )
                    if new_unidad != current_unidad:
                        st.session_state[unidad_key] = new_unidad
                        item['unidad'] = new_unidad
                        if persist_db: 
                            _call_db_upsert(item)

                    # CANTIDAD
                    new_cant = col3.number_input(
                        "Cantidad",
                        min_value=0,
                        step=1,
                        value=st.session_state[cant_key],
                        key=f"cant_input_{unique_suffix}",  # USAR unique_suffix
                        label_visibility="collapsed"
                    )
                    if new_cant != st.session_state[cant_key]:
                        st.session_state[cant_key] = new_cant
                        item['cantidad'] = int(new_cant)
                        if item.get('precio_unitario') is not None:
                            try:
                                item['total'] = int(item['cantidad']) * int(item.get('precio_unitario') or 0)
                                st.session_state[total_key] = item['total']
                            except Exception:
                                item['total'] = item.get('total', 0)
                        if persist_db: 
                            _call_db_upsert(item)

                    # PRECIO UNITARIO
                    precio_display = str(st.session_state[pre_key]) if st.session_state[pre_key] != 0 else ""
                    new_pre_str = col4.text_input(
                        "Precio Unitario",
                        value=precio_display,
                        key=f"pre_input_{unique_suffix}",  # USAR unique_suffix
                        label_visibility="collapsed"
                    )
                    try:
                        new_pre = clean_integer_input(new_pre_str)
                    except:
                        new_pre = 0
                    
                    if new_pre != st.session_state[pre_key]:
                        st.session_state[pre_key] = new_pre
                        item['precio_unitario'] = new_pre
                        item['total'] = int(item.get('cantidad') or 0) * new_pre
                        st.session_state[total_key] = item['total']
                        if persist_db: 
                            _call_db_upsert(item)

                    # TOTAL (readonly)
                    total_display = f"${int(item.get('total',0)):,}".replace(",", ".")
                    col5.text_input(
                        "Total",
                        value=total_display,
                        disabled=True,
                        key=f"total_display_{unique_suffix}",  # USAR unique_suffix
                        label_visibility="collapsed"
                    )

                else:
                    # TRABAJO SIMPLE - CORREGIDO
                    total_display = str(st.session_state[total_key]) if st.session_state[total_key] != 0 else ""
                    new_total_str = col5.text_input(
                        "Total",
                        value=total_display,
                        key=f"total_input_{unique_suffix}",  # USAR unique_suffix
                        label_visibility="collapsed"
                    )
                    try:
                        new_total = clean_integer_input(new_total_str)
                    except:
                        new_total = 0

                    if new_total != st.session_state[total_key]:
                        st.session_state[total_key] = new_total
                        item['total'] = new_total
                        if persist_db: 
                            _call_db_upsert(item)

                # reordenamiento (flechas)
                with col6:
                    # Crear dos columnas dentro de col6 para poner las flechas lado a lado
                    col_up, col_down = st.columns(2)
                    
                    with col_up:
                        if st.button("↑", key=f"up_{unique_suffix}", width='stretch'):  # USAR unique_suffix
                            # buscar lista que contiene este item
                            lista = st.session_state['categorias'][cat_nombre]['items']
                            pos = idx
                            if pos > 0:
                                # swap posiciones
                                lista[pos]['posicion'], lista[pos-1]['posicion'] = lista[pos-1].get('posicion', pos-1), lista[pos].get('posicion', pos)
                                lista[pos], lista[pos-1] = lista[pos-1], lista[pos]
                                ensure_ids_and_positions(st.session_state['categorias'])
                                # persist reindex if necesario
                                if persist_db: _call_db_reindex(None, sum((c['items'] for c in st.session_state['categorias'].values()), []))
                                st.rerun()
                    
                    with col_down:
                        if st.button("↓", key=f"down_{unique_suffix}", width='stretch'):  # USAR unique_suffix
                            lista = st.session_state['categorias'][cat_nombre]['items']
                            pos = idx
                            if pos < len(lista)-1:
                                lista[pos]['posicion'], lista[pos+1]['posicion'] = lista[pos+1].get('posicion', pos+1), lista[pos].get('posicion', pos)
                                lista[pos], lista[pos+1] = lista[pos+1], lista[pos]
                                ensure_ids_and_positions(st.session_state['categorias'])
                                if persist_db: _call_db_reindex(None, sum((c['items'] for c in st.session_state['categorias'].values()), []))
                                st.rerun()

                # mover de categoria (selectbox)
                with col7:
                    move_key = f"move_{unique_suffix}"  # USAR unique_suffix
                    # opciones: todas las categorias + GENERAL
                    opts = list(st.session_state['categorias'].keys()) + ["GENERAL"]
                    current_cat = item.get('categoria', cat_nombre)
                    # don't raise if current_cat not in opts
                    current_index = opts.index(current_cat) if current_cat in opts else 0
                    new_cat = col7.selectbox("Mover a", opts, index=current_index, key=move_key, label_visibility="collapsed")
                    if new_cat != current_cat:
                        # remover de la categoria actual e insertar al final de la nueva
                        # eliminar por id
                        try:
                            # quitar del current list
                            src_list = st.session_state['categorias'][cat_nombre]['items']
                            new_list = [it for it in src_list if it.get('id') != item_id]
                            st.session_state['categorias'][cat_nombre]['items'] = new_list
                            # actualizar item.categoria
                            item['categoria'] = new_cat
                            # si new_cat no existe, crear
                            if new_cat == "GENERAL":
                                if "GENERAL" not in st.session_state['categorias']:
                                    st.session_state['categorias']["GENERAL"] = {'categoria_id': None, 'items': [], 'mano_obra': 0}
                                dest_list = st.session_state['categorias']["GENERAL"]['items']
                            else:
                                if new_cat not in st.session_state['categorias']:
                                    st.session_state['categorias'][new_cat] = {'categoria_id': None, 'items': [], 'mano_obra': 0}
                                dest_list = st.session_state['categorias'][new_cat]['items']
                            # append and reindex positions
                            dest_list.append(item)
                            ensure_ids_and_positions(st.session_state['categorias'])
                            if persist_db:
                                _call_db_upsert(item)
                                _call_db_reindex(None, sum((c['items'] for c in st.session_state['categorias'].values()), []))
                            st.rerun()
                        except Exception:
                            st.error("Error al mover el ítem de categoría")

                # eliminar
                with col8:
                    if col8.button("❌", key=f"del_{unique_suffix}"):  # USAR unique_suffix
                        # eliminar por id de la lista actual
                        try:
                            src_list = st.session_state['categorias'][cat_nombre]['items']
                            st.session_state['categorias'][cat_nombre]['items'] = [it for it in src_list if it.get('id') != item_id]
                            if persist_db:
                                _call_db_delete(item_id)
                                _call_db_reindex(None, sum((c['items'] for c in st.session_state['categorias'].values()), []))
                            ensure_ids_and_positions(st.session_state['categorias'])
                            st.rerun()
                        except Exception:
                            st.error("No se pudo eliminar el ítem")

    return st.session_state['categorias']

def show_trabajos_simples(items_data: Dict[str, Any], persist_db: bool = False) -> None:
    """
    UI para agregar trabajos simples. Se guardan como items con unidad='Unidad', cantidad=1, precio_unitario=total, y campo es_trabajo_simple=True.
    """
    ensure_ids_and_positions(items_data)

    with st.expander("💼 Agregar Trabajo / Servicio", expanded=True):
        
        nombre_trabajo = st.text_input("Nombre del trabajo:", key="nombre_trabajo_simple")
        col1, col2 = st.columns(2)
        with col1:
            monto_input = st.text_input("Monto total ($):", key="monto_trabajo_simple")

        with col2:
            monto_trabajo = clean_integer_input(monto_input)

            categorias = list(items_data.keys())
            # permitir GENERAL
            categorias_display = categorias + ["GENERAL"]

            categoria_sel = st.selectbox("Aplicar a:", categorias_display, key="categoria_trabajo_simple")

        if st.button("📌 Agregar Trabajo", width='stretch', key="btn_add_trabajo_simple"):
            if not nombre_trabajo or monto_trabajo <= 0:
                st.warning("Debes ingresar un nombre y un monto válido.")
            else:
                target_cat = categoria_sel
                if target_cat == "GENERAL":
                    if "GENERAL" not in items_data:
                        items_data["GENERAL"] = {'categoria_id': None, 'items': [], 'mano_obra': 0}
                    target_cat = "GENERAL"

                nuevo_item = {
                    'nombre_personalizado': nombre_trabajo.strip(),
                    'unidad': 'Unidad',
                    'cantidad': 1,
                    'precio_unitario': monto_trabajo,
                    'total': monto_trabajo,
                    'categoria': target_cat,
                    'categoria_id': items_data.get(target_cat, {}).get('categoria_id'),
                    'notas': '',
                    'tipo': 'trabajo_simple',
                    'es_trabajo_simple': True
                }
                add_item_to_category(items_data, target_cat, nuevo_item, persist_db=persist_db)
                ensure_ids_and_positions(items_data)
                st.success(f"Trabajo '{nombre_trabajo}' agregado correctamente en '{target_cat}'.")
                st.rerun()

def show_resumen(items_data: Dict[str, Any]) -> float:
    """Resumen simplificado del presupuesto."""
    
    if not items_data or all(not data.get('items') for cat, data in items_data.items()):
        st.info("📭 No hay ítems agregados aún")
        return 0.0

    total_general = 0

    for cat, data in items_data.items():
        items = data.get('items', [])
        
        if items:  # Solo mostrar categorías que tienen items
            total_categoria = sum(item.get('total', 0) for item in items)
            total_general += total_categoria

            st.markdown(f"#### 🔹 {cat}")
            
            if items:
                df_items = pd.DataFrame(items)
                
                # Configuración de columnas - usar 'nombre_personalizado' o 'nombre' como "Insumo"
                column_config = {
                    "nombre_personalizado": st.column_config.TextColumn("Insumo", width="medium"),
                    "nombre": st.column_config.TextColumn("Insumo", width="medium"),
                    "unidad": st.column_config.TextColumn("Unidad", width="small"),
                    "cantidad": st.column_config.NumberColumn("Cantidad", width="small"),
                    "precio_unitario": st.column_config.NumberColumn("P. Unitario", format="$%d", width="small"),
                    "total": st.column_config.NumberColumn("Total", format="$%d", width="small")
                }
                
                # Determinar qué columna usar para "Insumo"
                if "nombre_personalizado" in df_items.columns and not df_items["nombre_personalizado"].isna().all():
                    columns_to_show = ["nombre_personalizado", "unidad", "cantidad", "precio_unitario", "total"]
                else:
                    columns_to_show = ["nombre", "unidad", "cantidad", "precio_unitario", "total"]
                
                # Filtrar solo las columnas que existen
                columns_to_show = [col for col in columns_to_show if col in df_items.columns]
                
                st.dataframe(df_items[columns_to_show], column_config=column_config, hide_index=True, width='stretch')
            
            st.markdown(f"**Total {cat}:** **${total_categoria:,}**")
            st.markdown("---")

    if total_general > 0:
        st.markdown(f"#### 💰 **TOTAL GENERAL:** **${total_general:,}**")
    
    return total_general
