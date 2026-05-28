import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# =================================================================
# FUNCIÓN DE INICIACIÓN DE BASE DE DATOS Y CONEXIÓN
# =================================================================

def initialize_neon_connection():
    """Establece una conexión directa con Neon utilizando st.secrets de forma plana."""
    try:
        conn = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            sslmode="require"
        )
        return conn
    except KeyError as e:
        st.error(f"Error de configuración: Falta la credencial {e} en st.secrets.")
        st.stop()
    except Exception as e:
        st.error(f"Error al conectar a Neon (PostgreSQL): {e}")
        st.stop()

def get_connection():
    """Devuelve una nueva conexión activa."""
    return initialize_neon_connection()

# =================================================================
# LECTURA DE ENTIDADES (CACHÉ)
# =================================================================

@st.cache_data(ttl=600)
def get_clientes(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de clientes utilizando la columna usuario_uid."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM clientes WHERE usuario_uid = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            return cur.fetchall()
    except Exception as e:
        st.error(f"Error al obtener clientes: {e}")
        return []
    finally:
        conn.close()

@st.cache_data(ttl=600)
def get_lugares_trabajo(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de lugares de trabajo utilizando la columna usuario_uid."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM lugares_trabajo WHERE usuario_uid = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            return cur.fetchall()
    except Exception as e:
        st.error(f"Error al obtener lugares de trabajo: {e}")
        return []
    finally:
        conn.close()

@st.cache_data(ttl=600)
def get_categorias(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de categorías utilizando la columna usuario_uid."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre FROM categorias WHERE usuario_uid = %s ORDER BY nombre ASC;",
                (user_id,)
            )
            return cur.fetchall()
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []
    finally:
        conn.close()

# =================================================================
# GESTIÓN DE ENTIDADES
# =================================================================

def create_cliente(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo cliente asignando usuario_uid."""
    conn = get_connection()
    try:
        alias_base = nombre.strip().lower().replace(' ', '_')[:45]
        alias = alias_base
        counter = 1
        
        with conn.cursor() as cur:
            while True:
                cur.execute("SELECT id FROM clientes WHERE alias = %s AND usuario_uid = %s;", (alias, user_id))
                if not cur.fetchone():
                    break
                alias = f"{alias_base}_{counter}"
                counter += 1

            cur.execute(
                "INSERT INTO clientes (nombre, alias, usuario_uid) VALUES (%s, %s, %s) RETURNING id;",
                (nombre, alias, user_id)
            )
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            return nuevo_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error al crear cliente: {e}")
        return None
    finally:
        conn.close()

def create_lugar_trabajo(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo lugar de trabajo asignando usuario_uid."""
    conn = get_connection()
    try:
        nombre_base = nombre.strip()
        nombre_final = nombre_base
        counter = 1
        
        with conn.cursor() as cur:
            while True:
                cur.execute("SELECT id FROM lugares_trabajo WHERE nombre = %s AND usuario_uid = %s;", (nombre_final, user_id))
                if not cur.fetchone():
                    break
                nombre_final = f"{nombre_base}_{counter}"
                counter += 1

            cur.execute(
                "INSERT INTO lugares_trabajo (nombre, usuario_uid) VALUES (%s, %s) RETURNING id;",
                (nombre_final, user_id)
            )
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            return nuevo_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error al crear lugar de trabajo: {e}")
        return None
    finally:
        conn.close()

def create_categoria(nombre: str, user_id: str) -> Optional[int]:
    """Crea una nueva categoría asignando usuario_uid."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM categorias WHERE nombre = %s AND usuario_uid = %s;",
                (nombre, user_id)
            )
            if cur.fetchone():
                st.error("❌ Ya existe una categoría con ese nombre")
                return None

            cur.execute(
                "INSERT INTO categorias (nombre, usuario_uid) VALUES (%s, %s) RETURNING id;",
                (nombre, user_id)
            )
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            return nuevo_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error al crear categoría: {e}")
        return None
    finally:
        conn.close()

def update_cliente(cliente_id: int, nuevo_nombre: str, user_id: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE clientes SET nombre = %s WHERE id = %s AND usuario_uid = %s RETURNING id;",
                (nuevo_nombre, cliente_id, user_id)
            )
            updated = cur.fetchone()
            conn.commit()
            return updated is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al actualizar cliente: {e}")
        return False
    finally:
        conn.close()

def delete_cliente(cliente_id: int, user_id: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM clientes WHERE id = %s AND usuario_uid = %s RETURNING id;",
                (cliente_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar cliente: {e}")
        return False
    finally:
        conn.close()

def update_lugar_trabajo(lugar_id: int, nuevo_nombre: str, user_id: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE lugares_trabajo SET nombre = %s WHERE id = %s AND usuario_uid = %s RETURNING id;",
                (nuevo_nombre, lugar_id, user_id)
            )
            updated = cur.fetchone()
            conn.commit()
            return updated is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al actualizar lugar de trabajo: {e}")
        return False
    finally:
        conn.close()

def delete_lugar_trabajo(lugar_id: int, user_id: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM lugares_trabajo WHERE id = %s AND usuario_uid = %s RETURNING id;",
                (lugar_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar lugar de trabajo: {e}")
        return False
    finally:
        conn.close()

def get_presupuestos_por_cliente(cliente_id: int) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, descripcion, fecha_creacion, total FROM presupuestos WHERE cliente_id = %s;",
                (cliente_id,)
            )
            resultados = cur.fetchall()
            for p in resultados:
                if p.get("fecha_creacion"):
                    p["fecha_creacion"] = p["fecha_creacion"].strftime("%d/%m/%Y")
            return [dict(r) for r in resultados]
    except Exception as e:
        return []
    finally:
        conn.close()

def get_presupuestos_por_lugar(lugar_id: int) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, descripcion, fecha_creacion, total FROM presupuestos WHERE lugar_trabajo_id = %s;",
                (lugar_id,)
            )
            resultados = cur.fetchall()
            for p in resultados:
                if p.get("fecha_creacion"):
                    p["fecha_creacion"] = p["fecha_creacion"].strftime("%d/%m/%Y")
            return [dict(r) for r in resultados]
    except Exception as e:
        return []
    finally:
        conn.close()

# =================================================================
# GESTIÓN DE PRESUPUESTOS
# =================================================================

def get_presupuestos_usuario(user_id: str, filtros: dict) -> list:
    conn = get_connection()
    try:
        sql = """
            SELECT 
                p.id, p.total, p.fecha_creacion, p.descripcion, p.notas,
                c.nombre AS cliente_nombre,
                l.nombre AS lugar_nombre,
                (SELECT COUNT(*)::int FROM items_en_presupuesto WHERE presupuesto_id = p.id) AS num_items
            FROM presupuestos p
            LEFT JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN lugares_trabajo l ON p.lugar_trabajo_id = l.id
            WHERE p.usuario_uid = %s
        """
        params = [user_id]
        
        if 'cliente_id' in filtros and filtros['cliente_id']:
            sql += " AND p.cliente_id = %s"
            params.append(filtros['cliente_id'])
        if 'lugar_trabajo_id' in filtros and filtros['lugar_trabajo_id']:
            sql += " AND p.lugar_trabajo_id = %s"
            params.append(filtros['lugar_trabajo_id'])
        if 'fecha_inicio' in filtros and filtros['fecha_inicio']:
            sql += " AND p.fecha_creacion >= %s"
            params.append(filtros['fecha_inicio'].isoformat())
            
        sql += " ORDER BY p.fecha_creacion DESC;"
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            
            presupuestos_procesados = []
            for r in rows:
                p = dict(r)
                p['cliente'] = {'nombre': p.pop('cliente_nombre') or 'N/A'}
                p['lugar'] = {'nombre': p.pop('lugar_nombre') or 'N/A'}
                if p.get('notas') is None:
                    p['notas'] = ''
                presupuestos_procesados.append(p)
                
            return presupuestos_procesados
    except Exception as e:
        st.error(f"Error al cargar presupuestos: {e}")
        return []
    finally:
        conn.close()

def delete_presupuesto(presupuesto_id: int, user_id: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM presupuestos WHERE id = %s AND usuario_uid = %s RETURNING id;",
                (presupuesto_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar: {e}")
        return False
    finally:
        conn.close()

def save_presupuesto_completo(
    user_id: str, cliente_id: int, lugar_trabajo_id: int,
    descripcion: str, items_data: Dict[str, Any], total: float
) -> Optional[int]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO presupuestos (cliente_id, lugar_trabajo_id, descripcion, total, usuario_uid) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id;""",
                (cliente_id, lugar_trabajo_id, descripcion, float(total), user_id)
            )
            nuevo_presupuesto_id = cur.fetchone()[0]

            cur.execute("SELECT id, LOWER(nombre) FROM categorias WHERE usuario_uid = %s;", (user_id,))
            categorias_map = {row[1]: row[0] for row in cur.fetchall()}

            for cat_nombre, data in items_data.items():
                cat_id = categorias_map.get(cat_nombre.lower())

                for item in data.get('items', []):
                    if 'cantidad' not in item or 'precio_unitario' not in item:
                        continue
                    cantidad_int = int(item['cantidad'])
                    precio_unitario_float = float(item['precio_unitario'])

                    cur.execute(
                        """INSERT INTO items_en_presupuesto 
                           (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas)
                           VALUES (%s, %s, %s, %s, %s, %s, %s);""",
                        (nuevo_presupuesto_id, cat_id, item.get('nombre_personalizado', 'Sin nombre'),
                         item.get('unidad', 'Unidad'), cantidad_int, precio_unitario_float, item.get('notas', ''))
                    )

                mano_obra = float(data.get('mano_obra', 0.0))
                if mano_obra > 0:
                    final_cat_id_mo = cat_id if cat_nombre.lower() != 'general' else None
                    cur.execute(
                        """INSERT INTO items_en_presupuesto 
                           (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas, tipo)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                        (nuevo_presupuesto_id, final_cat_id_mo, 'Mano de Obra', 'Unidad', 1, mano_obra, 'Mano de Obra', 'mano_obra')
                    )

            conn.commit()
            return nuevo_presupuesto_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error al guardar presupuesto completo: {e}")
        return None
    finally:
        conn.close()

def _show_presupuesto_detail(presupuesto_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT nombre_personalizado, unidad, cantidad, precio_unitario, total, notas 
                   FROM items_en_presupuesto WHERE presupuesto_id = %s;""",
                (presupuesto_id,)
            )
            data = [dict(r) for r in cur.fetchall()]
            
        if data:
            st.data_editor(
                data, 
                column_config={
                    "nombre_personalizado": st.column_config.TextColumn("Ítem", width="large"),
                    "precio_unitario": st.column_config.NumberColumn("P. Unitario", format="$%.2f"),
                    "total": st.column_config.NumberColumn("Total Ítem", format="$%.2f"),
                },
                hide_index=True,
                disabled=True,
                key=f"data_editor_unique_{presupuesto_id}" 
            )
    except Exception as e:
        st.error(f"Error al cargar detalle de ítems: {e}")
    finally:
        conn.close()

# =================================================================
# PRESUPUESTOS EDITADOS
# =================================================================

def get_presupuestos_para_edicion(user_id: str) -> List[Dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id, descripcion, fecha_creacion, cliente_id, lugar_trabajo_id 
                   FROM presupuestos WHERE usuario_uid = %s ORDER BY fecha_creacion DESC;""",
                (user_id,)
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return []
    finally:
        conn.close()

def get_presupuesto_para_editar(presupuesto_id: int) -> Dict:
    conn = get_connection()
    try:
        presupuesto_data = {}
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, descripcion, cliente_id, lugar_trabajo_id FROM presupuestos WHERE id = %s;",
                (presupuesto_id,)
            )
            row = cur.fetchone()
            if not row:
                return {}
            presupuesto_data = dict(row)

            # Corregido: Se cambió ip.notes por ip.notas según tu esquema real
            cur.execute(
                """SELECT ip.nombre_personalizado, ip.unidad, ip.cantidad, ip.precio_unitario, ip.total, ip.notas, c.nombre as cat_nombre
                   FROM items_en_presupuesto ip
                   LEFT JOIN categorias c ON ip.categoria_id = c.id
                   WHERE ip.presupuesto_id = %s;""",
                (presupuesto_id,)
            )
            items_list = []
            for r in cur.fetchall():
                items_list.append({
                    'nombre': r['nombre_personalizado'],
                    'unidad': r['unidad'],
                    'cantidad': r['cantidad'],
                    'precio_unitario': r['precio_unitario'],
                    'total': r['total'],
                    'notas': r.get('notas') or '',
                    'categoria': r['cat_nombre'] if r['cat_nombre'] else 'Sin Categoría'
                })
            presupuesto_data['items'] = items_list

            if presupuesto_data.get('cliente_id'):
                cur.execute("SELECT nombre FROM clientes WHERE id = %s;", (presupuesto_data['cliente_id'],))
                cli = cur.fetchone()
                if cli: presupuesto_data['cliente_nombre'] = cli['nombre']
                
            if presupuesto_data.get('lugar_trabajo_id'):
                cur.execute("SELECT nombre FROM lugares_trabajo WHERE id = %s;", (presupuesto_data['lugar_trabajo_id'],))
                lug = cur.fetchone()
                if lug: presupuesto_data['lugar_nombre'] = lug['nombre']

        return presupuesto_data
    except Exception as e:
        return {}
    finally:
        conn.close()

def save_edited_presupuesto(
    user_id: str, cliente_id: int, lugar_trabajo_id: int,
    descripcion: str, items_data: Dict[str, Any], total_general: float
) -> Optional[int]:
    formatted_items = {}
    for cat, d in items_data.items():
        formatted_items[cat] = {
            'mano_obra': d.get('mano_obra', 0.0),
            'items': [{
                'nombre_personalizado': i['nombre'],
                'unidad': i['unidad'],
                'cantidad': i['cantidad'],
                'precio_unitario': i['precio_unitario'],
                'notas': i.get('notas', '')
            } for i in d.get('items', [])]
        }
    return save_presupuesto_completo(user_id, cliente_id, lugar_trabajo_id, descripcion, formatted_items, total_general)

@st.cache_data(ttl=60) 
def get_presupuesto_detallado(presupuesto_id: int) -> dict:
    return get_presupuesto_para_editar(presupuesto_id)

# =================================================================
# COMPONENTE ESTADOS DE CUENTA
# =================================================================

@st.cache_data(ttl=60)
def get_estados_cuenta_usuario(user_id: str, filtros: dict = None) -> list:
    conn = get_connection()
    filtros = filtros or {}
    try:
        sql = """
            SELECT 
                ec.id, ec.usuario_uid, ec.cliente_id, ec.lugar_trabajo_id,
                ec.monto_base, ec.abono_monto, ec.total_neto, ec.fecha_emision, ec.pagado,
                c.nombre AS cliente_nombre,
                l.nombre AS lugar_nombre
            FROM estados_cuenta ec
            LEFT JOIN clientes c ON ec.cliente_id = c.id
            LEFT JOIN lugares_trabajo l ON ec.lugar_trabajo_id = l.id
            WHERE ec.usuario_uid = %s
        """
        params = [user_id]
        
        if filtros.get('cliente_id'):
            sql += " AND ec.cliente_id = %s"
            params.append(filtros['cliente_id'])
        if filtros.get('lugar_trabajo_id'):
            sql += " AND ec.lugar_trabajo_id = %s"
            params.append(filtros['lugar_trabajo_id'])
        if filtros.get('fecha_inicio'):
            sql += " AND ec.fecha_emision >= %s"
            params.append(filtros['fecha_inicio'].strftime('%Y-%m-%d'))
            
        sql += " ORDER BY ec.fecha_emision DESC;"
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            
            result = []
            for r in rows:
                d = dict(r)
                d['cliente'] = {'nombre': d.pop('cliente_nombre') or 'N/A'}
                d['lugar_trabajo'] = {'nombre': d.pop('lugar_nombre') or 'N/A'}
                result.append(d)
            return result
    except Exception as e:
        st.error(f"Error interno en get_estados_cuenta_usuario: {e}")
        return []
    finally:
        conn.close()

def toggle_estado_pago_ec(estado_id: int, nuevo_estado: bool) -> bool:
    conn = get_connection()
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
    finally:
        conn.close()

def delete_estado_cuenta(estado_id: int, user_id: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM estados_cuenta WHERE id = %s AND usuario_uid = %s RETURNING id;",
                (estado_id, user_id)
            )
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
    except Exception as e:
        conn.rollback()
        st.error(f"Error al eliminar estado de cuenta: {e}")
        return False
    finally:
        conn.close()