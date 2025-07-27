import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
from backend.database import obtener_registros, eliminar_registro, actualizar_registro, guardar
from backend.loaders import load_all_models
from backend.predictors import predecir
from backend.utils import cultivos as cultivo_dict
from datetime import datetime
import pytz

st.set_page_config(page_title="Gestor de Registros", layout="wide")
st.title("📋 Gestor de Registros de Predicción")

# Cargar registros desde Supabase
registros = obtener_registros()
if registros.empty:
    st.info("No hay registros disponibles.")
    st.stop()

df = pd.DataFrame(registros)

# Mostrar tabla
with st.expander("📑 Ver todos los registros", expanded=True):
    st.dataframe(df, use_container_width=True)

# Selección de registro por ID
st.subheader("🔍 Seleccionar un registro para editar o eliminar")

# Crear lista de selección: mostrar id y lugar (o lat,lon si no hay lugar)
opciones = [
    f"{row['id']} | {row.get('lugar') or f'{row.get('latitud', 0):.3f},{row.get('longitud', 0):.3f}'}"
    for _, row in df.iterrows()
]

seleccion = st.selectbox("Selecciona un registro:", opciones)
id_sel = int(seleccion.split(" | ")[0])
registro_sel = df[df["id"] == id_sel].iloc[0]

# Mostrar datos actuales
with st.expander("📌 Datos actuales del registro"):
    st.write(registro_sel)

encoders = load_all_models()
# Bloque de edición
with st.expander("✏️ Editar registro", expanded=True):
    # Función auxiliar para campos de entrada
    def input_field(key, valor_actual, tipo="numerico", opciones=None, enabled=True, encoders=None):
        ...
        if tipo == "categorico" and opciones is None:
             opciones = list(encoders[key].classes_)

    # Campos a editar
    campos = {
        "tipo_suelo": (registro_sel["tipo_suelo"], "categorico"),
        "pH": (registro_sel["pH"], "numerico"),
        "materia_organica": (registro_sel["materia_organica"], "numerico"),
        "conductividad": (registro_sel["conductividad"], "numerico"),
        "nitrogeno": (registro_sel["nitrogeno"], "numerico"),
        "fosforo": (registro_sel["fosforo"], "numerico"),
        "potasio": (registro_sel["potasio"], "numerico"),
        "humedad": (registro_sel["humedad"], "numerico"),
        "densidad": (registro_sel["densidad"], "numerico"),
        "condiciones_clima": (registro_sel["condiciones_clima"], "categorico"),
        "altitud": (registro_sel["altitud"], "numerico"),
        "temperatura": (registro_sel["temperatura"], "numerico"),
        "evapotranspiracion": (registro_sel["evapotranspiracion"], "numerico"),
        "mes": (registro_sel["mes"], "numerico"),
        "lugar": (registro_sel.get("lugar", ""), "categorico"),
        "latitud": (registro_sel.get("latitud", 0.0), "numerico"),
        "longitud": (registro_sel.get("longitud", 0.0), "numerico")
    }

    # Guardar nuevos valores
    nuevos_valores = {}
    for campo, (val, tipo) in campos.items():
        nuevos_valores[campo] = input_field(
            campo.replace("_", " ").capitalize(),
            key=f"{campo}_{id_sel}",
            value=val,
            tipo=tipo,
            enabled=registro_sel["prediccion"],
            encoders=encoders
        )

    # Botón de actualización
    if registro_sel["prediccion"] and st.button("🔁 Actualizar registro"):
        cambios = any(round(nuevos_valores[k], 2) != round(registro_sel[k], 2) for k in nuevos_valores)
        if not cambios:
            st.info("ℹ️ No se detectaron cambios. El registro no fue actualizado.")
        else:
            modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders = load_all_models()
            tipo_suelo = encoders["tipo_suelo"].transform([nuevos_valores["tipo_suelo"]])[0]
            condiciones_clima = encoders["condiciones_clima"].transform([nuevos_valores["condiciones_clima"]])[0]

            input_df = pd.DataFrame([{
                **nuevos_valores,
                "tipo_suelo": tipo_suelo,
                "condiciones_clima": condiciones_clima
            }])

            fert_pred, cult_pred_idx = predecir(input_df, modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders)
            cultivo_pred = cultivo_dict.get(cult_pred_idx, "Desconocido")

            tz = pytz.timezone("America/Lima")
            fecha_actual = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            actualizar_registro(id_sel, {
                **nuevos_valores,
                "fertilidad": int(fert_pred),
                "cultivo": cultivo_pred,
                "fecha": fecha_actual
            })

            st.success("✅ Registro actualizado correctamente.")
            st.rerun()

# Eliminación
with st.expander("🗑️ Eliminar registro"):
    if st.button("❌ Confirmar eliminación"):
        eliminar_registro(id_sel)
        st.warning("Registro eliminado.")
        st.rerun()







