import requests
from schemas.session_schema import SessionConfig
from orchestrator.config import host, port, WEATHER_MANAGER_PATH, CAPTURE_MANAGER_PATH, DRONE_PATHS

class UnrealClient:
    def __init__(self, host, port, weather_path, capture_path, drone_paths):
        self.URL = f"http://{host}:{port}/remote/object/call"
        self.weather_path = weather_path
        self.capture_path = capture_path
        self.drone_paths = drone_paths
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

    def set_cloud_coverage(self, value: float):
        self._call("SetCloudCoverage", {"NewCloudCoverage": value}, self.weather_path)

    def capture_RGB(self, filename: str):
        self._call("CaptureRGB", {"FileName": filename + ".png"}, self.capture_path)

    def set_camera_transform(self, location: tuple, rotation: tuple):
        self._call("SetCameraTransform", {
            "NewLocation": {"X": location[0] * 100, "Y": location[1] * 100, "Z": location[2] * 100},
            "NewRotation": {"Pitch": rotation[0], "Yaw": rotation[1], "Roll": rotation[2]}
        }, self.capture_path)

    def set_drone_transform(self, positions: list):
        park = {"X": 0.0, "Y": 0.0, "Z": -500000.0}
        for i, path in enumerate(self.drone_paths):
            if i < len(positions):
                p = positions[i]
                loc = {"X": p[0] * 100, "Y": p[1] * 100, "Z": p[2] * 100}
            else:
                loc = park
            self._call("SetDroneTransform", {"NewLocation": loc}, path)

    def apply_schema(self, schema: SessionConfig):
        self.set_camera_transform(schema.camera.position, schema.camera.rotation)
        self.set_time_of_day(schema.environment.time_of_day)
        self.set_cloud_coverage(schema.environment.cloud_coverage)
        self.set_fog_density(schema.environment.fog_density)
        self.set_rain_intensity(schema.environment.rain_intensity)
        self.set_snow_intensity(schema.environment.snow_intensity)
        self.set_wind_strength(schema.environment.wind_intensity)



