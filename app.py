import streamlit as st
import pandas as pd
from modules.loaders import load_all_models
from modules.apis import get_weather, get_elevation
from modules.predictors import predecir

def main():
    try:
        st.set_page_config(page_title="Predicción de Fertilidad y Cultivo", layout="centered")
        st.title("🌱 Predicción de Fertilidad del Suelo y Cultivo Recomendado")

        API_KEY = "f75c529787e26621bbd744dd67c056b0"  # ⬆️ Reemplaza con tu propia API Key de OpenWeatherMap

        if "historial" not in st.session_state:
            st.session_state["historial"] = []

        # Cargar modelos y encoders
        modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders = load_all_models()

        # Diccionario de nombres de cultivos
        cultivo_dict = {i: clase for i, clase in enumerate(encoders['cultivo'].classes_)}

        # Entrada de coordenadas
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
                    "altitud": altitud
                })
                st.success(f"✅ Datos obtenidos para {clima['ubicacion']}")
            else:
                st.warning("No se pudieron obtener datos. Verifique la conexión o API Key.")

        # Datos del suelo
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

        # Datos climáticos
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

            fert_pred, cult_pred_idx = predecir(input_data, modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders)
            estado_fertilidad = "FÉRTIL ✅" if fert_pred == 1 else "INFÉRTIL ❌"
            cultivo_predicho = cultivo_dict.get(cult_pred_idx, "Desconocido") if cult_pred_idx is not None else None

            st.markdown("---")
            st.subheader("🔎 Resultado")
            st.info(f"🧪 Fertilidad estimada: **{estado_fertilidad}**")
            if cultivo_predicho:
                st.success(f"🌾 Cultivo recomendado: **{cultivo_predicho}**")
            else:
                st.warning("⚠️ No se recomienda sembrar. Mejore las condiciones del suelo.")

            st.session_state.historial.append({
                "Ubicación": st.session_state.get("ubicacion", "Manual"),
                "Fertilidad": "FÉRTIL" if fert_pred == 1 else "INFÉRTIL",
                "Cultivo": cultivo_predicho if cultivo_predicho else "No recomendado",
                "Tipo de suelo": tipo_suelo_texto,
                "Mes": mes,
                "Temperatura": temperatura,
                "Humedad": humedad,
                "Altitud": altitud
            })

        if st.session_state.historial:
            st.markdown("---")
            st.subheader("📋 Historial de predicciones")
            df_historial = pd.DataFrame(st.session_state.historial)
            st.dataframe(df_historial)

            csv = df_historial.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📅 Descargar historial en CSV",
                data=csv,
                file_name="historial_predicciones.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error en la app: {e}")

if __name__ == "__main__":
    main()