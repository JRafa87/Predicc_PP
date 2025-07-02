import streamlit as st
import pandas as pd
from modules.loaders import load_all_models
from modules.apis import get_weather, get_elevation
from modules.predictors import predecir

st.set_page_config(page_title="Predicción de Fertilidad y Cultivo", layout="centered")
st.title("🌱 Predicción de Fertilidad del Suelo y Cultivo Recomendado")

# API Key de OpenWeatherMap
API_KEY = "f75c529787e26621bbd744dd67c056b0"

# Inicializar historial en sesión
if "historial" not in st.session_state:
    st.session_state["historial"] = []

# Cargar modelos y encoders
modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders = load_all_models()

# Sección ubicación
st.header("📍 Ubicación")
col1, col2 = st.columns(2)
lat = col1.number_input("Latitud", format="%.6f")
lon = col2.number_input("Longitud", format="%.6f")

if st.button("🌤 Obtener datos climáticos"):
    clima = get_weather(lat, lon, API_KEY)
    altitud = get_elevation(lat, lon)
    if clima["humedad"] is not None:
        st.session_state["humedad"] = clima["humedad"]
        st.session_state["temperatura"] = clima["temperatura"]
        st.session_state["condiciones_clima"] = clima["condiciones_clima"]
        st.session_state["ubicacion"] = clima["ubicacion"]
        st.session_state["altitud"] = altitud
        st.success(f"✅ Datos obtenidos para {clima['ubicacion']}")
    else:
        st.warning("No se pudieron obtener datos. Verifique la conexión o API Key.")

# Entrada de datos del suelo
st.header("🌾 Datos del suelo")

tipo_suelo = st.selectbox("Tipo de suelo", ["0", "1", "2", "3"])
pH = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1)
materia_organica = st.number_input("Materia orgánica (%)", min_value=0.0, step=0.1)
conductividad = st.number_input("Conductividad", min_value=0.0, step=0.01)
nitrogeno = st.number_input("Nitrógeno (mg/kg)", min_value=0.0, step=0.1)
fosforo = st.number_input("Fósforo (mg/kg)", min_value=0.0, step=0.1)
potasio = st.number_input("Potasio (mg/kg)", min_value=0.0, step=0.1)
densidad = st.number_input("Densidad (g/cm³)", min_value=0.0, step=0.01)

# Datos ambientales
st.header("🌤 Datos ambientales")
humedad = st.number_input("Humedad (%)", min_value=0.0, max_value=100.0, step=0.1, value=st.session_state.get("humedad", 0.0))
temperatura = st.number_input("Temperatura (°C)", value=st.session_state.get("temperatura", 0.0))
condiciones_clima = st.selectbox("Condiciones del clima", ["Clear", "Clouds", "Rain", "Drizzle", "Thunderstorm", "Snow", "Mist"])
altitud = st.number_input("Altitud (m)", value=st.session_state.get("altitud", 0.0))
mes = st.selectbox("Mes de siembra", list(range(1, 13)))
evapotranspiracion = st.number_input("Evapotranspiración (mm/día)", min_value=0.0, step=0.1)
tipo_riego = st.selectbox("Tipo de riego", ["0", "1", "2"])

# Botón de predicción
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
        "evapotranspiracion": evapotranspiracion,
        "tipo_riego": tipo_riego
    }])

    fert_pred, cult_pred = predecir(input_data, modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders)
    estado_fertilidad = "FÉRTIL ✅" if fert_pred == 1 else "INFÉRTIL ❌"

    st.markdown("---")
    st.subheader("🔎 Resultado")
    st.info(f"🧪 Fertilidad estimada: **{estado_fertilidad}**")
    if cult_pred:
        st.success(f"🌾 Cultivo recomendado: **{cult_pred}**")
    else:
        st.warning("⚠️ No se recomienda sembrar. Mejore las condiciones del suelo.")

    # Guardar en historial
    st.session_state.historial.append({
        "Ubicación": st.session_state.get("ubicacion", "Manual"),
        "Fertilidad": "FÉRTIL" if fert_pred == 1 else "INFÉRTIL",
        "Cultivo": cult_pred if cult_pred else "No recomendado",
        "Mes": mes,
        "Temperatura": temperatura,
        "Humedad": humedad,
        "Altitud": altitud
    })

# Mostrar historial
if st.session_state.historial:
    st.markdown("---")
    st.subheader("📋 Historial de predicciones")
    
    df_historial = pd.DataFrame(st.session_state.historial)
    st.dataframe(df_historial)

    # Descargar como CSV
    csv = df_historial.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar historial en CSV",
        data=csv,
        file_name="historial_predicciones.csv",
        mime="text/csv"
    )

# ✅ Cierre del script
if __name__ == "__main__":
    main()
