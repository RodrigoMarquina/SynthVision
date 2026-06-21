from typing import Literal, List, Tuple
from typing_extensions import Self
from pydantic import BaseModel, model_validator

class SpawnVolume(BaseModel):
    depth_min: float
    depth_max: float
    altitude_min: float
    frame_margin: float

class MotionBlur(BaseModel):
    speed_min: float
    speed_max: float
    direction: Literal["random"]

class SubjectConfig(BaseModel):
    class_label: Literal["drone"]
    count: int
    placement: Literal["random", "explicit"]
    spawn_volume: SpawnVolume
    scale_variance: float
    rotation_variance: float
    propeller_speed_variance: float
    motion_blur: MotionBlur

class EnvironmentConfig(BaseModel):
    terrain_preset: Literal["urban"]
    time_of_day: float
    cloud_coverage: float
    fog_density: float
    rain_intensity: float
    snow_intensity: float
    wind_intensity: float
    ground_material_variant: int

    @model_validator(mode="after")
    def check_snow(self) -> Self:
        if self.snow_intensity > 0 and self.rain_intensity > 0:
            raise ValueError("Snow and rain enabled at the same time.")
        return self 
        
class CameraConfig(BaseModel):
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    zone_half_extent: float
    zone_height_min: float
    zone_height_max: float
    fov: Literal[90.0]

class CaptureConfig(BaseModel):
    passes: List[Literal["rgb", "depth", "stencil"]]
    output_resolution: Tuple[int, int]

class AnnotationConfig(BaseModel):
    min_visible_pixel_fraction: float
    min_bbox_area_px: int
    discard_below_threshold: bool

class OutputConfig(BaseModel):
    base_dir: str
    save_depth: bool
    save_stencil_mask: bool

class SessionConfig(BaseModel):
    config_name: str
    seed: int
    tags: List[str]
    environment: EnvironmentConfig
    camera: CameraConfig
    subjects: List[SubjectConfig]
    capture: CaptureConfig
    annotation: AnnotationConfig
    output: OutputConfig