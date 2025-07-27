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

st.title("🗃️ Gestión de Registros - Predicciones Fertilidad y Cultivo")

# Mostrar predicción pendiente
if "registro_predicho" in st.session_state:
    st.markdown("### ✅ Última predicción no guardada")
    st.json(st.session_state["registro_predicho"])

    col_guardar, col_descartar = st.columns(2)
    if col_guardar.button("💾 Guardar predicción"):
        guardar(st.session_state["registro_predicho"])
        st.success("📥 Predicción guardada correctamente.")
        del st.session_state["registro_predicho"]
        st.rerun()

    if col_descartar.button("🗑️ Descartar predicción"):
        del st.session_state["registro_predicho"]
        st.info("Predicción descartada.")
        st.rerun()

st.markdown("### 📄 Registros actuales en Supabase")
df = obtener_registros()
df = df.sort_values(by="id", ascending=True).reset_index(drop=True)

if df.empty:
    st.info("No hay registros aún.")
    st.stop()

# Añadir columna visual para mostrar si es editable
df_mostrar = df.copy()
df_mostrar["editable"] = df_mostrar["prediccion"].apply(lambda x: "✅ Sí" if x else "❌ No")

# Mostrar dataframe con filas grises para registros predichos (no manuales)
def colorear_filas(row):
    estilo = [''] * len(row)
    if row["prediccion"]:
        estilo = ['color: gray'] * len(row)
    return estilo

try:
    st.dataframe(
        df_mostrar.drop(columns=["prediccion"]).style.apply(colorear_filas, axis=1),
        use_container_width=True
    )
except Exception:
    st.dataframe(df_mostrar.drop(columns=["prediccion"]), use_container_width=True)

# Construir opciones del selectbox
opciones = (
    df["id"].astype(str)
    + " | "
    + df["lugar"].fillna("Sin lugar")
    + " | "
    + df["cultivo"]
    + " | "
    + df["prediccion"].apply(lambda x: "🧠 Predicción" if x else "✍️ Manual")
)

seleccion = st.selectbox("Selecciona un registro para editar o eliminar", opciones)

if seleccion:
    id_sel = int(seleccion.split(" | ")[0])
    registro_sel = df[df["id"] == id_sel].iloc[0]

    st.markdown(f"**Registro ID {id_sel}** – {'🧠 Predicción automática' if registro_sel['prediccion'] else '✍️ Ingreso manual'}")

    editable = registro_sel["prediccion"]

    # Cargar encoders si es editable (para los campos categóricos)
    if editable:
        _, _, _, _, encoders = load_all_models()

    with st.expander("✏️ Editar registro", expanded=True):

        def input_field(label, key, value, enabled=True):
            if isinstance(value, (int, float)):
                return st.number_input(label, key=key, value=float(value), disabled=not enabled)
            elif isinstance(value, bool):
                return st.checkbox(label, key=key, value=value, disabled=not enabled)
            elif isinstance(value, pd.Timestamp) or "fecha" in label.lower():
                return st.date_input(label, key=key, value=value if value else datetime.date.today(), disabled=not enabled)
            else:
                return st.text_input(label, key=key, value=str(value) if value is not None else "", disabled=not enabled)



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
            "mes": (registro_sel["mes"], "numerico")
        }
     for i, fila in df.iterrows():
        nuevos_valores = {}
        for campo, valor in fila.items():
            editable = campo in campos_editables
            etiqueta = str(campo).replace("_", " ").capitalize()
            nuevos_valores[campo] = input_field(etiqueta, key=f"{campo}_{i}", value=valor, enabled=editable)


        if editable and st.button("🔁 Actualizar registro"):
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

    with st.expander("🗑️ Eliminar registro"):
        if st.button("❌ Confirmar eliminación"):
            eliminar_registro(id_sel)
            st.warning("Registro eliminado.")
            st.rerun()



