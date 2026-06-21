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

    def get_ground_height(self, x_m: float, y_m: float) -> float:
        body = {
            "objectPath": self.capture_path,
            "functionName": "GetGroundHeight",
            "parameters": {"X": x_m * 100, "Y": y_m * 100}
        }
        r = self.session.put(self.URL, json=body)
        return r.json().get("GroundZ", 0.0)

    def check_line_of_sight(self, position_m: tuple) -> bool:
        body = {
            "objectPath": self.capture_path,
            "functionName": "CheckLineOfSight",
            "parameters": {
                "DroneLocation": {
                    "X": position_m[0] * 100,
                    "Y": position_m[1] * 100,
                    "Z": position_m[2] * 100
                }
            }
        }
        r = self.session.put(self.URL, json=body)
        return r.json().get("bVisible", False)

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

    def set_drone_colors(self, actor_index: int, color_body: tuple, color_detail: tuple):
        self._call("SetDroneColors", {
            "ActorIndex": actor_index,
            "BodyColor": {"R": color_body[0], "G": color_body[1], "B": color_body[2], "A": 1.0},
            "DetailColor": {"R": color_detail[0], "G": color_detail[1], "B": color_detail[2], "A": 1.0}
        }, self.capture_path)
        
    def apply_schema(self, schema: SessionConfig):
        self.set_camera_transform(schema.camera.position, schema.camera.rotation)
        self.set_time_of_day(schema.environment.time_of_day)
        self.set_cloud_coverage(schema.environment.cloud_coverage)
        self.set_fog_density(schema.environment.fog_density)
        self.set_rain_intensity(schema.environment.rain_intensity)
        self.set_snow_intensity(schema.environment.snow_intensity)
        self.set_wind_strength(schema.environment.wind_intensity)



