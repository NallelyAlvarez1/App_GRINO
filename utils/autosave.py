 # utils/autosave.py
import json
import os
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

class AutoSaveManager:
    def __init__(self, user_id: str, draft_key: str = "draft_presupuesto"):
        self.user_id = user_id
        self.draft_key = f"{draft_key}_{user_id}"
        self.draft_file = f"drafts/{user_id}_draft.json"
        self.last_save_time = None
        
        # Crear directorio de drafts si no existe
        os.makedirs("drafts", exist_ok=True)
    
    def save_draft(self, draft_data: Dict[str, Any]) -> bool:
        """Guarda el borrador en session_state y archivo local"""
        try:
            # Agregar metadata
            draft_with_meta = {
                **draft_data,
                "_metadata": {
                    "user_id": self.user_id,
                    "last_saved": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            # Guardar en session_state
            st.session_state[self.draft_key] = draft_with_meta
            
            # Guardar en archivo
            with open(self.draft_file, "w", encoding="utf-8") as f:
                json.dump(draft_with_meta, f, ensure_ascii=False, indent=2)
            
            self.last_save_time = datetime.now()
            return True
            
        except Exception as e:
            st.error(f"Error guardando borrador: {e}")
            return False
    
    def load_draft(self) -> Optional[Dict[str, Any]]:
        """Carga el borrador desde session_state o archivo local"""
        try:
            # 1. Prioridad: session_state
            if self.draft_key in st.session_state:
                draft = st.session_state[self.draft_key]
                return draft
            
            # 2. Archivo local
            if os.path.exists(self.draft_file):
                with open(self.draft_file, "r", encoding="utf-8") as f:
                    draft = json.load(f)
                return draft
            
            return None
            
        except Exception as e:
            st.error(f"Error cargando borrador: {e}")
            return None
    
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
    
    def has_draft(self) -> bool:
        """Verifica si existe un borrador guardado"""
        return (self.draft_key in st.session_state or 
                os.path.exists(self.draft_file))
    
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

def capture_current_state() -> Dict[str, Any]:
    """Captura el estado actual del presupuesto para guardarlo como borrador"""
    return {
        "cliente_id": st.session_state.get('cliente_id'),
        "lugar_trabajo_id": st.session_state.get('lugar_trabajo_id'),
        "descripcion": st.session_state.get('descripcion', ''),
        # Guardar ambas claves para compatibilidad
        "categorias": st.session_state.get('categorias', {}),
        "categorías": st.session_state.get('categorias', {}),  # Duplicado para el preview
        "items_data": st.session_state.get('items_data', {}),
        "cliente_nombre": st.session_state.get('cliente_nombre', ''),
        "lugar_nombre": st.session_state.get('lugar_nombre', ''),
        "trabajos_simples": st.session_state.get('trabajos_simples', [])
    }

def restore_draft_state(draft: Dict[str, Any]):
    """Restaura el estado desde un borrador"""
    try:
        # Restaurar datos básicos
        st.session_state['cliente_id'] = draft.get('cliente_id')
        st.session_state['lugar_trabajo_id'] = draft.get('lugar_trabajo_id')
        st.session_state['descripcion'] = draft.get('descripcion', '')
        
        # Restaurar categorías (priorizar 'categorias' que es lo que usa la app)
        if 'categorias' in draft:
            st.session_state['categorias'] = draft['categorias']
        elif 'categorías' in draft:
            st.session_state['categorias'] = draft['categorías']
        
        # Restaurar items_data (es lo más importante)
        if 'items_data' in draft and draft['items_data']:
            st.session_state['items_data'] = draft['items_data']
            # También sincronizar con categorias si es necesario
            if not st.session_state.get('categorias'):
                st.session_state['categorias'] = draft['items_data']
        
        # Restaurar trabajos_simples
        if 'trabajos_simples' in draft:
            st.session_state['trabajos_simples'] = draft['trabajos_simples']

        # Restaurar nombres
        if 'cliente_nombre' in draft:
            st.session_state['cliente_nombre'] = draft['cliente_nombre']
        if 'lugar_nombre' in draft:
            st.session_state['lugar_nombre'] = draft['lugar_nombre']

    except Exception as e:
        st.error(f"Error restaurando borrador: {e}")