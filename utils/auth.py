import streamlit as st
# Importamos la función de conexión nativa desde tu db.py
from utils.db import get_connection

def check_login() -> bool:
    """Verifica si el usuario está logueado en la sesión actual."""
    return 'user_id' in st.session_state and st.session_state.user_id is not None

def authenticate(email: str, password_hash: str) -> bool:
    """Autentica al usuario uniendo las columnas nombre y apellidos en PostgreSQL."""
    clean_email = email.strip().lower()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Corregido: Concatenamos 'nombre' y 'apellidos' como 'full_name'
            cur.execute(
                """SELECT uid, (nombre || ' ' || apellidos) AS full_name, email 
                   FROM usuarios 
                   WHERE lower(email) = %s AND password_hash = crypt(%s, password_hash);""",
                (clean_email, password_hash)
            )
            user_row = cur.fetchone()
            
        if user_row:
            # Seteamos el estado de sesión manteniendo la estructura original
            st.session_state.user_id = str(user_row[0])
            st.session_state.usuario = user_row[1] if user_row[1] else user_row[2]
            
            # Simulamos el objeto 'user' antiguo para compatibilidad con el front
            class MockUser:
                def __init__(self, uid, email, name):
                    self.id = uid
                    self.email = email
                    self.user_metadata = {"full_name": name, "display_name": name}
            
            st.session_state.user = MockUser(str(user_row[0]), user_row[2], user_row[1])
            return True
        else:
            st.error("Credenciales incorrectas o usuario no encontrado.")
            return False
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return False
    finally:
        conn.close()

def register_user(email: str, password_hash: str, full_name: str) -> bool:
    """Registra un usuario dividiendo el full_name en nombre y apellidos para la tabla."""
    clean_email = email.strip().lower()
    
    # Separar inteligentemente el nombre completo en nombre y apellidos
    parts = full_name.strip().split(" ", 1)
    nombre = parts[0]
    apellidos = parts[1] if len(parts) > 1 else ""

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar si el correo ya existe
            cur.execute("SELECT uid FROM usuarios WHERE lower(email) = %s;", (clean_email,))
            if cur.fetchone():
                st.error("❌ El correo electrónico ya está registrado.")
                return False
            
            # Insertar el registro usando tus columnas nativas: nombre y apellidos
            cur.execute(
                """INSERT INTO usuarios (email, password_hash, nombre, apellidos) 
                   VALUES (%s, crypt(%s, gen_salt('bf', 8)), %s, %s) RETURNING uid;""",
                (clean_email, password_hash, nombre, apellidos)
            )
            nuevo_id = cur.fetchone()
            conn.commit()
            
        if nuevo_id:
            st.success("✅ Usuario registrado correctamente. Ya puedes iniciar sesión.")
            return True
        else:
            st.error("❌ Error desconocido al registrar usuario")
            return False
    except Exception as e:
        if conn: conn.rollback()
        st.error(f"❌ Error en registro: {str(e)}")
        return False
    finally:
        conn.close()

def sign_out():
    """Cierra la sesión del usuario limpiando de manera segura el st.session_state."""
    keys_to_remove = ['user', 'user_id', 'usuario', 'categorias', 'presupuesto_a_editar_id', 'items_data', 'trabajos_simples']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
            
    st.rerun()