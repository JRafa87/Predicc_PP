import joblib

def load_all_models():
    modelo_fert = joblib.load("models/modelo_fertilidad.pkl")
    modelo_cult = joblib.load("models/modelo_cultivo.pkl")
    scaler_fert = joblib.load("models/scaler_fertilidad.pkl")
    scaler_cult = joblib.load("models/scaler_cultivo.pkl")
    encoders = joblib.load("models/label_encoders.pkl")
    return modelo_fert, modelo_cult, scaler_fert, scaler_cult, encoders
