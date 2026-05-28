import streamlit as st
import time
from utils.db import get_connection
from utils.auth import check_login, sign_out

st.set_page_config(page_title="Perfil", page_icon="🌱", layout="centered")

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'usuario' not in st.session_state:
    st.session_state.usuario = "Invitado"

# ----- autenticación -----
is_logged_in = check_login()
if not is_logged_in:
    st.error("🔒 No has iniciado sesión. Serás redirigido al inicio en 5 segundos...")
    progress_bar = st.progress(0)
    for percent_complete in range(100):
        time.sleep(0.05)
        progress_bar.progress(percent_complete + 1)
    st.switch_page("App_principal.py")
    st.stop()


# ------------------- Contenido Principal de la App -------------------
if is_logged_in:
    supabase = get_connection()

    with st.sidebar:
        st.markdown("**👤 Usuario:**")
        st.markdown(f"`{st.session_state.usuario}`")

        if st.button("🚪 Cerrar Sesión", type="primary", width='stretch'):
            sign_out()
            st.toast("Sesión cerrada correctamente", icon="🌱")
            st.rerun()
        st.divider()

supabase = get_connection()
user = st.session_state.user
metadata = user.user_metadata or {}



# ----------------------------- TÍTULO -----------------------------
st.title("⚙️ Panel de Perfil del Usuario")
st.write("Administra tu información personal y cuenta.")

# ============================= FORM 1: DATOS BÁSICOS =============================
st.subheader("📝 Datos personales", divider="green")

with st.form("form_datos"):
    nombre = st.text_input("Nombre completo", metadata.get("display_name", ""))
    telefono = st.text_input("Número de teléfono", metadata.get("phone", ""))

    if st.form_submit_button("💾 Guardar cambios", type="primary"):
        try:
            supabase.auth.update_user({
                "data": {
                    "display_name": nombre,
                    "phone": telefono
                }
            })
            st.success("Datos actualizados correctamente.")
            st.session_state.user.user_metadata["display_name"] = nombre
            st.session_state.user.user_metadata["phone"] = telefono
            st.rerun()
        except Exception as e:
            st.error(f"Error al actualizar: {e}")

# ============================= FORM 2: CAMBIAR EMAIL =============================
st.subheader("📧 Cambiar email", divider="green")

with st.form("form_email"):
    new_email = st.text_input("Nuevo correo", user.email)

    if st.form_submit_button("✉️ Actualizar correo"):
        try:
            supabase.auth.update_user({"email": new_email})
            st.success("Correo actualizado. Debes verificarlo desde tu bandeja de entrada.")
        except Exception as e:
            st.error(f"Error al actualizar email: {e}")

# ============================= FORM 3: CAMBIAR CONTRASEÑA =============================
st.subheader("🔐 Cambiar contraseña", divider="green")

with st.form("form_pass"):
    nueva_pass = st.text_input("Nueva contraseña", type="password")
    confirmar_pass = st.text_input("Confirmar contraseña", type="password")

    if st.form_submit_button("🔑 Actualizar contraseña"):
        if nueva_pass != confirmar_pass:
            st.error("Las contraseñas no coinciden.")
        else:
            try:
                supabase.auth.update_user({"password": nueva_pass})
                st.success("Contraseña actualizada correctamente.")
            except Exception as e:
                st.error(f"Error: {e}")

# ============================= ELIMINAR CUENTA =============================
st.subheader("🗑️ Eliminar cuenta", divider="red")

st.warning("Esta acción es irreversible. Se eliminará tu cuenta y todos tus datos asociados.")

if st.button("❌ Eliminar mi cuenta"):
    st.error("La eliminación directa requiere una función en Supabase Edge.")
    st.info("Te puedo generar el endpoint y el código para hacerlo. Solo dímelo.")
