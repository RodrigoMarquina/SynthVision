import requests
from schemas.session_schema import SessionConfig
from orchestrator.config import host, port, WEATHER_MANAGER_PATH, CAPTURE_MANAGER_PATH

class UnrealClient:
    def __init__(self, host, port, weather_path, capture_path):
        self.URL = f"http://{host}:{port}/remote/object/call"
        self.weather_path = weather_path
        self.capture_path = capture_path
        self.session = requests.Session()

    def _call(self, function_name, parameters, object_path):
        body = {
            "objectPath": object_path,
            "functionName": function_name,
            "parameters": parameters
        }
        self.session.put(self.URL, json = body)

    def set_time_of_day(self, value: float):
        self._call("SetTimeOfDay",  {"NewTime": value}, self.weather_path)
        
    def set_fog_density(self, value: float):
        self._call("SetFogDensity", {"NewFog": value}, self.weather_path)

    def set_rain_intensity(self, value: float):
        self._call("SetRainIntensity", {"NewRainIntensity": value}, self.weather_path)
    
    def set_snow_intensity(self, value: float):
        self._call("SetSnowIntensity", {"NewSnowIntensity": value}, self.weather_path)
    
    def set_wind_strength(self, value: float):
        self._call("SetWindStrength", {"NewWindStrength": value}, self.weather_path)

    def apply_schema(self, schema: SessionConfig):
        self.set_time_of_day(schema.environment.time_of_day)
        self.set_fog_density(schema.environment.fog_density)
        self.set_rain_intensity(schema.environment.rain_intensity)
        self.set_snow_intensity(schema.environment.snow_intensity)
        self.set_wind_strength(schema.environment.wind_intensity)

    def capture_RGB(self, filename: str):
        self._call("CaptureRGB", {"FileName": filename + ".png"}, self.capture_path)

