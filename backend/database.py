from supabase import create_client
import os
from datetime import datetime
import streamlit as st
import pytz
import pandas as pd

# Conexión a Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["anon_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar(data_dict):
    """Guarda una predicción en la tabla registros_pp."""
    try:
        tz = pytz.timezone("America/Lima")
        data_dict["fecha_ingreso"] = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        data_dict["prediccion"] = True
        
        # Insertar en Supabase
        response, error = supabase.table("registros_pp").insert(data_dict).execute()
        
        if error:
            st.error(f"❌ Error Supabase: {error}")
            return None
            
        st.success("✅ Registro guardado exitosamente.")
        return response
    except Exception as e:
        st.error(f"❌ Error al insertar en Supabase: {e}")
        return None

def obtener_registros():
    """Obtiene todos los registros ordenados por fecha."""
    try:
        # Obtener TODOS los registros sin límite
        response = supabase.table("registros_pp").select("*").execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Ordenar por ID descendente
            df = df.sort_values("id", ascending=False)
            return df
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Error al obtener registros: {e}")
        return pd.DataFrame()

def eliminar_registro(id_registro):
    """Elimina un registro por su ID."""
    try:
        supabase.table("registros_pp").delete().eq("id", id_registro).execute()
        st.success(f"🗑️ Registro con ID {id_registro} eliminado correctamente.")
    except Exception as e:
        st.error(f"❌ Error al eliminar registro: {e}")

def actualizar_registro(id_registro, nuevos_datos):
    """Actualiza un registro existente por su ID."""
    try:
        # Ejecutar actualización
        response, error = supabase.table("registros_pp").update(nuevos_datos).eq("id", id_registro).execute()
        
        if error:
            st.error(f"❌ Error Supabase: {error}")
            return None
            
        # Verificar si realmente se actualizó algo
        if response and len(response.data) > 0:
            st.success(f"✏️ Registro con ID {id_registro} actualizado correctamente.")
            return response
        else:
            st.warning("⚠️ No se detectaron cambios o el registro no existe")
            return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return None



