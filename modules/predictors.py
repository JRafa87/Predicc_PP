import pandas as pd

def predecir(df_input, modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders):
    import streamlit as st

    # Codificar variables categóricas excepto 'cultivo'
    for col in encoders:
        if col != "cultivo" and col in df_input.columns:
            if df_input[col].dtype == object:
                try:
                    df_input[col] = encoders[col].transform(df_input[col])
                except Exception as err:
                    st.error(f"Error codificando '{col}': {err}")
                    st.stop()


    # Fertilidad
    vars_fert = ['pH', 'materia_organica', 'conductividad', 'nitrogeno', 
                 'fosforo', 'potasio', 'densidad', 'tipo_suelo']
    X_fert = scaler_fert.transform(df_input[vars_fert])
    pred_fert = modelo_fert.predict(X_fert)[0]

    # Cultivo solo si fértil
    if pred_fert == 1:
        vars_cult = ['mes', 'altitud', 'temperatura', 'condiciones_clima', 'tipo_suelo', 
                     'pH', 'humedad', 'evapotranspiracion']
        X_cult = scaler_cult.transform(df_input[vars_cult])
        pred_cult_code = modelo_cult.predict(X_cult)[0]
        pred_cult = encoders['cultivo'].inverse_transform([pred_cult_code])[0]
    else:
        pred_cult = None

    return pred_fert, pred_cult
