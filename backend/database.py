from supabase import create_client
import os
from datetime import datetime
import streamlit as st
import pytz
import pandas as pd

# Conexión a Supabase usando st.secrets o variables de entorno
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["anon_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar(data_dict):
    """Guarda una predicción en la tabla registros_pp."""
    try:
        tz = pytz.timezone("America/Lima")
        data_dict["fecha_ingreso"] = datetime.now(tz).strftime("%Y-%m-%d")
        data_dict["prediccion"] = True
        response = supabase.table("registros_pp").insert(data_dict).execute()
        st.success("✅ Registro guardado exitosamente.")
        return response
    except Exception as e:
        st.error(f"❌ Error al insertar en Supabase: {e}")
        return None


def obtener_registros():
    """Obtiene todos los registros ordenados por fecha."""
    try:
        response = supabase.table("registros_pp").select("*").order("fecha_ingreso", desc=True).execute()
        return pd.DataFrame(response.data)
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
    """Actualiza un registro existente por su ID y controla errores correctamente."""
    try:
        st.write("📝 Intentando actualizar ID:", id_registro)
        st.write("🔄 Datos nuevos:", nuevos_datos)

        response = (
            supabase.table("registros_pp")
            .update(nuevos_datos)
            .eq("id", id_registro)
            .execute()
        )

        st.write("📡 Respuesta de Supabase:", response)

        # Validación por tipo y estado
        if isinstance(response, dict) and response.get("status_code", 200) >= 400:
            st.error(f"❌ Error Supabase: {response.get('error')}")
            return False

        # Si no hay datos devueltos
        elif "data" in response and not response["data"]:
            st.warning("⚠️ No se actualizó ningún registro. Verifica si el ID existe o si no cambiaste los datos.")
            return False

        # Actualización exitosa
        else:
            st.success(f"✅ Registro con ID {id_registro} actualizado correctamente.")
            return True

    except Exception as e:
        st.exception(f"⚠️ Excepción inesperada: {e}")
        return False




