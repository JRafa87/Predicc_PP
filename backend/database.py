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


# --- Función para actualizar en Supabase ---

def actualizar_registro(id_registro, nuevos_valores):
    try:
        st.write("🆔 ID que se intenta actualizar:", id_registro)
        st.write("📦 Nuevos valores que se intentan guardar:", nuevos_valores)

        # Ejecutar la actualización forzada
        response = (
            supabase
            .table("registros_pp")
            .update(nuevos_valores)
            .eq("id", id_registro)
            .select("*")  # Devuelve la fila actualizada
            .execute()
        )

        # Mostrar la respuesta completa
        st.write("✅ Respuesta de Supabase:", response)

        # Validar si se actualizó algo
        if response.data:
            st.success("🎉 Registro actualizado correctamente.")
        else:
            st.warning("⚠️ La operación se ejecutó, pero no se actualizó ningún registro. Verifica si el ID existe o si los datos son iguales.")

        return response

    except Exception as e:
        st.error(f"❌ Error actualizando el registro: {e}")
        return None



