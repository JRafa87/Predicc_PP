import pandas as pd

# modules/predictors.py
def predecir(df_input, modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders):
    import streamlit as st

    # Codificar categóricas (excepto cultivo)
    for col in encoders:
        if col != "cultivo" and col in df_input.columns:
            if df_input[col].dtype == object:
                try:
                    df_input[col] = encoders[col].transform(df_input[col])
                except Exception as err:
                    st.error(f"Error codificando '{col}': {err}")
                    st.stop()

    # ======== Predicción de fertilidad ========
    vars_fert = ['pH', 'materia_organica', 'conductividad', 'nitrogeno',
                 'fosforo', 'potasio', 'densidad', 'tipo_suelo']
    
    X_fert = df_input[vars_fert]
    X_fert_scaled = scaler_fert.transform(X_fert)
    fert_pred = modelo_fert.predict(X_fert_scaled)[0]

    if fert_pred == 0:
        return fert_pred, None  # Si infértil, no predecimos cultivo

    # ======== Predicción de cultivo (si fértil) ========
    vars_cult = ['mes', 'altitud', 'temperatura', 'condiciones_clima',
                 'tipo_suelo', 'pH', 'humedad', 'evapotranspiracion']

    X_cult = df_input[vars_cult]
    X_cult_scaled = scaler_cult.transform(X_cult)
    cult_pred_idx = int(modelo_cult.predict(X_cult_scaled)[0])  # aseguramos int

    return fert_pred, cult_pred_idx

