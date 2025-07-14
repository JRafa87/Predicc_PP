from supabase import create_client
import os
from datetime import datetime
import streamlit as st

# Conexión a Supabase usando st.secrets o variables de entorno
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["anon_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar(data_dict):
    """Guarda una predicción en la tabla registros_pp de Supabase."""
    data_dict["fecha_ingreso"] = datetime.now().date().isoformat()
    data_dict["prediccion"] = True
    try:
        response = supabase.table("registros_pp").insert(data_dict).execute()
        print("🟢 Supabase response:", response)
        st.write("🟢 Supabase response:", response)
        return response
    except Exception as e:
        print(f"❌ Error al insertar en Supabase: {e}")
        st.error(f"❌ Error al insertar en Supabase: {e}")
        return None
