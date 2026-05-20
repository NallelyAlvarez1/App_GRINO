import streamlit as st
import uuid
import time
from utils.auth import check_login, sign_out
from utils.db import (
    get_clientes, create_cliente,
    get_lugares_trabajo, create_lugar_trabajo,
    delete_cliente, delete_lugar_trabajo,
    update_cliente, update_lugar_trabajo,
    get_presupuestos_por_cliente,
    get_presupuestos_por_lugar
)
from datetime import datetime

# ------------------ ESTILOS ------------------
st.markdown("""
<style>
.stTextInput, .stNumberInput, .stSelectbox, .stButton {
    margin-bottom: -0.3rem;
    margin-top: -0.4rem;
}
h2, h3, h4 {
    margin-top: 0.4rem !important;
    margin-bottom: 0.4rem !important;
    padding-top: 0.4rem !important;
    padding-bottom: 0.4rem !important;
}
.uniform-card {
    min-height: 180px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Clientes", page_icon="🌱", layout="wide")

# ------------------ LOGIN ------------------
is_logged_in = check_login()

if not is_logged_in:
    st.error("🔒 No has iniciado sesión. Serás redirigido al inicio en 5 segundos...")
    progress_bar = st.progress(0)
    for percent_complete in range(100):
        time.sleep(0.05)
        progress_bar.progress(percent_complete + 1)
    st.switch_page("App_principal.py")
    st.stop()

user_id = st.session_state.get('user_id')
if not user_id:
    st.error("❌ Error: No se pudo identificar al usuario.")
    st.stop()

with st.sidebar:
    st.markdown("**👤 Usuario:**")
    st.markdown(f"`{st.session_state.usuario}`")

    if st.button("🚪 Cerrar Sesión", type="primary", width='stretch'):
        sign_out()
        st.toast("Sesión cerrada correctamente", icon="🌱")
        st.rerun()

# ------------------ PESTAÑAS ------------------
tab1, tab2 = st.tabs(["👥 Gestión de Clientes", "📍 Gestión de Lugares de Trabajo"])

# =========================================================
# ---------------------- CLIENTES -------------------------
# =========================================================
with tab1:
    st.subheader("👥 Gestión de Clientes")
    st.info("💡 **Nota:** Al eliminar un **CLIENTE** se eliminarán **TODOS** los presupuestos asociados automáticamente.")

    col1, col2 = st.columns([3, 1])
    with col1:
        busqueda_cliente = st.text_input("🔍 Buscar cliente:", placeholder="Escribe para filtrar clientes...", key="buscar_cliente")
    with col2:
        if st.button("➕ Nuevo Cliente", width='stretch', key="btn_nuevo_cliente"):
            st.session_state.creando_cliente = True

    try:
        clientes = get_clientes(user_id)

        if not clientes:
            st.info("📭 No hay clientes registrados. Crea tu primer cliente.")
        else:
            clientes_filtrados = [
                (id, nombre) for id, nombre in clientes
                if not busqueda_cliente or busqueda_cliente.lower() in nombre.lower()
            ]

            if not clientes_filtrados:
                st.warning("🔍 No se encontraron clientes con ese criterio de búsqueda.")
            else:
                num_clientes = len(clientes_filtrados)
                num_filas = (num_clientes + 3) // 4

                for fila in range(num_filas):
                    cols = st.columns(4)
                    inicio, fin = fila * 4, fila * 4 + 4

                    for idx, (cliente_id, cliente_nombre) in enumerate(clientes_filtrados[inicio:fin]):
                        with cols[idx]:
                            with st.container(border=True):
                                inicial = cliente_nombre[0].upper() if cliente_nombre else "?"
                                st.markdown(
                                    f"<div style='text-align:center;'><div style='width:60px;height:60px;background:#4e8cff;color:white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold'>{inicial}</div></div>",
                                    unsafe_allow_html=True
                                )
                                st.markdown(
                                    f"<h4 style='text-align:center;margin:5px 0'>{cliente_nombre}</h4>",
                                    unsafe_allow_html=True
                                )

                                col_btn1, col_btn2 = st.columns(2)

                                # ---- Botón Editar ----
                                with col_btn1:
                                    if st.button("✏️ Editar", key=f"edit_cliente_{cliente_id}", width='stretch'):
                                        st.session_state.editando_cliente_id = cliente_id
                                        st.session_state.editando_cliente_nombre = cliente_nombre

                                # ---- Botón Borrar ----
                                with col_btn2:
                                    if st.button("🗑️ Borrar", key=f"del_cliente_{cliente_id}", width='stretch', type="secondary"):
                                        st.session_state.eliminando_cliente_id = cliente_id
                                        st.session_state.eliminando_cliente_nombre = cliente_nombre

                                # =============== POPOVER EDITAR CLIENTE ===============
                                if st.session_state.get("editando_cliente_id") == cliente_id:
                                    with st.popover(f"✏️ Editar Cliente: {cliente_nombre}", use_container_width=True):
                                        nuevo_nombre = st.text_input(
                                            "Nuevo nombre:",
                                            value=st.session_state.editando_cliente_nombre,
                                            key=f"edit_cliente_input_{cliente_id}"
                                        )
                                        col1, col2 = st.columns(2)

                                        with col1:
                                            if st.button("💾 Guardar", key=f"guardar_edicion_cliente_{cliente_id}"):
                                                if update_cliente(cliente_id, nuevo_nombre, user_id):
                                                    st.success("✅ Cliente actualizado correctamente!")
                                                    st.cache_data.clear()
                                                del st.session_state.editando_cliente_id
                                                del st.session_state.editando_cliente_nombre
                                                st.rerun()

                                        with col2:
                                            if st.button("❌ Cancelar", key=f"cancelar_edicion_cliente_{cliente_id}"):
                                                del st.session_state.editando_cliente_id
                                                del st.session_state.editando_cliente_nombre
                                                st.rerun()

                                # =============== POPOVER ELIMINAR CLIENTE ===============
                                if st.session_state.get("eliminando_cliente_id") == cliente_id:
                                    with st.popover(f"🗑️ Eliminar Cliente: {cliente_nombre}", use_container_width=True):
                                        st.markdown(
                                            f"<h3 style='text-align:center; margin-bottom:5px;'>Cliente: {cliente_nombre}</h3>",
                                            unsafe_allow_html=True
                                        )
                                        st.warning("⚠️ Esta acción eliminará el cliente y todos los presupuestos asociados. ¡No se puede deshacer!")

                                        try:
                                            presupuestos = get_presupuestos_por_cliente(cliente_id)
                                        except:
                                            presupuestos = []

                                        if presupuestos:
                                            st.markdown("**Presupuestos asociados:**")
                                            for p in presupuestos:
                                                descripcion = p.get("descripcion", "Sin descripción")
                                                fecha = p.get("fecha_creacion", "")
                                                total = p.get("total", "")

                                                st.markdown(f"- **{descripcion}** — {fecha} — Total: ${total}")

                                        else:
                                            st.info("No hay presupuestos asociados.")

                                        col1, col2 = st.columns(2)

                                        # Confirmar eliminación
                                        with col1:
                                            if st.button("✅ Confirmar", key=f"confirmar_eliminar_cliente_{cliente_id}"):
                                                delete_cliente(cliente_id, user_id)
                                                st.success(f"Cliente **{cliente_nombre}** eliminado correctamente")

                                                for k in ["eliminando_cliente_id", "eliminando_cliente_nombre"]:
                                                    if k in st.session_state:
                                                        del st.session_state[k]

                                                st.cache_data.clear()
                                                st.rerun()

                                        # Cancelar eliminación
                                        with col2:
                                            if st.button("❌ Cancelar", key=f"cancelar_eliminar_cliente_{cliente_id}"):
                                                for k in ["eliminando_cliente_id", "eliminando_cliente_nombre"]:
                                                    if k in st.session_state:
                                                        del st.session_state[k]
                                                st.rerun()

    except Exception as e:
        st.error(f"❌ Error al cargar clientes: {e}")

    # ------------------ CREAR CLIENTE ------------------
    if st.session_state.get('creando_cliente', False):
        with st.popover("➕ Crear Nuevo Cliente", use_container_width=True):
            nombre_cliente = st.text_input("Nombre del cliente:", placeholder="Ej: Juan Pérez", key="nuevo_cliente_nombre")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Crear Cliente", key="crear_cliente_btn"):
                    if nombre_cliente.strip():
                        try:
                            create_cliente(nombre_cliente.strip(), user_id)
                            st.success(f"✅ Cliente '{nombre_cliente}' creado correctamente!")
                            st.session_state.creando_cliente = False
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al crear cliente: {e}")
                    else:
                        st.error("❌ El nombre del cliente es requerido")

            with col2:
                if st.button("❌ Cancelar", key="cancelar_cliente_btn"):
                    st.session_state.creando_cliente = False
                    st.rerun()

# =========================================================
# ---------------------- LUGARES --------------------------
# =========================================================
with tab2:
    st.subheader("📍 Gestión de Lugares de Trabajo")
    st.info("💡 **Nota:** Al eliminar un **LUGAR DE TRABAJO** se eliminarán **TODOS** los presupuestos asociados automáticamente.")

    col1, col2 = st.columns([3, 1])

    with col1:
        busqueda_lugar = st.text_input("🔍 Buscar lugar:", placeholder="Escribe para filtrar lugares...", key="busqueda_lugar")

    with col2:
        if st.button("➕ Nuevo Lugar", width='stretch', key="btn_nuevo_lugar"):
            st.session_state.creando_lugar = True

    try:
        lugares = get_lugares_trabajo(user_id)

        if not lugares:
            st.info("📭 No hay lugares de trabajo registrados.")
        else:
            lugares_filtrados = [
                (id, nombre) for id, nombre in lugares
                if not busqueda_lugar or busqueda_lugar.lower() in nombre.lower()
            ]

            cols = st.columns(2)

            for i, (lugar_id, lugar_nombre) in enumerate(lugares_filtrados):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.write(f"**{lugar_nombre}**")

                        col_btn1, col_btn2 = st.columns(2)

                        # Editar
                        with col_btn1:
                            if st.button("✏️ Editar", key=f"edit_lugar_{lugar_id}", width='stretch'):
                                st.session_state.editando_lugar_id = lugar_id
                                st.session_state.editando_lugar_nombre = lugar_nombre

                        # Eliminar
                        with col_btn2:
                            if st.button("🗑️ Eliminar", key=f"del_lugar_{lugar_id}", width='stretch'):
                                st.session_state.eliminando_lugar_id = lugar_id
                                st.session_state.eliminando_lugar_nombre = lugar_nombre

                        # -------- POPOVER EDITAR LUGAR --------
                        if st.session_state.get("editando_lugar_id") == lugar_id:
                            with st.popover(f"✏️ Editar Lugar: {lugar_nombre}", use_container_width=True):
                                nuevo_nombre = st.text_input(
                                    "Nuevo nombre:",
                                    value=st.session_state.editando_lugar_nombre,
                                    key=f"edit_lugar_input_{lugar_id}"
                                )

                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button("💾 Guardar", key=f"guardar_edicion_lugar_{lugar_id}"):
                                        update_lugar_trabajo(lugar_id, nuevo_nombre, user_id)
                                        st.success("Lugar actualizado correctamente!")
                                        st.cache_data.clear()
                                        del st.session_state.editando_lugar_id
                                        del st.session_state.editando_lugar_nombre
                                        st.rerun()

                                with col2:
                                    if st.button("❌ Cancelar", key=f"cancelar_edicion_lugar_{lugar_id}"):
                                        del st.session_state.editando_lugar_id
                                        del st.session_state.editando_lugar_nombre
                                        st.rerun()

                        # -------- POPOVER ELIMINAR LUGAR --------
                        if st.session_state.get("eliminando_lugar_id") == lugar_id:
                            with st.popover(f"🗑️ Eliminar Lugar: {lugar_nombre}", use_container_width=True):
                                st.error(f"Se eliminará el lugar **{lugar_nombre}** junto con todos los presupuestos asociados.")
                                st.warning("Esta acción NO se puede deshacer.")
                                presupuestos = get_presupuestos_por_lugar(lugar_id)

                                if presupuestos:
                                    st.markdown("**Presupuestos asociados:**")
                                    for p in presupuestos:
                                        st.markdown(
                                            f"- **{p.get('descripcion', 'Sin descripción')}** — {p.get('fecha_creacion', '')} — Total: ${p.get('total', 0)}"
                                        )
                                else:
                                    st.info("No hay presupuestos asociados.")


                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button("✅ Confirmar", key=f"confirmar_eliminar_lugar_{lugar_id}"):
                                        delete_lugar_trabajo(lugar_id, user_id)

                                        for k in ["eliminando_lugar_id", "eliminando_lugar_nombre"]:
                                            if k in st.session_state:
                                                del st.session_state[k]

                                        st.cache_data.clear()
                                        st.rerun()

                                with col2:
                                    if st.button("❌ Cancelar", key=f"cancelar_eliminar_lugar_{lugar_id}"):
                                        for k in ["eliminando_lugar_id", "eliminando_lugar_nombre"]:
                                            if k in st.session_state:
                                                del st.session_state[k]
                                        st.rerun()

    except Exception as e:
        st.error(f"❌ Error al cargar lugares: {e}")

    # ------------------ CREAR LUGAR ------------------
    if st.session_state.get('creando_lugar', False):
        with st.popover("➕ Crear Nuevo Lugar", use_container_width=True):
            nombre_lugar = st.text_input("Nombre del lugar:", placeholder="Ej: Casa Central, Jardín Principal", key="nuevo_lugar_nombre2")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Crear Lugar", key="crear_lugar_btn"):
                    if nombre_lugar.strip():
                        try:
                            create_lugar_trabajo(nombre_lugar.strip(), user_id)
                            st.success(f"Lugar '{nombre_lugar}' creado correctamente!")
                            st.session_state.creando_lugar = False
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear lugar: {e}")
                    else:
                        st.error("❌ El nombre del lugar es requerido")

            with col2:
                if st.button("❌ Cancelar", key="cancelar_lugar_btn"):
                    st.session_state.creando_lugar = False
                    st.rerun()