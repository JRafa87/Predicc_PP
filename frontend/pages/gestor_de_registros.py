import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import numpy as np
from backend.database import obtener_registros, eliminar_registro, actualizar_registro
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
df = df.sort_values(by="id", ascending=False)

# Mostrar tabla
with st.expander("📑 Ver todos los registros", expanded=True):
    st.dataframe(df, use_container_width=True)

# Selección de registro por ID
st.subheader("🔍 Seleccionar un registro para editar o eliminar")
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

# Bloque de edición
with st.expander("✏️ Editar registro", expanded=True):
    # Cargar modelos y encoders
    modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders = load_all_models()
    
    # Función auxiliar para generar campos de entrada
    def input_field(label, valor_actual, tipo="numerico", opciones=None, key=None, enabled=True):
        if not enabled:
            st.text_input(label, value=str(valor_actual), disabled=True, key=key)
            return valor_actual

        if tipo == "numerico":
            return st.number_input(label, value=float(valor_actual), key=key)
        elif tipo == "categorico":
            return st.selectbox(label, opciones, index=opciones.index(valor_actual), key=key)
        else:
            return st.text_input(label, value=str(valor_actual), key=key)

    # Campos a editar
    campos = {
        "tipo_suelo": (registro_sel["tipo_suelo"], "categorico", list(encoders["tipo_suelo"].classes_)),
        "pH": (registro_sel["pH"], "numerico"),
        "materia_organica": (registro_sel["materia_organica"], "numerico"),
        "conductividad": (registro_sel["conductividad"], "numerico"),
        "nitrogeno": (registro_sel["nitrogeno"], "numerico"),
        "fosforo": (registro_sel["fosforo"], "numerico"),
        "potasio": (registro_sel["potasio"], "numerico"),
        "humedad": (registro_sel["humedad"], "numerico"),
        "densidad": (registro_sel["densidad"], "numerico"),
        "condiciones_clima": (registro_sel["condiciones_clima"], "categorico", list(encoders["condiciones_clima"].classes_)),
        "altitud": (registro_sel["altitud"], "numerico"),
        "temperatura": (registro_sel["temperatura"], "numerico"),
        "evapotranspiracion": (registro_sel["evapotranspiracion"], "numerico"),
        "mes": (registro_sel["mes"], "numerico"),
        "lugar": (registro_sel.get("lugar", ""), "text"),
        "latitud": (registro_sel.get("latitud", 0.0), "numerico"),
        "longitud": (registro_sel.get("longitud", 0.0), "numerico")
    }

    nuevos_valores = {}
    for campo, datos in campos.items():
        valor_actual = datos[0]
        tipo = datos[1]
        opciones = datos[2] if len(datos) > 2 else None
        nuevos_valores[campo] = input_field(
            campo.replace("_", " ").capitalize(),
            valor_actual,
            tipo=tipo,
            opciones=opciones,
            key=campo,
            enabled=registro_sel["prediccion"]
        )

    # Botón de actualización
    if registro_sel["prediccion"] and st.button("🔁 Actualizar registro"):
        # Verificar si hay cambios reales
        cambios = False
        
        for campo in campos:
            # Manejo especial para valores nulos/NaN
            if pd.isna(registro_sel[campo]) and pd.isna(nuevos_valores[campo]):
                continue
            elif pd.isna(registro_sel[campo]) or pd.isna(nuevos_valores[campo]):
                cambios = True
                break
            
            # Comparación numérica con tolerancia
            if isinstance(registro_sel[campo], (int, float, np.number)) and \
               isinstance(nuevos_valores[campo], (int, float)):
                if abs(registro_sel[campo] - nuevos_valores[campo]) > 1e-5:
                    cambios = True
                    break
            # Comparación de texto
            elif str(registro_sel[campo]) != str(nuevos_valores[campo]):
                cambios = True
                break
        
        if not cambios:
            st.info("ℹ️ No se detectaron cambios. El registro no fue actualizado.")
        else:
            # Convertir valores de texto a numéricos para predicción
            tipo_suelo_code = encoders["tipo_suelo"].transform([nuevos_valores["tipo_suelo"]])[0]
            condiciones_clima_code = encoders["condiciones_clima"].transform([nuevos_valores["condiciones_clima"]])[0]

            # Crear DataFrame para predicción
            input_df = pd.DataFrame([{
                "tipo_suelo": tipo_suelo_code,
                "pH": nuevos_valores["pH"],
                "materia_organica": nuevos_valores["materia_organica"],
                "conductividad": nuevos_valores["conductividad"],
                "nitrogeno": nuevos_valores["nitrogeno"],
                "fosforo": nuevos_valores["fosforo"],
                "potasio": nuevos_valores["potasio"],
                "humedad": nuevos_valores["humedad"],
                "densidad": nuevos_valores["densidad"],
                "altitud": nuevos_valores["altitud"],
                "temperatura": nuevos_valores["temperatura"],
                "condiciones_clima": condiciones_clima_code,
                "mes": nuevos_valores["mes"],
                "evapotranspiracion": nuevos_valores["evapotranspiracion"]
            }])

            # Realizar nueva predicción
            fert_pred, cult_pred_idx = predecir(input_df, modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders)
            cultivo_pred = cultivo_dict.get(cult_pred_idx, "Desconocido")

            # Preparar datos para actualizar
            tz = pytz.timezone("America/Lima")
            fecha_actual = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            
            datos_actualizacion = {
                **nuevos_valores,
                "fertilidad": int(fert_pred),
                "cultivo": cultivo_pred,
                "fecha": fecha_actual
            }
            
            # Actualizar registro en Supabase
            actualizar_registro(id_sel, datos_actualizacion)
            st.success("✅ Registro actualizado correctamente.")
            st.rerun()

# Eliminación
with st.expander("🗑️ Eliminar registro"):
    if st.button("❌ Confirmar eliminación"):
        eliminar_registro(id_sel)
        st.rerun()







