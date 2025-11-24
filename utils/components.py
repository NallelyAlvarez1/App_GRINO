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

def show_cliente_lugar_selector(user_id: str) -> Tuple[Optional[int], str, Optional[int], str, str]:
    """Selector simplificado de cliente y lugar de trabajo"""
    
    if not user_id:
        st.error("❌ El ID de usuario no fue proporcionado al componente.")
        return None, "", None, "", ""
    
    try:
        clientes = get_clientes(user_id)
        lugares = get_lugares_trabajo(user_id)
    except Exception as e:
        st.error(f"❌ Error cargando datos de entidades: {e}")
        return None, "", None, "", ""

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 👤 Cliente")
        cliente_id = _selector_entidad(
            datos=clientes,
            label="cliente",
            key="cliente",
            btn_nuevo="➕ Nuevo cliente",
            modal_title="Nuevo Cliente",
            placeholder_nombre="Nombre de cliente",
            funcion_creacion=create_cliente,
            user_id=user_id  # ← Asegúrate de incluir esto
        )
        
    with col2:
        st.markdown("#### 📍 Lugar de Trabajo")
        lugar_trabajo_id = _selector_entidad(
            datos=lugares,
            label="lugar",
            key="lugar",
            btn_nuevo="➕ Nuevo lugar",
            modal_title="Nuevo Lugar de Trabajo",
            placeholder_nombre="Nombre del lugar",
            funcion_creacion=create_lugar_trabajo,
            user_id=user_id  # ← Asegúrate de incluir esto
        )
        
    with col3:
        st.markdown("#### 📝 Descripción")
        descripcion = st.text_area("Trabajo a realizar", 
                                   placeholder="Breve descripción del trabajo a realizar", 
                                   key="presupuesto_descripcion",
                                   label_visibility="collapsed",
                                   height=80)

    # Obtener nombres para el resumen o visualización
    cliente_nombre = next((n for i, n in clientes if i == cliente_id), "(No Seleccionado)")
    lugar_nombre = next((n for i, n in lugares if i == lugar_trabajo_id), "(No Seleccionado)")
    
    return cliente_id, cliente_nombre, lugar_trabajo_id, lugar_nombre, descripcion
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

def show_edited_presupuesto(user_id: str, is_editing: bool = False, persist_db: bool = True) -> Dict[str, Any]:
    """Muestra y permite editar los ítems del presupuesto cargado."""
    
    if 'categorias' not in st.session_state:
        st.error("No hay datos de presupuesto cargados.")
        return {}

    categorias = st.session_state['categorias']
    items_modificados = False

    # Obtener lista de categorías disponibles para el selector
    categorias_disponibles = [cat for cat in categorias.keys() if cat != 'general']
    
    for categoria_nombre, datos_categoria in categorias.items():
        with st.expander(f"📁 {categoria_nombre}", expanded=True):
            
            # Mostrar y editar mano de obra si existe
            mano_obra_actual = datos_categoria.get('mano_obra', 0.0)
            if mano_obra_actual > 0 or st.checkbox(f"Agregar Mano de Obra a {categoria_nombre}", 
                                                  key=f"mo_check_{categoria_nombre}"):
                nueva_mano_obra = st.number_input(
                    "Mano de Obra ($)",
                    min_value=0.0,
                    value=float(mano_obra_actual),
                    step=1000.0,
                    key=f"mo_edit_{categoria_nombre}"  # Clave única por categoría
                )
                if nueva_mano_obra != mano_obra_actual:
                    categorias[categoria_nombre]['mano_obra'] = nueva_mano_obra
                    items_modificados = True

            # Mostrar ítems existentes en tabla editable
            if datos_categoria['items']:
                st.markdown("**Ítems existentes:**")
                
                for idx, item in enumerate(datos_categoria['items']):
                    # Usar columnas para la edición en línea
                    col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 0.5])
                    
                    with col1:
                        # Clave única para cada text_input usando categoria + idx
                        new_name = col1.text_input(
                            "Descripción",
                            value=item.get('nombre_personalizado', item.get('nombre', '')),
                            key=f"name_{categoria_nombre}_{idx}_{item.get('id', '')}"
                        )
                    
                    with col2:
                        new_unidad = col2.selectbox(
                            "Unidad",
                            options=["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", 
                                    "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"],
                            index=0,
                            key=f"unit_{categoria_nombre}_{idx}_{item.get('id', '')}"
                        )
                    
                    with col3:
                        new_cantidad = col3.number_input(
                            "Cantidad",
                            min_value=1,
                            value=int(item.get('cantidad', 1)),
                            step=1,
                            key=f"qty_{categoria_nombre}_{idx}_{item.get('id', '')}"
                        )
                    
                    with col4:
                        new_precio = col4.number_input(
                            "P. Unitario",
                            min_value=0.0,
                            value=float(item.get('precio_unitario', 0.0)),
                            step=1000.0,
                            key=f"price_{categoria_nombre}_{idx}_{item.get('id', '')}"
                        )
                    
                    with col5:
                        total_item = new_cantidad * new_precio
                        col5.text_input(
                            "Total",
                            value=f"${total_item:,.0f}",
                            disabled=True,
                            key=f"total_{categoria_nombre}_{idx}_{item.get('id', '')}"
                        )
                    
                    with col6:
                        if col6.button("🗑️", 
                                     key=f"delete_{categoria_nombre}_{idx}_{item.get('id', '')}",
                                     help="Eliminar ítem"):
                            categorias[categoria_nombre]['items'].pop(idx)
                            ensure_ids_and_positions(categorias)
                            items_modificados = True
                            st.rerun()
                    
                    # Verificar si hubo cambios
                    if (new_name != item.get('nombre_personalizado', item.get('nombre', '')) or
                        new_unidad != item.get('unidad', 'Unidad') or
                        new_cantidad != item.get('cantidad', 1) or
                        new_precio != item.get('precio_unitario', 0.0)):
                        
                        categorias[categoria_nombre]['items'][idx]['nombre_personalizado'] = new_name
                        categorias[categoria_nombre]['items'][idx]['unidad'] = new_unidad
                        categorias[categoria_nombre]['items'][idx]['cantidad'] = new_cantidad
                        categorias[categoria_nombre]['items'][idx]['precio_unitario'] = new_precio
                        categorias[categoria_nombre]['items'][idx]['total'] = new_cantidad * new_precio
                        items_modificados = True

            # Opción para mover ítems a otra categoría
            if datos_categoria['items'] and categorias_disponibles:
                st.markdown("---")
                col_move, col_target = st.columns([2, 1])
                with col_move:
                    item_a_mover = st.selectbox(
                        "Mover ítem a otra categoría:",
                        options=[item.get('nombre_personalizado', item.get('nombre', '')) 
                                for item in datos_categoria['items']],
                        key=f"move_select_{categoria_nombre}"
                    )
                with col_target:
                    categoria_destino = st.selectbox(
                        "Categoría destino:",
                        options=categorias_disponibles,
                        key=f"target_cat_{categoria_nombre}"
                    )
                
                if st.button("Mover Ítem", key=f"move_btn_{categoria_nombre}"):
                    # Encontrar y mover el ítem
                    for idx, item in enumerate(datos_categoria['items']):
                        if item.get('nombre_personalizado', item.get('nombre', '')) == item_a_mover:
                            item_movido = datos_categoria['items'].pop(idx)
                            categorias[categoria_destino]['items'].append(item_movido)
                            ensure_ids_and_positions(categorias)
                            items_modificados = True
                            st.success(f"Ítem movido a {categoria_destino}")
                            st.rerun()
                            break

            # Agregar nuevo ítem a esta categoría
            st.markdown("---")
            st.markdown("**Agregar nuevo ítem:**")
            col_new_name, col_new_unit = st.columns([2, 1])
            with col_new_name:
                nuevo_item_nombre = st.text_input(
                    "Nombre del nuevo ítem",
                    key=f"new_item_name_{categoria_nombre}"
                )
            with col_new_unit:
                nuevo_item_unidad = st.selectbox(
                    "Unidad",
                    options=["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", 
                            "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"],
                    key=f"new_item_unit_{categoria_nombre}"
                )
            
            col_new_qty, col_new_price = st.columns(2)
            with col_new_qty:
                nuevo_item_cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    value=1,
                    key=f"new_item_qty_{categoria_nombre}"
                )
            with col_new_price:
                nuevo_item_precio = st.number_input(
                    "Precio unitario",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                    key=f"new_item_price_{categoria_nombre}"
                )
            
            if st.button("Agregar Ítem", key=f"add_item_{categoria_nombre}"):
                if nuevo_item_nombre:
                    nuevo_item = {
                        'id': str(uuid.uuid4()),
                        'nombre': nuevo_item_nombre,
                        'nombre_personalizado': nuevo_item_nombre,
                        'unidad': nuevo_item_unidad,
                        'cantidad': nuevo_item_cantidad,
                        'precio_unitario': nuevo_item_precio,
                        'total': nuevo_item_cantidad * nuevo_item_precio,
                        'categoria': categoria_nombre,
                        'posicion': len(categorias[categoria_nombre]['items'])
                    }
                    categorias[categoria_nombre]['items'].append(nuevo_item)
                    ensure_ids_and_positions(categorias)
                    items_modificados = True
                    st.success("Ítem agregado")
                    st.rerun()
                else:
                    st.error("El nombre del ítem es requerido")

    # Actualizar session_state si hubo cambios
    if items_modificados:
        st.session_state['categorias'] = categorias
        st.session_state['_items_modified'] = True
        if persist_db:
            st.success("✅ Cambios guardados temporalmente")

    return categorias

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
