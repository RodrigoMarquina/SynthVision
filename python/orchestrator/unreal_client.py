import requests
from schemas.session_schema import SessionConfig
from orchestrator.config import host, port, WEATHER_MANAGER_PATH

class UnrealClient:
    def __init__(self, host, port, actor_path):
        self.URL = f"http://{host}:{port}/remote/object/call"
        self.path = actor_path
        self.session = requests.Session()

    def _call(self, function_name, parameters):
        body = {
            "objectPath": self.path,
            "functionName": function_name,
            "parameters": parameters
        }
        self.session.put(self.URL, json = body)

    def set_time_of_day(self, value: float):
        d = {"NewTime": value}
        self._call("SetTimeOfDay", d)
        
    def set_fog_density(self, value: float):
        d = {"NewFog": value}
        self._call("SetFogDensity", d)

    def set_rain_intensity(self, value: float):
        d = {"NewRainIntensity": value}
        self._call("SetRainIntensity", d)
    
    def set_snow_intensity(self, value: float):
        d = {"NewSnowIntensity": value}
        self._call("SetSnowIntensity", d)
    
    def set_wind_strength(self, value: float):
        d = {"NewWindStrength": value}
        self._call("SetWindStrength", d)

    def apply_schema(self, schema: SessionConfig):
        self.set_time_of_day(schema.environment.time_of_day)
        self.set_fog_density(schema.environment.fog_density)
        self.set_rain_intensity(schema.environment.rain_intensity)
        self.set_snow_intensity(schema.environment.snow_intensity)
        self.set_wind_strength(schema.environment.wind_intensity)
