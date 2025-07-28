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
def actualizar_registro(id_registro, nuevos_datos):
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

        if isinstance(response, dict) and response.get("status_code", 200) >= 400:
            st.session_state.update_error = f"❌ Error Supabase: {response.get('error')}"
        elif "data" in response and not response["data"]:
            st.session_state.update_error = "⚠️ Supabase no devolvió datos. Verifica si el ID existe o si hubo algún cambio real."
        else:
            st.session_state.update_success = f"✏️ Registro con ID {id_registro} actualizado correctamente."
        st.rerun()

    except Exception as e:
        st.session_state.update_error = f"⚠️ Excepción: {e}"
        st.rerun()

# --- Mostrar mensajes persistentes si existen ---
if "update_error" in st.session_state:
    st.error(st.session_state.update_error)
    del st.session_state.update_error

if "update_success" in st.session_state:
    st.success(st.session_state.update_success)
    del st.session_state.update_success

# --- Vista de actualización interactiva ---
st.title("🔧 Actualizar Registro")

id_registro = st.number_input("ID del registro a actualizar", min_value=1, step=1)

# Obtener datos actuales del registro
registro_actual = None
if id_registro:
    res = supabase.table("registros_pp").select("*").eq("id", id_registro).execute()
    if res and "data" in res and res["data"]:
        registro_actual = res["data"][0]

if registro_actual:
    st.subheader("📄 Datos actuales")
    st.json(registro_actual)

    # Campos editables
    nuevos_valores = {}
    campos_editables = ["tipo_suelo", "ph", "materia_organica", "conductividad", "nitrogeno", "fosforo", "potasio",
                        "humedad", "densidad", "altitud", "temperatura", "velocidad_viento", "direccion_viento",
                        "condiciones_clima", "probabilidad_precipitacion", "evapotranspiracion", "tipo_riego",
                        "volumen_agua", "mes", "region"]

    for campo in campos_editables:
        valor = st.text_input(campo, value=str(registro_actual.get(campo, "")))
        try:
            # Convertir a float si es número
            nuevos_valores[campo] = float(valor)
        except:
            nuevos_valores[campo] = valor

    # Recalcular predicción
    nueva_pred_fertilidad, nuevo_cultivo = predecir(nuevos_valores)
    st.info(f"🔍 Predicción nueva: Fertilidad = {nueva_pred_fertilidad}, Cultivo = {nuevo_cultivo}")

    if st.button("🧠 Comparar con predicción anterior"):
        st.session_state.pendiente_guardado = True
        st.session_state.nuevos_datos = nuevos_valores.copy()
        st.session_state.nuevos_datos["fertilidad"] = int(nueva_pred_fertilidad)
        st.session_state.nuevos_datos["cultivo"] = nuevo_cultivo
        st.session_state.nuevos_datos["fecha"] = fecha_actual_peru()
        st.session_state.pred_anterior = registro_actual["cultivo"]
        st.session_state.pred_nueva = nuevo_cultivo
        st.rerun()

# --- Confirmación persistente tras rerun ---
if st.session_state.get("pendiente_guardado"):
    st.warning(f"🔁 Cultivo anterior: {st.session_state.pred_anterior}")
    st.success(f"✅ Nueva predicción: {st.session_state.pred_nueva}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirmar y actualizar"):
            actualizar_registro(id_registro, st.session_state.nuevos_datos)

    with col2:
        if st.button("❌ Cancelar"):
            st.info("Actualización cancelada.")
            for key in ["pendiente_guardado", "nuevos_datos", "pred_anterior", "pred_nueva"]:
                st.session_state.pop(key, None)
            st.rerun()


