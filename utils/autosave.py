# utils/autosave.py
import json
import os
import time
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

class AutoSaveManager:
    def __init__(self, user_id: str = None, draft_key: str = "draft_presupuesto"):
        self.user_id = user_id
        self.draft_key = f"{draft_key}_{user_id}" if user_id else draft_key
        
        # Siempre tener un persistent_id
        if 'persistent_session_id' in st.session_state:
            self.persistent_id = st.session_state['persistent_session_id']
        else:
            self.persistent_id = str(uuid.uuid4())
            st.session_state['persistent_session_id'] = self.persistent_id
            
        # El archivo siempre usa persistent_id para sobrevivir recargas
        self.draft_file = f"drafts/{self.persistent_id}_draft.json"
        self.last_save_time = None
        
        os.makedirs("drafts", exist_ok=True)
    
    def save_draft(self, draft_data: Dict[str, Any]) -> bool:
        """Guarda el borrador en archivo local SIEMPRE"""
        try:
            draft_with_meta = {
                **draft_data,
                "_metadata": {
                    "user_id": self.user_id,
                    "persistent_id": self.persistent_id,
                    "username": st.session_state.get('usuario'),
                    "last_saved": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            # Guardar en archivo (SIEMPRE)
            with open(self.draft_file, "w", encoding="utf-8") as f:
                json.dump(draft_with_meta, f, ensure_ascii=False, indent=2)
            
            # También guardar copia con username si existe
            if st.session_state.get('usuario'):
                backup_file = f"drafts/{st.session_state['usuario']}_draft.json"
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(draft_with_meta, f, ensure_ascii=False, indent=2)
            
            # Guardar en session_state si hay user_id
            if self.user_id:
                st.session_state[self.draft_key] = draft_with_meta
            
            self.last_save_time = datetime.now()
            return True
            
        except Exception as e:
            st.error(f"Error guardando borrador: {e}")
            return False
    
    def load_draft(self) -> Optional[Dict[str, Any]]:
        """Carga el borrador desde archivo local"""
        try:
            # 1. Intentar por persistent_id (más confiable)
            if os.path.exists(self.draft_file):
                with open(self.draft_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            
            # 2. Intentar por username
            if st.session_state.get('usuario'):
                username_file = f"drafts/{st.session_state['usuario']}_draft.json"
                if os.path.exists(username_file):
                    return json.load(open(username_file, "r", encoding="utf-8"))
            
            return None
            
        except Exception as e:
            st.error(f"Error cargando borrador: {e}")
            return None
    
    def has_draft(self) -> bool:
        """Verifica si existe un borrador guardado"""
        # Verificar archivo por persistent_id
        if os.path.exists(self.draft_file):
            return True
        
        # Verificar por username
        if st.session_state.get('usuario'):
            username_file = f"drafts/{st.session_state['usuario']}_draft.json"
            if os.path.exists(username_file):
                return True
        
        return False
     
    def clear_draft(self) -> bool:
        """Elimina el borrador completamente"""
        try:
            # Eliminar archivo principal
            if os.path.exists(self.draft_file):
                os.remove(self.draft_file)
            
            # Eliminar backup por username
            if st.session_state.get('usuario'):
                username_file = f"drafts/{st.session_state['usuario']}_draft.json"
                if os.path.exists(username_file):
                    os.remove(username_file)
            
            return True
            
        except Exception as e:
            st.error(f"Error eliminando borrador: {e}")
            return False

    def get_draft_age(self) -> Optional[str]:
        """Obtiene hace cuánto tiempo se guardó el borrador"""
        try:
            draft = self.load_draft()
            if draft and "_metadata" in draft and "last_saved" in draft["_metadata"]:
                saved_time = datetime.fromisoformat(draft["_metadata"]["last_saved"])
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
            return None
        except:
            return "tiempo desconocido"

def capture_current_state() -> Dict[str, Any]:
    """Captura el estado actual del presupuesto"""
    state = {
        "cliente_id": st.session_state.get('cliente_id'),
        "lugar_trabajo_id": st.session_state.get('lugar_trabajo_id'),
        "descripcion": st.session_state.get('descripcion', ''),
        "cliente_nombre": st.session_state.get('cliente_nombre', ''),
        "lugar_nombre": st.session_state.get('lugar_nombre', ''),
        "items_data": st.session_state.get('items_data', {}),
        "categorias": st.session_state.get('categorias', {}),
        "categorías": st.session_state.get('categorias', {}),
        "trabajos_simples": st.session_state.get('trabajos_simples', [])
    }
    return state



def restore_draft_state(draft: Dict[str, Any]):
    """Restaura el estado desde un borrador y fuerza la actualización de la UI"""
    try:
        # Limpiar estados anteriores que puedan interferir
        keys_to_clear = ['categorias', 'items_data', 'trabajos_simples']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Restaurar datos básicos
        st.session_state['cliente_id'] = draft.get('cliente_id')
        st.session_state['lugar_trabajo_id'] = draft.get('lugar_trabajo_id')
        st.session_state['descripcion'] = draft.get('descripcion', '')
        st.session_state['cliente_nombre'] = draft.get('cliente_nombre', '')
        st.session_state['lugar_nombre'] = draft.get('lugar_nombre', '')
        
        # Restaurar items (priorizar items_data)
        items_data = draft.get('items_data', {}) or draft.get('categorias', {})
        if items_data:
            st.session_state['items_data'] = items_data
            st.session_state['categorias'] = items_data
            
            # Forzar la inicialización de items en cada categoría
            for cat_name, cat_data in items_data.items():
                if isinstance(cat_data, dict):
                    if 'items' not in cat_data:
                        cat_data['items'] = []
                    if 'mano_obra' not in cat_data:
                        cat_data['mano_obra'] = 0
        
        # Restaurar trabajos simples
        trabajos = draft.get('trabajos_simples', [])
        if trabajos:
            st.session_state['trabajos_simples'] = trabajos
        
        # Marcar que se ha restaurado un borrador
        st.session_state['draft_restored'] = True
        
        # Forzar recarga completa para que todos los componentes se actualicen
        st.success("✅ Borrador restaurado correctamente. Recargando...")
        time.sleep(1)  # Pequeña pausa para que se vea el mensaje
        st.rerun()
        
    except Exception as e:
        st.error(f"Error restaurando borrador: {e}")
        return False