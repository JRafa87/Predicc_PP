import requests

def get_elevation(lat, lon):
    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url)
        return float(response.json()['results'][0]['elevation'])
    except:
        return None


def get_weather(lat, lon, api_key):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        data = requests.get(url, params=params).json()

        # mapear condiciones del clima directamente aquí
        condiciones_clima_texto = data["weather"][0]["main"]
        condiciones_clima = mapear_clima(condiciones_clima_texto)

        return {
            "humedad": data["main"]["humidity"],
            "temperatura": data["main"]["temp"],
            "condiciones_clima": condiciones_clima,
            "ubicacion": data.get("name", "")
        }
    except:
        return {"humedad": None, "temperatura": None, "condiciones_clima": 2, "ubicacion": ""}
