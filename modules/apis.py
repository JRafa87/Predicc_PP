import requests

# Recibe el encoder desde fuera para mapear correctamente
def get_weather(lat, lon, api_key, encoder_clima=None):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        data = requests.get(url, params=params).json()

        condicion_clima_raw = data["weather"][0]["main"]  # Ej. 'Clear', 'Rain', etc.

        if encoder_clima:
            try:
                # Transforma el texto de OpenWeatherMap usando el encoder original
                condicion_clima = encoder_clima.transform([condicion_clima_raw])[0]
            except:
                condicion_clima = encoder_clima.transform(["Clouds"])[0]  # Valor por defecto: 'nublado'
        else:
            condicion_clima = 2  # por defecto si no se pasa encoder

        return {
            "humedad": data["main"]["humidity"],
            "temperatura": data["main"]["temp"],
            "condiciones_clima": condicion_clima,
            "ubicacion": data.get("name", "")
        }

    except Exception:
        return {
            "humedad": None,
            "temperatura": None,
            "condiciones_clima": 2,
            "ubicacion": ""
        }


def get_elevation(lat, lon):
    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url)
        return float(response.json()['results'][0]['elevation'])
    except:
        return None

