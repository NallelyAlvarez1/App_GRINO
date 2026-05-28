import streamlit as st
from utils.db import get_supabase_client 

def check_login() -> bool:
    """Verifica si el usuario está logueado."""
    return 'user_id' in st.session_state and st.session_state.user_id is not None

def authenticate(email: str, password: str) -> bool:
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if response.user:
            refreshed = supabase.auth.get_user()
            user = refreshed.user

            st.session_state.user = user
            st.session_state.user_id = user.id
            
            metadata = response.user.user_metadata or {}
            
            # Obtiene display_name, luego full_name, o email como último recurso
            user_name = (
                metadata.get('display_name') or
                metadata.get('full_name') or
                email
            )
            
            st.session_state.usuario = user_name
            
            return True
        
        else:
            st.error("Credenciales incorrectas o usuario no confirmado.")
            return False

    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return False


def register_user(email: str, password: str, full_name: str) -> bool:
    """Registra un nuevo usuario en Supabase Auth."""
    supabase = get_supabase_client()
    try:
        # Limpiar y normalizar el email
        clean_email = email.strip().lower()
        
        response = supabase.auth.sign_up({
            "email": clean_email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "email": clean_email
                }
            }
        })
        
        if response.user:
            st.success("✅ Usuario registrado correctamente. Por favor, verifica tu email.")
            return True
        elif response.error:
            st.error(f"❌ Error al registrar: {response.error.message}")
            return False
        else:
            st.error("❌ Error desconocido al registrar usuario")
            return False
            
    except Exception as e:
        st.error(f"❌ Error en registro: {str(e)}")
        return False

def sign_out():
    """Cierra la sesión del usuario."""
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Error al cerrar sesión: {e}")
        
    # Limpiar el estado de Streamlit
    keys_to_remove = ['user', 'user_id', 'usuario', 'categorias', 'presupuesto_a_editar_id']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
            
    # Limpiar estados de expanders
    for key in list(st.session_state.keys()):
        if key.startswith('expander_toggle_'):
            del st.session_state[key]