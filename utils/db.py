import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

# =================================================================
# FUNCIÓN DE INICIACIÓN DE BASE DE DATOS Y CACHÉ
# =================================================================

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

# =================================================================
# LECTURA DE ENTIDADES (CACHÉ)
# =================================================================

@st.cache_data(ttl=600)
def get_clientes(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de clientes (id, nombre) del usuario logueado."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM clientes WHERE creado_por = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            rows = cur.fetchall()
            return [(row[0], row[1]) for row in rows]
    except Exception as e:
        st.error(f"Error al obtener clientes: {e}")
        return []

@st.cache_data(ttl=600)
def get_lugares_trabajo(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de lugares de trabajo (id, nombre) del usuario logueado."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM lugares_trabajo WHERE creado_por = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            rows = cur.fetchall()
            return [(row[0], row[1]) for row in rows]
    except Exception as e:
        st.error(f"Error al obtener lugares de trabajo: {e}")
        return []

@st.cache_data(ttl=600)
def get_categorias(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de categorías (id, nombre) del usuario logueado."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM categorias WHERE creado_por = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            rows = cur.fetchall()
            return [(row[0], row[1]) for row in rows]
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

# =================================================================
# GESTIÓN DE ENTIDADES
# =================================================================

def create_cliente(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo cliente para el usuario."""
    conn = _get_connection()
    try:
        alias_base = nombre.strip().lower().replace(' ', '_')[:45]
        alias = alias_base
        counter = 1
        
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
    except Exception as e:
        conn.rollback()
        st.error(f"Error al crear cliente: {e}")
        if '23505' in str(e) and 'clientes_pkey' in str(e):
            st.error("⚠️ Error de secuencia: Contacta al administrador para resetear la secuencia de IDs de clientes")
        return None

def create_lugar_trabajo(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo lugar de trabajo para el usuario."""
    conn = _get_connection()
    try:
        nombre_base = nombre.strip()
        nombre_final = nombre_base
        counter = 1
        
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
    except Exception as e:
        conn.rollback()
        st.error(f"Error al crear lugar de trabajo: {e}")
        if '23505' in str(e) and 'lugares_trabajo_pkey' in str(e):
            st.error("⚠️ Error de secuencia: La secuencia de IDs de lugares de trabajo está desincronizada")
        return None

def create_categoria(nombre: str, user_id: str) -> Optional[int]:
    """Crea una nueva categoría para el usuario."""
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
    except Exception as e:
        conn.rollback()
        st.error(f"Error al crear categoría: {e}")
        return None

def update_cliente(cliente_id: int, nuevo_nombre: str, user_id: str) -> bool:
    """Actualiza el nombre de un cliente existente"""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE clientes SET nombre = %s WHERE id = %s AND creado_por = %s RETURNING id;",
                (nuevo_nombre, cliente_id, user_id)
            )
            updated = cur.fetchone()
            conn.commit()
            return updated is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al actualizar cliente: {e}")
        return False

def delete_cliente(cliente_id: int, user_id: str) -> bool:
    """Elimina un cliente junto con todos sus presupuestos e items asociados (CASCADE)."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM clientes WHERE id = %s AND creado_por = %s RETURNING id;",
                (cliente_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar cliente: {e}")
        return False

def update_lugar_trabajo(lugar_id: int, nuevo_nombre: str, user_id: str) -> bool:
    """Actualiza el nombre de un lugar de trabajo existente"""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE lugares_trabajo SET nombre = %s WHERE id = %s AND creado_por = %s RETURNING id;",
                (nuevo_nombre, lugar_id, user_id)
            )
            updated = cur.fetchone()
            conn.commit()
            return updated is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al actualizar lugar de trabajo: {e}")
        return False

def delete_lugar_trabajo(lugar_id: int, user_id: str) -> bool:
    """Elimina un lugar de trabajo junto con todos sus presupuestos e items asociados (CASCADE)."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM lugares_trabajo WHERE id = %s AND creado_por = %s RETURNING id;",
                (lugar_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar lugar de trabajo: {e}")
        return False

def get_presupuestos_por_cliente(cliente_id: int) -> list[dict]:
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
    except Exception as e:
        print(f"Error al obtener presupuestos del cliente {cliente_id}: {e}")
        return []

def get_presupuestos_por_lugar(lugar_id: int) -> list[dict]:
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
    except Exception as e:
        print(f"Error al obtener presupuestos del lugar {lugar_id}: {e}")
        return []

# =================================================================
# GESTIÓN DE PRESUPUESTOS
# =================================================================

def get_presupuestos_usuario(user_id: str, filtros: dict) -> list:
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
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar: {e}")
        return False
  
def save_presupuesto_completo(
    user_id: str,
    cliente_id: int,
    lugar_trabajo_id: int,
    descripcion: str,
    items_data: Dict[str, Any],
    total: float
) -> Optional[int]:
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

    except Exception as e:
        conn.rollback()
        st.error(f"Error al guardar presupuesto completo: {e}")
        return None

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
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id, descripcion, fecha_creacion, cliente_id, lugar_trabajo_id 
                   FROM presupuestos WHERE creado_por = %s ORDER BY fecha_creacion DESC;""",
                (user_id,)
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"Error en get_presupuestos_para_edicion: {e}")
        return []

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
                items_list.append({
                    'nombre': item['nombre_personalizado'],
                    'unidad': item['unidad'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'total': item['total'],
                    'notas': item['notas'],
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
                items_list.append({
                    'nombre': item['nombre_personalizado'],
                    'unidad': item['unidad'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'total': item['total'],
                    'notas': item['notas'],
                    'categoria': item['categoria_nombre'] if item.get('categoria_nombre') else 'Sin Categoría'
                })
                
            presupuesto_data['items'] = items_list
            return presupuesto_data
    except Exception as e:
        st.error(f"Error al obtener detalle del presupuesto: {e}")
        return {}

@st.cache_data
def save_draft(draft: dict):
    """Guarda un borrador local persistente."""
    return draft

@st.cache_data
def load_draft() -> dict:
    """Carga un borrador guardado si existe."""
    return {}

@st.cache_data(ttl=60)
def get_estados_cuenta_usuario(user_id: str, filtros: dict = None) -> list:
    """Obtiene los estados de cuenta de un usuario."""
    conn = _get_connection()
    filtros = filtros or {}
    try:
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
    except Exception as e:
        st.error(f"Error interno en get_estados_cuenta_usuario: {e}")
        return []
    
def toggle_estado_pago_ec(estado_id: int, nuevo_estado: bool) -> bool:
    """Cambia el estado de pago (True/False) de un estado de cuenta específico."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE estados_cuenta SET pagado = %s WHERE id = %s RETURNING id;",
                (nuevo_estado, estado_id)
            )
            updated = cur.fetchone()
            conn.commit()
            return updated is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al actualizar estado de pago: {e}")
        return False

def delete_estado_cuenta(estado_id: int, user_id: str) -> bool:
    """Elimina un estado de cuenta de la base de datos."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM estados_cuenta WHERE id = %s AND user_id = %s RETURNING id;",
                (estado_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar estado de cuenta: {e}")
        return False