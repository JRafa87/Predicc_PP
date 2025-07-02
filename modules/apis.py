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
        return {
            "humedad": data["main"]["humidity"],
            "temperatura": data["main"]["temp"],
            "condiciones_clima": data["weather"][0]["main"],
            "ubicacion": data.get("name", "")
        }
    except:
        return {"humedad": None, "temperatura": None, "condiciones_clima": None, "ubicacion": ""}

# ✅ Agrega esta función al final del archivo
def mapear_clima(descripcion):
    descripcion = descripcion.lower()
    if "drizzle" in descripcion or "llovizna" in descripcion:
        return 0  # llovizna
    elif "rain" in descripcion or "lluvia" in descripcion:
        return 1  # lluvioso
    elif "cloud" in descripcion or "nublado" in descripcion:
        return 2  # nublado
    elif "clear" in descripcion or "soleado" in descripcion:
        return 3  # soleado
    else:
        return 2  # nublado como valor por defecto