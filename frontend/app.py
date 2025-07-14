import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from backend.loaders import load_all_models
from backend.apis import get_weather, get_elevation
from backend.predictors import predecir
from backend.utils import cultivos as cultivo_dict
from backend.database import guardar


def main():
    try:
        st.set_page_config(page_title="Predicción de Fertilidad y Cultivo", layout="centered")
        st.title("🌱 Predicción de Fertilidad del Suelo y Cultivo Recomendado")

        API_KEY = st.secrets["api"]["openweather_key"]

        if "historial" not in st.session_state:
            st.session_state["historial"] = []

        modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders = load_all_models()
        cultivo_dict = {i: clase for i, clase in enumerate(encoders['cultivo'].classes_)}

        st.header("📍 Ubicación")
        col1, col2 = st.columns(2)
        lat = col1.number_input("Latitud", format="%.6f")
        lon = col2.number_input("Longitud", format="%.6f")

        if st.button("🌤 Obtener datos climáticos"):
            clima = get_weather(lat, lon, API_KEY)
            altitud = get_elevation(lat, lon)
            if clima["humedad"] is not None:
                st.session_state.update({
                    "humedad": clima["humedad"],
                    "temperatura": clima["temperatura"],
                    "ubicacion": clima["ubicacion"],
                    "altitud": altitud,
                    "lat": lat,
                    "lon": lon
                })
                st.success(f"✅ Datos obtenidos para {clima['ubicacion']}")
            else:
                st.warning("No se pudieron obtener datos. Verifique la conexión o API Key.")

        st.header("🌾 Datos del suelo")
        tipo_suelo_opciones = list(encoders["tipo_suelo"].classes_)
        tipo_suelo_texto = st.selectbox("Tipo de suelo", tipo_suelo_opciones)
        tipo_suelo = encoders["tipo_suelo"].transform([tipo_suelo_texto])[0]

        pH = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1)
        materia_organica = st.number_input("Materia orgánica (%)", min_value=0.0, step=0.1)
        conductividad = st.number_input("Conductividad", min_value=0.0, step=0.01)
        nitrogeno = st.number_input("Nitrógeno (mg/kg)", min_value=0.0, step=0.1)
        fosforo = st.number_input("Fósforo (mg/kg)", min_value=0.0, step=0.1)
        potasio = st.number_input("Potasio (mg/kg)", min_value=0.0, step=0.1)
        densidad = st.number_input("Densidad (g/cm³)", min_value=0.0, step=0.01)

        st.header("🌤 Datos ambientales")
        humedad = st.number_input("Humedad (%)", min_value=0.0, max_value=100.0, step=0.1, value=float(st.session_state.get("humedad", 0.0)))
        temperatura = st.number_input("Temperatura (°C)", value=float(st.session_state.get("temperatura", 0.0)))

        condiciones_opciones = list(encoders["condiciones_clima"].classes_)
        condiciones_clima_texto = st.selectbox("Condiciones del clima", condiciones_opciones, index=condiciones_opciones.index(st.session_state.get("condiciones_clima_texto", condiciones_opciones[0])))
        condiciones_clima = encoders["condiciones_clima"].transform([condiciones_clima_texto])[0]

        altitud = st.number_input("Altitud (m)", value=float(st.session_state.get("altitud", 0.0)))
        mes = st.selectbox("Mes de siembra", list(range(1, 13)))
        evapotranspiracion = st.number_input("Evapotranspiración (mm/día)", min_value=0.0, step=0.1)

        if st.button("📊 Predecir"):
            input_data = pd.DataFrame([{
                "tipo_suelo": tipo_suelo,
                "pH": pH,
                "materia_organica": materia_organica,
                "conductividad": conductividad,
                "nitrogeno": nitrogeno,
                "fosforo": fosforo,
                "potasio": potasio,
                "humedad": humedad,
                "densidad": densidad,
                "altitud": altitud,
                "temperatura": temperatura,
                "condiciones_clima": condiciones_clima,
                "mes": mes,
                "evapotranspiracion": evapotranspiracion
            }])

            st.write("tipo_suelo (input):", tipo_suelo)
            st.write("Encoder tipo_suelo classes_:", encoders['tipo_suelo'].classes_)
            st.write("condiciones_clima (input):", condiciones_clima)
            st.write("Encoder condiciones_clima classes_:", encoders['condiciones_clima'].classes_)

            for col in encoders:
                if col != 'cultivo' and col in input_data.columns:
                    if input_data[col].dtype == object:
                        input_data[col] = encoders[col].transform(input_data[col])

            fert_pred, cult_pred_idx = predecir(input_data, modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders)
            estado_fertilidad = "FÉRTIL ✅" if fert_pred == 1 else "INFÉRTIL ❌"
            cultivo_predicho = cultivo_dict.get(cult_pred_idx, "Desconocido")

            st.markdown("---")
            st.subheader("🔎 Resultado")
            st.info(f"🧪 Fertilidad estimada: **{estado_fertilidad}**")
            if cultivo_predicho:
                st.success(f"🌾 Cultivo recomendado: **{cultivo_predicho}**")
            else:
                st.warning("⚠️ No se recomienda sembrar. Mejore las condiciones del suelo.")

            registro = {
                "tipo_suelo": tipo_suelo,
                "pH": round(pH, 2),
                "materia_organica": round(materia_organica, 2),
                "conductividad": round(conductividad, 2),
                "nitrogeno": round(nitrogeno, 2),
                "fosforo": round(fosforo, 2),
                "potasio": round(potasio, 2),
                "humedad": round(humedad, 2),
                "densidad": round(densidad, 2),
                "altitud": round(altitud, 2),
                "temperatura": round(temperatura, 2),
                "condiciones_clima": condiciones_clima,
                "mes": mes,
                "evapotranspiracion": round(evapotranspiracion, 2),
                "fertilidad": int(fert_pred),
                "cultivo": cultivo_predicho,
                "lugar": st.session_state.get("ubicacion", None),
                "latitud": st.session_state.get("lat", None),
                "longitud": st.session_state.get("lon", None)
            }

            guardar(registro)

    except Exception as e:
        st.error(f"❌ Error en la app: {e}")

if __name__ == "__main__":
    main()


