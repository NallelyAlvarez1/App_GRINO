# utils/autosave.py
import json
import os
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

class AutoSaveManager:
    def __init__(self, user_id: str = None, draft_key: str = "draft_presupuesto"):
        # Si no hay user_id (recarga de página), intentar recuperar de un archivo temporal
        self.user_id = user_id or self._get_persistent_id()
        self.draft_key = f"{draft_key}_{self.user_id}"
        
        # Crear un identificador persistente basado en el navegador si no hay user_id
        if not user_id:
            self.persistent_id = self._get_or_create_persistent_id()
        else:
            self.persistent_id = user_id
            
        self.draft_file = f"drafts/{self.persistent_id}_draft.json"
        self.last_save_time = None
        
        # Crear directorio de drafts si no existe
        os.makedirs("drafts", exist_ok=True)
    
    def _get_persistent_id(self):
        """Intenta obtener un ID persistente de session_state o crea uno nuevo"""
        if 'persistent_session_id' not in st.session_state:
            # Crear un ID único para esta sesión del navegador
            import uuid
            st.session_state['persistent_session_id'] = str(uuid.uuid4())
        return st.session_state['persistent_session_id']
    
    def _get_or_create_persistent_id(self):
        """Obtiene o crea un ID persistente basado en el user_id o sesión"""
        if self.user_id:
            return self.user_id
        return self._get_persistent_id()
    
    def save_draft(self, draft_data: Dict[str, Any]) -> bool:
        """Guarda el borrador en session_state y archivo local"""
        try:
            # Agregar metadata
            draft_with_meta = {
                **draft_data,
                "_metadata": {
                    "user_id": self.user_id,  # Puede ser None en recarga
                    "persistent_id": self.persistent_id,
                    "last_saved": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            # Guardar en session_state (si existe)
            if self.user_id:
                st.session_state[self.draft_key] = draft_with_meta
            
            # SIEMPRE guardar en archivo (esto persiste recargas)
            with open(self.draft_file, "w", encoding="utf-8") as f:
                json.dump(draft_with_meta, f, ensure_ascii=False, indent=2)
            
            # También guardar una copia de respaldo con el username si está disponible
            if st.session_state.get('usuario'):
                backup_file = f"drafts/{st.session_state['usuario']}_draft.json"
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(draft_with_meta, f, ensure_ascii=False, indent=2)
            
            self.last_save_time = datetime.now()
            return True
            
        except Exception as e:
            st.error(f"Error guardando borrador: {e}")
            return False
    
    def load_draft(self) -> Optional[Dict[str, Any]]:
        """Carga el borrador desde session_state o archivo local"""
        try:
            # 1. Intentar cargar por user_id actual
            if self.user_id and self.draft_key in st.session_state:
                return st.session_state[self.draft_key]
            
            # 2. Intentar cargar por persistent_id
            if os.path.exists(self.draft_file):
                with open(self.draft_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            
            # 3. Intentar cargar por username
            if st.session_state.get('usuario'):
                username_file = f"drafts/{st.session_state['usuario']}_draft.json"
                if os.path.exists(username_file):
                    with open(username_file, "r", encoding="utf-8") as f:
                        return json.load(f)
            
            return None
            
        except Exception as e:
            st.error(f"Error cargando borrador: {e}")
            return None
    
    def has_draft(self) -> bool:
        """Verifica si existe un borrador guardado"""
        # Buscar en todas las posibles ubicaciones
        if self.user_id and self.draft_key in st.session_state:
            return True
        
        if os.path.exists(self.draft_file):
            return True
        
        if st.session_state.get('usuario'):
            username_file = f"drafts/{st.session_state['usuario']}_draft.json"
            if os.path.exists(username_file):
                return True
        
        return False
     
    def clear_draft(self) -> bool:
        """Elimina el borrador completamente"""
        try:
            # Eliminar de session_state
            st.session_state.pop(self.draft_key, None)
            
            # Eliminar archivo
            if os.path.exists(self.draft_file):
                os.remove(self.draft_file)
            
            return True
            
        except Exception as e:
            st.error(f"Error eliminando borrador: {e}")
            return False

    def get_draft_age(self) -> Optional[str]:
        """Obtiene hace cuánto tiempo se guardó el borrador"""
        try:
            if self.draft_key in st.session_state:
                draft = st.session_state[self.draft_key]
                saved_time = datetime.fromisoformat(draft["_metadata"]["last_saved"])
            elif os.path.exists(self.draft_file):
                with open(self.draft_file, "r", encoding="utf-8") as f:
                    draft = json.load(f)
                saved_time = datetime.fromisoformat(draft["_metadata"]["last_saved"])
            else:
                return None
            
            delta = datetime.now() - saved_time
            minutes = int(delta.total_seconds() / 60)
            
            if minutes < 1:
                return "hace unos segundos"
            elif minutes == 1:
                return "hace 1 minuto"
            elif minutes < 60:
                return f"hace {minutes} minutos"
            else:
                hours = minutes // 60
                return f"hace {hours} hora{'s' if hours > 1 else ''}"
                
        except:
            return "tiempo desconocido"

# Funciones de utilidad (opcionales - puedes ponerlas aquí o en el archivo principal)
# utils/autosave.py

# utils/autosave.py

def capture_current_state() -> Dict[str, Any]:
    """Captura el estado actual del presupuesto para guardarlo como borrador"""
    
    state = {
        "cliente_id": st.session_state.get('cliente_id'),
        "lugar_trabajo_id": st.session_state.get('lugar_trabajo_id'),
        "descripcion": st.session_state.get('descripcion', ''),
        "cliente_nombre": st.session_state.get('cliente_nombre', ''),
        "lugar_nombre": st.session_state.get('lugar_nombre', ''),
    }
    
    # DEBUG: Verificar específicamente items_data y categorias
    items_data = st.session_state.get('items_data', {})
    categorias = st.session_state.get('categorias', {})
        
    # Guardar ambas
    state["items_data"] = items_data
    state["categorias"] = categorias
    state["categorías"] = categorias  # Para compatibilidad
    
    # DEBUG: Verificar trabajos_simples
    trabajos = st.session_state.get('trabajos_simples', [])
    
    state["trabajos_simples"] = trabajos
    
    return state

def restore_draft_state(draft: Dict[str, Any]):
    """Restaura el estado desde un borrador"""
    try:
        # Restaurar datos básicos
        st.session_state['cliente_id'] = draft.get('cliente_id')
        st.session_state['lugar_trabajo_id'] = draft.get('lugar_trabajo_id')
        st.session_state['descripcion'] = draft.get('descripcion', '')
        
        # Restaurar items
        if 'items_data' in draft and draft['items_data']:
            st.session_state['items_data'] = draft['items_data']
            st.session_state['categorias'] = draft['items_data']
        elif 'categorias' in draft and draft['categorias']:
            st.session_state['categorias'] = draft['categorias']
            st.session_state['items_data'] = draft['categorias']
        
        # Restaurar nombres
        if 'cliente_nombre' in draft:
            st.session_state['cliente_nombre'] = draft['cliente_nombre']
        if 'lugar_nombre' in draft:
            st.session_state['lugar_nombre'] = draft['lugar_nombre']
        
        # Restaurar trabajos simples
        if 'trabajos_simples' in draft:
            st.session_state['trabajos_simples'] = draft['trabajos_simples']
        
        st.success("✅ Borrador restaurado correctamente")

    except Exception as e:
        st.error(f"Error restaurando borrador: {e}")