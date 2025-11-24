import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple



# =================================================================
# FUNCIÓN DE INICIACIÓN DE BASE DE DATOS Y CACHÉ
# =================================================================

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

# =================================================================
# LECTURA DE ENTIDADES (CACHÉ)
# =================================================================

@st.cache_data(ttl=600)
def get_clientes(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de clientes (id, nombre) del usuario logueado."""
    supabase = get_supabase_client()
    try:
        response = supabase.from_('clientes').select('id, nombre').eq('creado_por', user_id).order('nombre', desc=False).execute()
        if response and response.data:
            return [(c['id'], c['nombre']) for c in response.data]
        return []
    except Exception as e:
        st.error(f"Error al obtener clientes: {e}")
        return []

@st.cache_data(ttl=600)
def get_lugares_trabajo(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de lugares de trabajo (id, nombre) del usuario logueado."""
    supabase = get_supabase_client()
    try:
        response = supabase.from_('lugares_trabajo').select('id, nombre').eq('creado_por', user_id).order('nombre', desc=False).execute()
        if response and response.data:
            return [(l['id'], l['nombre']) for l in response.data]
        return []
    except Exception as e:
        st.error(f"Error al obtener lugares de trabajo: {e}")
        return []

@st.cache_data(ttl=600)
def get_categorias(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene la lista de categorías (id, nombre) del usuario logueado."""
    supabase = get_supabase_client()
    try:
        response = supabase.from_('categorias').select('id, nombre').eq('creado_por', user_id).order('nombre', desc=False).execute()
        if response.data:
            return [(d['id'], d['nombre']) for d in response.data]
        return []
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

# =================================================================
# GESTIÓN DE ENTIDADES
# =================================================================

def create_cliente(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo cliente para el usuario."""
    supabase = get_supabase_client()
    try:
        alias_base = nombre.strip().lower().replace(' ', '_')[:45]
        alias = alias_base
        counter = 1
        
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
    except Exception as e:
        st.error(f"Error al crear cliente: {e}")
        if '23505' in str(e) and 'clientes_pkey' in str(e):
            st.error("⚠️ Error de secuencia: Contacta al administrador para resetear la secuencia de IDs de clientes")
        return None

def create_lugar_trabajo(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo lugar de trabajo para el usuario."""
    supabase = get_supabase_client()
    try:
        nombre_base = nombre.strip()
        nombre_final = nombre_base
        counter = 1
        
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
    except Exception as e:
        st.error(f"Error al crear lugar de trabajo: {e}")
        if '23505' in str(e) and 'lugares_trabajo_pkey' in str(e):
            st.error("⚠️ Error de secuencia: La secuencia de IDs de lugares de trabajo está desincronizada")
        return None

def create_categoria(nombre: str, user_id: str) -> Optional[int]:
    """Crea una nueva categoría para el usuario."""
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
    except Exception as e:
        st.error(f"Error al crear categoría: {e}")
        return None

def update_cliente(cliente_id: int, nuevo_nombre: str, user_id: str) -> bool:
    """Actualiza el nombre de un cliente existente"""
    supabase = get_supabase_client()
    try:
        response = supabase.from_('clientes').update({'nombre': nuevo_nombre})\
            .eq('id', cliente_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al actualizar cliente: {e}")
        return False

def delete_cliente(cliente_id: int, user_id: str) -> bool:
    """
    Elimina un cliente junto con todos sus presupuestos e items asociados
    (gracias a ON DELETE CASCADE en la base de datos).
    """
    supabase = get_supabase_client()
    try:
        response = supabase.from_('clientes').delete()\
            .eq('id', cliente_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al eliminar cliente: {e}")
        return False

def update_lugar_trabajo(lugar_id: int, nuevo_nombre: str, user_id: str) -> bool:
    """Actualiza el nombre de un lugar de trabajo existente"""
    supabase = get_supabase_client()
    try:
        response = supabase.from_('lugares_trabajo').update({'nombre': nuevo_nombre})\
            .eq('id', lugar_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al actualizar lugar de trabajo: {e}")
        return False

def delete_lugar_trabajo(lugar_id: int, user_id: str) -> bool:
    """
    Elimina un lugar de trabajo junto con todos sus presupuestos e items asociados
    (gracias a ON DELETE CASCADE en la base de datos).
    """
    supabase = get_supabase_client()
    try:
        response = supabase.from_('lugares_trabajo').delete()\
            .eq('id', lugar_id).eq('creado_por', user_id).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Error al eliminar lugar de trabajo: {e}")
        return False

def get_presupuestos_por_cliente(cliente_id: int) -> list[dict]:
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

    except Exception as e:
        print(f"Error al obtener presupuestos del cliente {cliente_id}: {e}")
        return []
def get_presupuestos_por_lugar(lugar_id: int) -> list[dict]:
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

    except Exception as e:
        print(f"Error al obtener presupuestos del lugar {lugar_id}: {e}")
        return []

# =================================================================
# GESTIÓN DE PRESUPUESTOS
# =================================================================

def get_presupuestos_usuario(user_id: str, filtros: dict) -> list:
    """
    Obtiene los presupuestos del usuario con filtros aplicados.
    """
    supabase = get_supabase_client()
    
    query = supabase.from_('presupuestos').select(
        'id, total, fecha_creacion, descripcion, notas, '  # INCLUIR 'notas'
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

    except Exception as e:
        st.error(f"Error al guardar presupuesto completo: {e}")
        return None
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
    supabase = get_supabase_client()
    
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
        
        # Depuración: imprimir la respuesta
        print("Respuesta de Supabase (presupuestos):", response)
        print("Datos:", response.data)
        
        return response.data if response.data else []
    
    except Exception as e:
        print(f"Error en get_presupuestos_para_edicion: {e}")
        return []


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
                items_list.append({
                    'nombre': item['nombre_personalizado'],
                    'unidad': item['unidad'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'total': item['total'],
                    'notas': item['notas'],
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
        
    except Exception as e:
        print(f"Error en get_presupuesto_para_editar: {e}")
        return {}
    
def save_edited_presupuesto(
    user_id: str,
    cliente_id: int,
    lugar_trabajo_id: int,
    descripcion: str,
    items_data: Dict[str, Any],
    total_general: float,
    presupuesto_original_id: int = None  # NUEVO PARÁMETRO
) -> Optional[int]:
    """
    Crea un NUEVO presupuesto a partir de datos editados, con control de versiones en 'notas'.
    """
    supabase = get_supabase_client()

    try:
        # --- DETERMINAR VERSIÓN USANDO LA COLUMNA 'notas' ---
        notas_con_version = ""  # Empezamos vacío
        
        if presupuesto_original_id:
            # Buscar el presupuesto original para ver su versión
            response_original = supabase.table('presupuestos')\
                .select('notas')\
                .eq('id', presupuesto_original_id)\
                .execute()
            
            if response_original.data:
                notas_original = response_original.data[0].get('notas', '')
                
                if 'V' in notas_original:
                    # Extraer la versión actual y incrementar
                    import re
                    match = re.search(r'V(\d+)', notas_original)
                    if match:
                        version_actual = int(match.group(1))
                        nueva_version = version_actual + 1
                        # Reemplazar la versión anterior
                        notas_con_version = re.sub(r'V\d+', f'V{nueva_version}', notas_original)
                    else:
                        # Si tiene 'V' pero no número, agregar V2
                        notas_con_version = f"{notas_original} | V2"
                else:
                    # Es la primera edición (V2)
                    if notas_original:
                        notas_con_version = f"{notas_original} | V2"
                    else:
                        notas_con_version = "V2"
            else:
                # No se encontró el original, empezar con V2
                notas_con_version = "V2"
        else:
            # Es un presupuesto completamente nuevo (V1)
            notas_con_version = "V1"

        # --- FASE 1: Crear NUEVO registro en presupuestos ---
        nuevo_presupuesto_data = {
            'cliente_id': cliente_id,
            'lugar_trabajo_id': lugar_trabajo_id,
            'descripcion': descripcion,  # Descripción original siempre
            'notas': notas_con_version,  # Control de versiones aquí
            'total': float(total_general),
            'creado_por': user_id,
            'presupuesto_original_id': presupuesto_original_id  # Relacionar con el original
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
                items_list.append({
                    'nombre': item['nombre_personalizado'],
                    'unidad': item['unidad'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'total': item['total'],
                    'notas': item['notas'],
                    # Maneja el caso de que la categoría sea nula o no se encuentre
                    'categoria': item['categoria']['nombre'] if item.get('categoria') and item['categoria'] else 'Sin Categoría'
                })
                
        presupuesto_data['items'] = items_list
        
        return presupuesto_data
    
    except Exception as e:
        st.error(f"Error al obtener detalle del presupuesto: {e}")
        return {}
import streamlit as st

@st.cache_data
def save_draft(draft: dict):
    """Guarda un borrador local persistente."""
    return draft

@st.cache_data
def load_draft() -> dict:
    """Carga un borrador guardado si existe."""
    return {}
