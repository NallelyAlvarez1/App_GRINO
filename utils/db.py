import streamlit as st
<<<<<<< HEAD
from supabase import create_client, Client
=======
import psycopg2
from psycopg2.extras import RealDictCursor
>>>>>>> parent of 9fc908a (Update db.py)
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple



# =================================================================
# FUNCIÓN DE INICIACIÓN DE BASE DE DATOS Y CACHÉ
# =================================================================

<<<<<<< HEAD
def initialize_supabase_client(secrets: dict) -> Client:
    try:
        SUPABASE_URL = secrets["supabase"]["url"]
        SUPABASE_KEY = secrets["supabase"]["key"]
    except KeyError as e:
        st.error(f"Error de configuración: Falta la clave de Supabase en `st.secrets`: {e}") 
        st.stop()

    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Error de configuración: Las URL o KEY de Supabase están vacías.") 
        st.stop()

    return create_client(SUPABASE_URL, SUPABASE_KEY)
@st.cache_resource 
def get_supabase_client() -> Client:
    """Devuelve la instancia del cliente Supabase, cacheada globalmente."""
    return initialize_supabase_client(st.secrets)
=======
def initialize_supabase_client(secrets: dict):
    """
    Crea y devuelve una conexión activa a la base de datos Neon usando psycopg2.
    Se mantiene el nombre original de la función para no romper compatibilidad.
    """
    try:
        host = secrets["DB_HOST"]
        database = secrets["DB_NAME"]
        user = secrets["DB_USER"]
        password = secrets["DB_PASSWORD"]
    except KeyError as e:
        st.error(f"Error de configuración: Falta la clave de Neon en `st.secrets`: {e}") 
        st.stop()

    if not host or not database or not user or not password:
        st.error("Error de configuración: Los datos de conexión a la base de datos están vacíos.") 
        st.stop()

    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            sslmode="require"
        )
        return conn
    except Exception as e:
        st.error(f"Error crítico al conectar a Neon: {e}")
        st.stop()

@st.cache_resource 
def get_supabase_client():
    """
    Devuelve la instancia de la conexión a la base de datos.
    Nota: Con psycopg2 se recomienda abrir/cerrar conexiones por consulta,
    pero mantendremos esta función como generadora base para compatibilidad.
    """
    return initialize_supabase_client(st.secrets)

def _get_connection():
    """Función utilitaria interna para asegurar conexiones frescas si la cacheada se cierra."""
    try:
        conn = get_supabase_client()
        if conn.closed:
            st.cache_resource.clear()
            conn = get_supabase_client()
        return conn
    except Exception:
        return initialize_supabase_client(st.secrets)
>>>>>>> parent of 9fc908a (Update db.py)

# =================================================================
# LECTURA DE ENTIDADES (CACHÉ)
# =================================================================

@st.cache_data(ttl=600)
def get_clientes(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de clientes (id, nombre) del usuario logueado."""
<<<<<<< HEAD
    supabase = get_supabase_client()
    try:
        response = supabase.from_('clientes').select('id, nombre').eq('creado_por', user_id).order('nombre', desc=False).execute()
        if response and response.data:
            return [(c['id'], c['nombre']) for c in response.data]
        return []
=======
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM clientes WHERE creado_por = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            rows = cur.fetchall()
            return [(row[0], row[1]) for row in rows]
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al obtener clientes: {e}")
        return []

@st.cache_data(ttl=600)
def get_lugares_trabajo(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de lugares de trabajo (id, nombre) del usuario logueado."""
<<<<<<< HEAD
    supabase = get_supabase_client()
    try:
        response = supabase.from_('lugares_trabajo').select('id, nombre').eq('creado_por', user_id).order('nombre', desc=False).execute()
        if response and response.data:
            return [(l['id'], l['nombre']) for l in response.data]
        return []
=======
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM lugares_trabajo WHERE creado_por = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            rows = cur.fetchall()
            return [(row[0], row[1]) for row in rows]
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al obtener lugares de trabajo: {e}")
        return []

@st.cache_data(ttl=600)
def get_categorias(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de categorías (id, nombre) del usuario logueado."""
<<<<<<< HEAD
    supabase = get_supabase_client()
    try:
        response = supabase.from_('categorias').select('id, nombre').eq('creado_por', user_id).order('nombre', desc=False).execute()
        if response.data:
            return [(d['id'], d['nombre']) for d in response.data]
        return []
=======
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM categorias WHERE creado_por = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            rows = cur.fetchall()
            return [(row[0], row[1]) for row in rows]
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

# =================================================================
# GESTIÓN DE ENTIDADES
# =================================================================

def create_cliente(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo cliente para el usuario."""
<<<<<<< HEAD
    supabase = get_supabase_client()
=======
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        alias_base = nombre.strip().lower().replace(' ', '_')[:45]
        alias = alias_base
        counter = 1
        
<<<<<<< HEAD
        while True:
            existing = supabase.table('clientes').select('id').eq('alias', alias).execute()
            
            if not existing.data:
                break 
            alias = f"{alias_base}_{counter}"
            counter += 1
            
            if counter > 100:
                st.error("No se pudo generar un alias único después de 100 intentos")
                return None

        response = supabase.table('clientes').insert({
            'nombre': nombre,
            'alias': alias,
            'creado_por': user_id
        }).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        else:
            st.error("No se recibió data al crear el cliente.")
            return None
=======
        with conn.cursor() as cur:
            while True:
                cur.execute("SELECT id FROM clientes WHERE alias = %s;", (alias,))
                if not cur.fetchone():
                    break 
                alias = f"{alias_base}_{counter}"
                counter += 1
                
                if counter > 100:
                    st.error("No se pudo generar un alias único después de 100 intentos")
                    return None

            cur.execute(
                "INSERT INTO clientes (nombre, alias, creado_por) VALUES (%s, %s, %s) RETURNING id;",
                (nombre, alias, user_id)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al crear cliente: {e}")
        if '23505' in str(e) and 'clientes_pkey' in str(e):
            st.error("⚠️ Error de secuencia: Contacta al administrador para resetear la secuencia de IDs de clientes")
        return None

def create_lugar_trabajo(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo lugar de trabajo para el usuario."""
<<<<<<< HEAD
    supabase = get_supabase_client()
=======
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        nombre_base = nombre.strip()
        nombre_final = nombre_base
        counter = 1
        
<<<<<<< HEAD
        while True:
            existing = supabase.table('lugares_trabajo').select('id').eq('nombre', nombre_final).execute()
            
            if not existing.data:
                break
                
            nombre_final = f"{nombre_base}_{counter}"
            counter += 1
            
            if counter > 100:
                st.error("No se pudo generar un nombre único después de 100 intentos")
                return None

        response = supabase.table('lugares_trabajo').insert({
            'nombre': nombre_final,
            'creado_por': user_id
        }).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        else:
            st.error("No se recibió data al crear el lugar de trabajo.")
            return None
=======
        with conn.cursor() as cur:
            while True:
                cur.execute("SELECT id FROM lugares_trabajo WHERE nombre = %s;", (nombre_final,))
                if not cur.fetchone():
                    break
                    
                nombre_final = f"{nombre_base}_{counter}"
                counter += 1
                
                if counter > 100:
                    st.error("No se pudo generar un nombre único después de 100 intentos")
                    return None

            cur.execute(
                "INSERT INTO lugares_trabajo (nombre, creado_por) VALUES (%s, %s) RETURNING id;",
                (nombre_final, user_id)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al crear lugar de trabajo: {e}")
        if '23505' in str(e) and 'lugares_trabajo_pkey' in str(e):
            st.error("⚠️ Error de secuencia: La secuencia de IDs de lugares de trabajo está desincronizada")
        return None

def create_categoria(nombre: str, user_id: str) -> Optional[int]:
    """Crea una nueva categoría para el usuario."""
<<<<<<< HEAD
    supabase = get_supabase_client()
    try:
        # Verificar si la categoría ya existe
        existing = supabase.table("categorias").select("id").eq("nombre", nombre).eq("creado_por", user_id).execute()
        
        if existing.data:
            st.error("❌ Ya existe una categoría con ese nombre")
            return None

        response = supabase.table("categorias").insert({
            "nombre": nombre,
            "creado_por": user_id
        }).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        else:
            st.error("No se recibió data al crear la categoría.")
            return None
=======
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar si la categoría ya existe
            cur.execute("SELECT id FROM categorias WHERE nombre = %s AND creado_por = %s;", (nombre, user_id))
            if cur.fetchone():
                st.error("❌ Ya existe una categoría con ese nombre")
                return None

            cur.execute(
                "INSERT INTO categorias (nombre, creado_por) VALUES (%s, %s) RETURNING id;",
                (nombre, user_id)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al crear categoría: {e}")
        return None

def update_cliente(cliente_id: int, nuevo_nombre: str, user_id: str) -> bool:
    """Actualiza el nombre de un cliente existente"""
<<<<<<< HEAD
    supabase = get_supabase_client()
=======
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        response = supabase.from_('clientes').update({'nombre': nuevo_nombre})\
            .eq('id', cliente_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al actualizar cliente: {e}")
        return False

def delete_cliente(cliente_id: int, user_id: str) -> bool:
<<<<<<< HEAD
    """
    Elimina un cliente junto con todos sus presupuestos e items asociados
    (gracias a ON DELETE CASCADE en la base de datos).
    """
    supabase = get_supabase_client()
=======
    """Elimina un cliente junto con todos sus presupuestos e items asociados (CASCADE)."""
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        response = supabase.from_('clientes').delete()\
            .eq('id', cliente_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al eliminar cliente: {e}")
        return False

def update_lugar_trabajo(lugar_id: int, nuevo_nombre: str, user_id: str) -> bool:
    """Actualiza el nombre de un lugar de trabajo existente"""
<<<<<<< HEAD
    supabase = get_supabase_client()
=======
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        response = supabase.from_('lugares_trabajo').update({'nombre': nuevo_nombre})\
            .eq('id', lugar_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al actualizar lugar de trabajo: {e}")
        return False

def delete_lugar_trabajo(lugar_id: int, user_id: str) -> bool:
<<<<<<< HEAD
    """
    Elimina un lugar de trabajo junto con todos sus presupuestos e items asociados
    (gracias a ON DELETE CASCADE en la base de datos).
    """
    supabase = get_supabase_client()
=======
    """Elimina un lugar de trabajo junto con todos sus presupuestos e items asociados (CASCADE)."""
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        response = supabase.from_('lugares_trabajo').delete()\
            .eq('id', lugar_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al eliminar lugar de trabajo: {e}")
        return False

def get_presupuestos_por_cliente(cliente_id: int) -> list[dict]:
<<<<<<< HEAD
    """
    Retorna los presupuestos asociados a un cliente,
    incluyendo descripción y fecha de creación.
    """
    supabase = get_supabase_client()

    try:
        data = supabase.table("presupuestos") \
            .select("id, descripcion, fecha_creacion, total") \
            .eq("cliente_id", cliente_id) \
            .execute()

        resultados = data.data or []

        # Formatear la fecha
        for p in resultados:
            if p.get("fecha_creacion"):
                try:
                    p["fecha_creacion"] = datetime.fromisoformat(
                        p["fecha_creacion"]
                    ).strftime("%d/%m/%Y")
                except:
                    pass

        return resultados

=======
    """Retorna los presupuestos asociados a un cliente."""
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, descripcion, fecha_creacion, total FROM presupuestos WHERE cliente_id = %s;",
                (cliente_id,)
            )
            resultados = cur.fetchall()
            
            for p in resultados:
                if p.get("fecha_creacion"):
                    try:
                        if isinstance(p["fecha_creacion"], str):
                            p["fecha_creacion"] = datetime.fromisoformat(p["fecha_creacion"]).strftime("%d/%m/%Y")
                        else:
                            p["fecha_creacion"] = p["fecha_creacion"].strftime("%d/%m/%Y")
                    except:
                        pass
            return resultados
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        print(f"Error al obtener presupuestos del cliente {cliente_id}: {e}")
        return []

def get_presupuestos_por_lugar(lugar_id: int) -> list[dict]:
<<<<<<< HEAD
    """
    Devuelve una lista de presupuestos asociados a un lugar de trabajo.
    Cada presupuesto incluye: id, descripcion, fecha_creacion, total.
    """
    supabase = get_supabase_client()

    try:
        data = supabase.table("presupuestos") \
            .select("id, descripcion, fecha_creacion, total") \
            .eq("lugar_trabajo_id", lugar_id) \
            .execute()

        resultados = data.data or []

        # Formatear la fecha
        for p in resultados:
            if p.get("fecha_creacion"):
                try:
                    p["fecha_creacion"] = datetime.fromisoformat(
                        p["fecha_creacion"]
                    ).strftime("%d/%m/%Y")
                except:
                    pass

        return resultados

=======
    """Devuelve una lista de presupuestos asociados a un lugar de trabajo."""
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, descripcion, fecha_creacion, total FROM presupuestos WHERE lugar_trabajo_id = %s;",
                (lugar_id,)
            )
            resultados = cur.fetchall()
            
            for p in resultados:
                if p.get("fecha_creacion"):
                    try:
                        if isinstance(p["fecha_creacion"], str):
                            p["fecha_creacion"] = datetime.fromisoformat(p["fecha_creacion"]).strftime("%d/%m/%Y")
                        else:
                            p["fecha_creacion"] = p["fecha_creacion"].strftime("%d/%m/%Y")
                    except:
                        pass
            return resultados
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        print(f"Error al obtener presupuestos del lugar {lugar_id}: {e}")
        return []

# =================================================================
# GESTIÓN DE PRESUPUESTOS
# =================================================================

def get_presupuestos_usuario(user_id: str, filtros: dict) -> list:
<<<<<<< HEAD
    """
    Obtiene los presupuestos del usuario con filtros aplicados.
    """
    supabase = get_supabase_client()
    
    # QUITAR 'version' del SELECT - solo usar 'notas'
    query = supabase.from_('presupuestos').select(
        'id, total, fecha_creacion, descripcion, notas, '  # Solo 'notas', NO 'version'
        'cliente:cliente_id(nombre), '
        'lugar:lugar_trabajo_id(nombre), '
        'items_en_presupuesto(count)'
    ).eq('creado_por', user_id) 
    
    if 'cliente_id' in filtros:
        query = query.eq('cliente_id', filtros['cliente_id'])
    if 'lugar_trabajo_id' in filtros:
        query = query.eq('lugar_trabajo_id', filtros['lugar_trabajo_id'])
        
    if 'fecha_inicio' in filtros:
        fecha_str = filtros['fecha_inicio'].isoformat()
        query = query.gte('fecha_creacion', fecha_str)
        
    query = query.order('fecha_creacion', desc=True)
    response = query.execute()
    
    if response and response.data:
        presupuestos_procesados = []
        for p in response.data:
            p['cliente'] = p.pop('cliente') if p.get('cliente') else {'nombre': 'N/A'}
            p['lugar'] = p.pop('lugar') if p.get('lugar') else {'nombre': 'N/A'}
            
            num_items_data = p.pop('items_en_presupuesto')
            p['num_items'] = num_items_data[0]['count'] if num_items_data and num_items_data[0] else 0
            
            # ASEGURAR QUE 'notas' TENGA UN VALOR POR DEFECTO SI ES NULL
            if p.get('notas') is None:
                p['notas'] = 'V1'  # Valor por defecto
            
            presupuestos_procesados.append(p)
            
        return presupuestos_procesados
    return []

def delete_presupuesto(presupuesto_id: int, user_id: str) -> bool:
    """Elimina un presupuesto (los ítems se eliminan automáticamente por CASCADE)."""
    supabase = get_supabase_client()
    try:
        print(f"🔍 DEBUG: Intentando eliminar presupuesto {presupuesto_id} para usuario {user_id}")
        
        response = supabase.from_('presupuestos')\
            .delete()\
            .eq('id', presupuesto_id)\
            .eq('creado_por', user_id)\
            .execute()
        
        print(f"🔍 DEBUG: Response: {response}")
        print(f"🔍 DEBUG: Response data: {response.data}")
        print(f"🔍 DEBUG: Response error: {getattr(response, 'error', 'No error')}")
        
        if hasattr(response, 'error') and response.error:
            st.error(f"Error del servidor: {response.error.message}")
            return False
        
        return True
            
=======
    """Obtiene los presupuestos del usuario con filtros aplicados."""
    conn = _get_connection()
    try:
        query = """
            SELECT 
                p.id, p.total, p.fecha_creacion, p.descripcion, p.notas,
                c.nombre as cliente_nombre,
                l.nombre as lugar_nombre,
                (SELECT COUNT(*) FROM items_en_presupuesto WHERE presupuesto_id = p.id) as num_items
            FROM presupuestos p
            LEFT JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN lugares_trabajo l ON p.lugar_trabajo_id = l.id
            WHERE p.creado_por = %s
        """
        params = [user_id]
        
        if 'cliente_id' in filtros:
            query += " AND p.cliente_id = %s"
            params.append(filtros['cliente_id'])
        if 'lugar_trabajo_id' in filtros:
            query += " AND p.lugar_trabajo_id = %s"
            params.append(filtros['lugar_trabajo_id'])
        if 'fecha_inicio' in filtros:
            query += " AND p.fecha_creacion >= %s"
            params.append(filtros['fecha_inicio'].isoformat())
            
        query += " ORDER BY p.fecha_creacion DESC;"
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            
            presupuestos_procesados = []
            for row in rows:
                p = dict(row)
                # Formatear salida simulando la estructura original de Supabase
                p['cliente'] = {'nombre': p.pop('cliente_nombre') or 'N/A'}
                p['lugar'] = {'nombre': p.pop('lugar_nombre') or 'N/A'}
                
                if p.get('notas') is None:
                    p['notas'] = 'V1'
                    
                presupuestos_procesados.append(p)
                
            return presupuestos_procesados
    except Exception as e:
        st.error(f"Error al obtener presupuestos del usuario: {e}")
        return []

def delete_presupuesto(presupuesto_id: int, user_id: str) -> bool:
    """Elimina un presupuesto (los ítems se eliminan automáticamente por CASCADE)."""
    conn = _get_connection()
    try:
        print(f"🔍 DEBUG: Intentando eliminar presupuesto {presupuesto_id} para usuario {user_id}")
        
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM presupuestos WHERE id = %s AND creado_por = %s RETURNING id;",
                (presupuesto_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            
            if not deleted:
                return False
            return True
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        import traceback
        print(f"🔍 DEBUG: Exception: {traceback.format_exc()}")
        return False
  
def save_presupuesto_completo(
    user_id: str,
    cliente_id: int,
    lugar_trabajo_id: int,
    descripcion: str,
    items_data: Dict[str, Any],
    total: float
) -> Optional[int]:
<<<<<<< HEAD
    """
    Guarda un presupuesto completo (nuevo) en la base de datos.
    """
    supabase = get_supabase_client()

    try:
        # --- FASE 1: Crear NUEVO registro en presupuestos ---
        nuevo_presupuesto_data = {
            'cliente_id': cliente_id,
            'lugar_trabajo_id': lugar_trabajo_id,
            'descripcion': descripcion,
            'total': float(total),
            'creado_por': user_id
        }
        
        response_presupuesto = supabase.table('presupuestos').insert(nuevo_presupuesto_data).execute()

        if not response_presupuesto.data:
            raise Exception("Fallo la creación del nuevo presupuesto.")
        
        nuevo_presupuesto_id = response_presupuesto.data[0]['id']

        # --- FASE 2: Preparar e insertar los ítems para el NUEVO presupuesto ---
        items_a_insertar = []
        # Obtener mapeo de nombre de categoría a ID
        categorias_map = {nombre.lower(): id_cat for id_cat, nombre in get_categorias(user_id)}
        
        for cat_nombre, data in items_data.items():
            # Obtener ID de categoría (si es general/sin categoría, será None)
            cat_id = categorias_map.get(cat_nombre.lower())
            
            # --- Procesar Items Normales ---
            for item in data.get('items', []):
                # Verificar campos requeridos
                if 'cantidad' not in item or 'precio_unitario' not in item:
                    continue
                
                try:
                    # Asegurar que cantidad sea entero
                    cantidad_int = int(item['cantidad'])
                    precio_unitario_float = float(item['precio_unitario'])
                    total_item = cantidad_int * precio_unitario_float
                    
                    if total_item <= 0: 
                        continue
                    
                    # Para ítems sin categoría explícita (como 'general'), usamos la ID de la categoría del loop
                    final_cat_id = cat_id if cat_id is not None else None 
                    
                    # Usar nombre_personalizado
                    nombre_item = item.get('nombre_personalizado', 'Sin nombre')
                    
                    item_para_insertar = {
                        'presupuesto_id': nuevo_presupuesto_id,
                        'categoria_id': final_cat_id,
                        'nombre_personalizado': nombre_item,
                        'unidad': item.get('unidad', 'Unidad'),
                        'cantidad': cantidad_int,
                        'precio_unitario': precio_unitario_float,
                        'notas': item.get('notas', '')
                    }
                    
                    items_a_insertar.append(item_para_insertar)
                    
                except Exception:
                    continue
            
            # --- Procesar Mano de Obra ---
            mano_obra = float(data.get('mano_obra', 0.0))
            if mano_obra > 0:
                # La MO general o de categoría usa el ID de categoría o None si es 'general'
                final_cat_id_mo = cat_id if cat_nombre.lower() != 'general' else None
                
                items_a_insertar.append({
                    'presupuesto_id': nuevo_presupuesto_id,
                    'categoria_id': final_cat_id_mo, 
                    'nombre_personalizado': 'Mano de Obra',
                    'unidad': 'Unidad',
                    'cantidad': 1,
                    'precio_unitario': mano_obra,
                    'notas': 'Mano de Obra'
                })

        # --- FASE 3: Insertar items del NUEVO presupuesto ---
        if items_a_insertar:
            response_insert = supabase.table('items_en_presupuesto').insert(items_a_insertar).execute()
            
            if not response_insert.data:
                # Eliminar el presupuesto creado si falla la inserción de items
                supabase.table('presupuestos').delete().eq('id', nuevo_presupuesto_id).execute()
                raise Exception("Fallo la inserción de los ítems del nuevo presupuesto.")

        return nuevo_presupuesto_id

=======
    """Guarda un presupuesto completo (nuevo) en la base de datos."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            # --- FASE 1: Crear NUEVO registro en presupuestos ---
            cur.execute(
                """INSERT INTO presupuestos (cliente_id, lugar_trabajo_id, descripcion, total, creado_por) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id;""",
                (cliente_id, lugar_trabajo_id, descripcion, float(total), user_id)
            )
            nuevo_presupuesto_id = cur.fetchone()[0]

            # --- FASE 2: Preparar los ítems ---
            items_a_insertar = []
            categorias_map = {nombre.lower(): id_cat for id_cat, nombre in get_categorias(user_id)}
            
            for cat_nombre, data in items_data.items():
                cat_id = categorias_map.get(cat_nombre.lower())
                
                # --- Procesar Items Normales ---
                for item in data.get('items', []):
                    if 'cantidad' not in item or 'precio_unitario' not in item:
                        continue
                    try:
                        cantidad_int = int(item['cantidad'])
                        precio_unitario_float = float(item['precio_unitario'])
                        total_item = cantidad_int * precio_unitario_float
                        
                        if total_item <= 0: 
                            continue
                        
                        final_cat_id = cat_id if cat_id is not None else None 
                        nombre_item = item.get('nombre_personalizado', 'Sin nombre')
                        
                        items_a_insertar.append((
                            nuevo_presupuesto_id, final_cat_id, nombre_item,
                            item.get('text', item.get('unidad', 'Unidad')), # Mantiene fallback por consistencia
                            cantidad_int, precio_unitario_float, item.get('notas', '')
                        ))
                    except:
                        continue
                
                # --- Procesar Mano de Obra ---
                mano_obra = float(data.get('mano_obra', 0.0))
                if mano_obra > 0:
                    final_cat_id_mo = cat_id if cat_nombre.lower() != 'general' else None
                    items_a_insertar.append((
                        nuevo_presupuesto_id, final_cat_id_mo, 'Mano de Obra',
                        'Unidad', 1, mano_obra, 'Mano de Obra'
                    ))

            # --- FASE 3: Insertar items del NUEVO presupuesto ---
            if items_a_insertar:
                cur.executemany(
                    """INSERT INTO items_en_presupuesto 
                       (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas)
                       VALUES (%s, %s, %s, %s, %s, %s, %s);""",
                    items_a_insertar
                )
            
            conn.commit()
            return nuevo_presupuesto_id

>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error al guardar presupuesto completo: {e}")
        return None
<<<<<<< HEAD
#Ver detalles en Hitorial
def _show_presupuesto_detail(presupuesto_id: int):
    """Muestra el detalle de los ítems de un presupuesto en un st.data_editor de solo lectura."""
    supabase = get_supabase_client()
    try:
        response = supabase.from_('items_en_presupuesto').select(
            'nombre_personalizado, unidad, cantidad, precio_unitario, total, notas'
        ).eq('presupuesto_id', presupuesto_id).execute()
        
        if response and response.data:
            st.data_editor(
                response.data, 
=======

def _show_presupuesto_detail(presupuesto_id: int):
    """Muestra el detalle de los ítems de un presupuesto en un st.data_editor de solo lectura."""
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT nombre_personalizado, unidad, cantidad, precio_unitario, 
                          (cantidad * precio_unitario) as total, notas 
                   FROM items_en_presupuesto WHERE presupuesto_id = %s;""",
                (presupuesto_id,)
            )
            data = cur.fetchall()
            
        if data:
            st.data_editor(
                [dict(r) for r in data], 
>>>>>>> parent of 9fc908a (Update db.py)
                column_config={
                    "nombre_personalizado": st.column_config.TextColumn("Ítem", width="large"),
                    "precio_unitario": st.column_config.NumberColumn("P. Unitario", format="$%.2f"),
                    "total": st.column_config.NumberColumn("Total Ítem", format="$%.2f"),
                },
                hide_index=True,
                disabled=True,
                key=f"data_editor_unique_{presupuesto_id}" 
            )
        else:
            st.info("Este presupuesto no tiene ítems.")
    except Exception as e:
        st.error(f"Error al cargar detalle de ítems: {e}")

# =================================================================
# PRESUPUESTOS EDITADOS
# =================================================================

def get_presupuestos_para_edicion(user_id: str) -> List[Dict]:
    """Obtener presupuestos básicos para el selector de edición"""
<<<<<<< HEAD
    supabase = get_supabase_client()
    
=======
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        # Consulta mínima y segura
        response = (
            supabase
            .table("presupuestos")
            .select("id, descripcion, fecha_creacion, cliente_id, lugar_trabajo_id")
            .eq("creado_por", user_id)  # CAMBIO IMPORTANTE
            .order("fecha_creacion", desc=True)
            .execute()
        )
        

        
        return response.data if response.data else []
    
    except Exception as e:
        print(f"Error en get_presupuestos_para_edicion: {e}")
        return []
<<<<<<< HEAD


def get_presupuesto_para_editar(presupuesto_id: int) -> Dict:
    """Obtener detalle completo de un presupuesto para editar"""
    supabase = get_supabase_client()
    
    try:
        # Obtener datos básicos del presupuesto
        main_response = supabase.from_('presupuestos').select(
            'id, descripcion, cliente_id, lugar_trabajo_id'
        ).eq('id', presupuesto_id).single().execute()
        
        if not main_response.data:
            return {}
            
        presupuesto_data = main_response.data
        
        # Obtener items con categorías
        items_response = supabase.from_('items_en_presupuesto').select(
            'nombre_personalizado, unidad, cantidad, precio_unitario, total, notas, '
            'categoria:categoria_id(nombre)'
        ).eq('presupuesto_id', presupuesto_id).execute()
        
        items_list = []
        if items_response.data:
            for item in items_response.data:
=======

def get_presupuesto_para_editar(presupuesto_id: int) -> Dict:
    """Obtener detalle completo de un presupuesto para editar"""
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Datos principales
            cur.execute(
                "SELECT id, descripcion, cliente_id, lugar_trabajo_id FROM presupuestos WHERE id = %s;",
                (presupuesto_id,)
            )
            row = cur.fetchone()
            if not row:
                return {}
            presupuesto_data = dict(row)
            
            # Items con categorías
            cur.execute(
                """SELECT i.nombre_personalizado, i.unidad, i.cantidad, i.precio_unitario, 
                          (i.cantidad * i.precio_unitario) as total, i.notas, c.nombre as categoria_nombre
                   FROM items_en_presupuesto i
                   LEFT JOIN categorias c ON i.categoria_id = c.id
                   WHERE i.presupuesto_id = %s;""",
                (presupuesto_id,)
            )
            items_rows = cur.fetchall()
            
            items_list = []
            for item in items_rows:
>>>>>>> parent of 9fc908a (Update db.py)
                items_list.append({
                    'nombre': item['nombre_personalizado'],
                    'unidad': item['unidad'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'total': item['total'],
                    'notas': item['notas'],
<<<<<<< HEAD
                    'categoria': item['categoria']['nombre'] if item.get('categoria') else 'Sin Categoría'
                })
                
        presupuesto_data['items'] = items_list
        
        # Obtener nombres de cliente y lugar por separado
        if presupuesto_data.get('cliente_id'):
            cliente_response = supabase.table('clientes').select('nombre').eq('id', presupuesto_data['cliente_id']).execute()
            if cliente_response.data:
                presupuesto_data['cliente_nombre'] = cliente_response.data[0]['nombre']
        
        if presupuesto_data.get('lugar_trabajo_id'):
            lugar_response = supabase.table('lugares_trabajo').select('nombre').eq('id', presupuesto_data['lugar_trabajo_id']).execute()
            if lugar_response.data:
                presupuesto_data['lugar_nombre'] = lugar_response.data[0]['nombre']
        
        return presupuesto_data
        
=======
                    'categoria': item['categoria_nombre'] if item.get('categoria_nombre') else 'Sin Categoría'
                })
            presupuesto_data['items'] = items_list
            
            # Cliente nombre
            if presupuesto_data.get('cliente_id'):
                cur.execute("SELECT nombre FROM clientes WHERE id = %s;", (presupuesto_data['cliente_id'],))
                c_row = cur.fetchone()
                if c_row:
                    presupuesto_data['cliente_nombre'] = c_row['nombre']
                    
            # Lugar nombre
            if presupuesto_data.get('lugar_trabajo_id'):
                cur.execute("SELECT nombre FROM lugares_trabajo WHERE id = %s;", (presupuesto_data['lugar_trabajo_id'],))
                l_row = cur.fetchone()
                if l_row:
                    presupuesto_data['lugar_nombre'] = l_row['nombre']
                    
            return presupuesto_data
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        print(f"Error en get_presupuesto_para_editar: {e}")
        return {}
    
def save_edited_presupuesto(
    user_id: str,
    cliente_id: int,
    lugar_trabajo_id: int,
    descripcion: str,
    items_data: Dict[str, Any],
    total_general: float
) -> Optional[int]:
<<<<<<< HEAD
    """
    Crea un NUEVO presupuesto a partir de datos editados.
    """
    supabase = get_supabase_client()

    try:
        # --- FASE 1: Crear NUEVO registro en presupuestos ---
        nuevo_presupuesto_data = {
            'cliente_id': cliente_id,
            'lugar_trabajo_id': lugar_trabajo_id,
            'descripcion': descripcion,
            'notas': "Presupuesto editado",  # Nota simple
            'total': float(total_general),
            'creado_por': user_id
            # Eliminamos 'presupuesto_original_id'
        }
        
        response_presupuesto = supabase.table('presupuestos').insert(nuevo_presupuesto_data).execute()

        if not response_presupuesto.data:
            raise Exception("Fallo la creación del nuevo presupuesto.")
        
        nuevo_presupuesto_id = response_presupuesto.data[0]['id']

        # --- FASE 2: Preparar e insertar los ítems (código existente) ---
        items_a_insertar = []
        # Obtener mapeo de nombre de categoría a ID
        categorias_map = {nombre.lower(): id_cat for id_cat, nombre in get_categorias(user_id)}
        
        for cat_nombre, data in items_data.items():
            # Obtener ID de categoría (si es general/sin categoría, será None)
            cat_id = categorias_map.get(cat_nombre.lower())
            
            # --- Procesar Items Normales ---
            for item in data.get('items', []):
                # Asegurar que cantidad sea entero
                cantidad_int = int(item['cantidad'])
                precio_unitario_float = float(item['precio_unitario'])
                total = cantidad_int * precio_unitario_float
                
                if total <= 0: 
                    continue
                
                final_cat_id = cat_id if cat_id is not None else None 
                
                items_a_insertar.append({
                    'presupuesto_id': nuevo_presupuesto_id,
                    'categoria_id': final_cat_id,
                    'nombre_personalizado': item['nombre'],
                    'unidad': item['unidad'],
                    'cantidad': cantidad_int,
                    'precio_unitario': precio_unitario_float,
                    'notas': item.get('notas', '')
                })
            
            # --- Procesar Mano de Obra ---
            mano_obra = float(data.get('mano_obra', 0.0))
            if mano_obra > 0:
                final_cat_id_mo = cat_id if cat_nombre.lower() != 'general' else None
                
                items_a_insertar.append({
                    'presupuesto_id': nuevo_presupuesto_id,
                    'categoria_id': final_cat_id_mo, 
                    'nombre_personalizado': 'Mano de Obra',
                    'unidad': 'Unidad',
                    'cantidad': 1,
                    'precio_unitario': mano_obra,
                    'notas': 'Mano de Obra'
                })

        # --- FASE 3: Insertar items del NUEVO presupuesto ---
        if items_a_insertar:
            response_insert = supabase.table('items_en_presupuesto').insert(items_a_insertar).execute()
            
            if not response_insert.data:
                supabase.table('presupuestos').delete().eq('id', nuevo_presupuesto_id).execute()
                raise Exception("Fallo la inserción de los ítems del nuevo presupuesto.")

        return nuevo_presupuesto_id

    except Exception as e:
        st.error(f"Error al crear nuevo presupuesto: {e}")
        return None
# Ver los detalles del presupuesto
@st.cache_data(ttl=60) 
def get_presupuesto_detallado(presupuesto_id: int) -> dict:
    """
    Obtiene todos los detalles de un presupuesto para el PDF.
    La seguridad se aplica mediante RLS (Row Level Security).
    """
    supabase = get_supabase_client()
    
    try:
        # 1. Obtener datos principales del presupuesto (cliente, lugar, descripcion)
        # RLS asegura que solo el 'creado_por' pueda leer esto
        main_response = supabase.from_('presupuestos').select(
            'id, descripcion, total, '
            'cliente:cliente_id(nombre), '
            'lugar:lugar_trabajo_id(nombre)'
        ).eq('id', presupuesto_id).single().execute()
        
        if not main_response.data:
            raise Exception("Presupuesto no encontrado o sin acceso (Verifique RLS).")
            
        presupuesto_data = main_response.data
        
        # 2. Obtener los ítems asociados, incluyendo el nombre de la categoría
        # RLS en 'items_en_presupuesto' y 'categorias' debe permitir esto
        items_response = supabase.from_('items_en_presupuesto').select(
            'nombre_personalizado, unidad, cantidad, precio_unitario, total, notas, '
            'categoria:categoria_id(nombre)' # Join para obtener el nombre de la categoría
        ).eq('presupuesto_id', presupuesto_id).execute()
        
        items_list = []
        if items_response.data:
            for item in items_response.data:
=======
    """Crea un NUEVO presupuesto a partir de datos editados."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO presupuestos (cliente_id, lugar_trabajo_id, descripcion, notas, total, creado_por) 
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;""",
                (cliente_id, lugar_trabajo_id, descripcion, "Presupuesto editado", float(total_general), user_id)
            )
            nuevo_presupuesto_id = cur.fetchone()[0]

            items_a_insertar = []
            categorias_map = {nombre.lower(): id_cat for id_cat, nombre in get_categorias(user_id)}
            
            for cat_nombre, data in items_data.items():
                cat_id = \
                categorias_map.get(cat_nombre.lower())
                
                for item in data.get('items', []):
                    cantidad_int = int(item['cantidad'])
                    precio_unitario_float = float(item['precio_unitario'])
                    if (cantidad_int * precio_unitario_float) <= 0: 
                        continue
                    
                    final_cat_id = cat_id if cat_id is not None else None 
                    items_a_insertar.append((
                        nuevo_presupuesto_id, final_cat_id, item['nombre'],
                        item['unidad'], cantidad_int, precio_unitario_float, item.get('notas', '')
                    ))
                
                mano_obra = float(data.get('mano_obra', 0.0))
                if mano_obra > 0:
                    final_cat_id_mo = cat_id if cat_nombre.lower() != 'general' else None
                    items_a_insertar.append((
                        nuevo_presupuesto_id, final_cat_id_mo, 'Mano de Obra',
                        'Unidad', 1, mano_obra, 'Mano de Obra'
                    ))

            if items_a_insertar:
                cur.executemany(
                    """INSERT INTO items_en_presupuesto 
                       (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas)
                       VALUES (%s, %s, %s, %s, %s, %s, %s);""",
                    items_a_insertar
                )
                
            conn.commit()
            return nuevo_presupuesto_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error al crear nuevo presupuesto: {e}")
        return None

# Ver los detalles del presupuesto
@st.cache_data(ttl=60) 
def get_presupuesto_detallado(presupuesto_id: int) -> dict:
    """Obtiene todos los detalles de un presupuesto para el PDF."""
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT p.id, p.descripcion, p.total, c.nombre as cliente_nombre, l.nombre as lugar_nombre
                   FROM presupuestos p
                   LEFT JOIN clientes c ON p.cliente_id = c.id
                   LEFT JOIN lugares_trabajo l ON p.lugar_trabajo_id = l.id
                   WHERE p.id = %s;""",
                (presupuesto_id,)
            )
            main_row = cur.fetchone()
            if not main_row:
                raise Exception("Presupuesto no encontrado.")
                
            presupuesto_data = dict(main_row)
            presupuesto_data['cliente'] = {'nombre': presupuesto_data.pop('cliente_nombre') or 'N/A'}
            presupuesto_data['lugar'] = {'nombre': presupuesto_data.pop('lugar_nombre') or 'N/A'}
            
            cur.execute(
                """SELECT i.nombre_personalizado, i.unidad, i.cantidad, i.precio_unitario, 
                          (i.cantidad * i.precio_unitario) as total, i.notas, cat.nombre as categoria_nombre
                   FROM items_en_presupuesto i
                   LEFT JOIN categorias cat ON i.categoria_id = cat.id
                   WHERE i.presupuesto_id = %s;""",
                (presupuesto_id,)
            )
            items_rows = cur.fetchall()
            
            items_list = []
            for item in items_rows:
>>>>>>> parent of 9fc908a (Update db.py)
                items_list.append({
                    'nombre': item['nombre_personalizado'],
                    'unidad': item['unidad'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'total': item['total'],
                    'notas': item['notas'],
<<<<<<< HEAD
                    # Maneja el caso de que la categoría sea nula o no se encuentre
                    'categoria': item['categoria']['nombre'] if item.get('categoria') and item['categoria'] else 'Sin Categoría'
                })
                
        presupuesto_data['items'] = items_list
        
        return presupuesto_data
    
    except Exception as e:
        st.error(f"Error al obtener detalle del presupuesto: {e}")
        return {}
import streamlit as st
=======
                    'categoria': item['categoria_nombre'] if item.get('categoria_nombre') else 'Sin Categoría'
                })
                
            presupuesto_data['items'] = items_list
            return presupuesto_data
    except Exception as e:
        st.error(f"Error al obtener detalle del presupuesto: {e}")
        return {}
>>>>>>> parent of 9fc908a (Update db.py)

@st.cache_data
def save_draft(draft: dict):
    """Guarda un borrador local persistente."""
    return draft

@st.cache_data
def load_draft() -> dict:
    """Carga un borrador guardado si existe."""
    return {}

# Asegúrate de tener st.cache_data disponible en el archivo

@st.cache_data(ttl=60)  # <-- Guarda en memoria por 60 segundos para máxima velocidad
def get_estados_cuenta_usuario(user_id: str, filtros: dict = None) -> list:
<<<<<<< HEAD
    """
    Obtiene los estados de cuenta de un usuario desde Supabase aplicando filtros.
    Optimizado con caché de Streamlit.
    """
    supabase = get_supabase_client()
=======
    """Obtiene los estados de cuenta de un usuario."""
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    filtros = filtros or {}
    
    try:
<<<<<<< HEAD
        # Traemos solo los datos planos necesarios para la tabla de forma directa
        query = supabase.table('estados_cuenta').select('''
            id,
            user_id,
            cliente_id,
            lugar_trabajo_id,
            monto_base,
            abono_monto,
            total_neto,
            fecha_emision,
            pagado,
            cliente:cliente_id(nombre),
            lugar_trabajo:lugar_trabajo_id(nombre)
        ''').eq('user_id', user_id)
        
        if 'cliente_id' in filtros and filtros['cliente_id']:
            query = query.eq('cliente_id', filtros['cliente_id'])
            
        if 'lugar_trabajo_id' in filtros and filtros['lugar_trabajo_id']:
            query = query.eq('lugar_trabajo_id', filtros['lugar_trabajo_id'])
            
        if 'fecha_inicio' in filtros and filtros['fecha_inicio']:
            fecha_iso = filtros['fecha_inicio'].strftime('%Y-%m-%d')
            query = query.gte('fecha_emision', fecha_iso)
            
        query = query.order('fecha_emision', desc=True)
        
        response = query.execute()
        return response.data or []
        
=======
        query = """
            SELECT 
                ec.id, ec.user_id, ec.cliente_id, ec.lugar_trabajo_id, ec.monto_base,
                ec.abono_monto, ec.total_neto, ec.fecha_emision, ec.pagado,
                c.nombre as cliente_nombre, lt.nombre as lugar_nombre
            FROM estados_cuenta ec
            LEFT JOIN clientes c ON ec.cliente_id = c.id
            LEFT JOIN lugares_trabajo lt ON ec.lugar_trabajo_id = lt.id
            WHERE ec.user_id = %s
        """
        params = [user_id]
        
        if filtros.get('cliente_id'):
            query += " AND ec.cliente_id = %s"
            params.append(filtros['cliente_id'])
            
        if filtros.get('lugar_trabajo_id'):
            query += " AND ec.lugar_trabajo_id = %s"
            params.append(filtros['lugar_trabajo_id'])
            
        if filtros.get('fecha_inicio'):
            query += " AND ec.fecha_emision >= %s"
            params.append(filtros['fecha_inicio'].strftime('%Y-%m-%d'))
            
        query += " ORDER BY ec.fecha_emision DESC;"
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            
            resultados = []
            for row in rows:
                r = dict(row)
                r['cliente'] = {'nombre': r.pop('cliente_nombre') or 'N/A'}
                r['lugar_trabajo'] = {'nombre': r.pop('lugar_nombre') or 'N/A'}
                resultados.append(r)
            return resultados
>>>>>>> parent of 9fc908a (Update db.py)
    except Exception as e:
        st.error(f"Error interno en get_estados_cuenta_usuario: {e}")
        return []
    
def toggle_estado_pago_ec(estado_id: int, nuevo_estado: bool) -> bool:
<<<<<<< HEAD
    """
    Cambia el estado de pago (True/False) de un estado de cuenta específico.
    """
    supabase = get_supabase_client()
=======
    """Cambia el estado de pago (True/False) de un estado de cuenta específico."""
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        response = supabase.table('estados_cuenta')\
            .update({'pagado': nuevo_estado})\
            .eq('id', estado_id)\
            .execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Error al actualizar estado de pago: {e}")
        return False

def delete_estado_cuenta(estado_id: int, user_id: str) -> bool:
<<<<<<< HEAD
    """
    Elimina un estado de cuenta de la base de datos.
    """
    supabase = get_supabase_client()
=======
    """Elimina un estado de cuenta de la base de datos."""
    conn = _get_connection()
>>>>>>> parent of 9fc908a (Update db.py)
    try:
        response = supabase.table('estados_cuenta').delete().eq('id', estado_id).eq('user_id', user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Error al eliminar estado de cuenta: {e}")
        return False