import random
import json
import time
from .constraints import apply_constraints
from .naming import derive_tags, derive_config_name
from .sampler import sampler
from .writer import write_session
from schemas.session_schema import SessionConfig
from .unreal_client import UnrealClient
from orchestrator.config import host, port, WEATHER_MANAGER_PATH, CAPTURE_MANAGER_PATH
import os
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../configs/orchestrator.json")

client = UnrealClient(host, port, WEATHER_MANAGER_PATH, CAPTURE_MANAGER_PATH)

with open(CONFIG_PATH) as f:
    orch_config = json.load(f)

dist = orch_config["drone_count_distribution"]

manifest = []

for i in range(int(orch_config["session_count"] * orch_config["overage_factor"])):
    environment_samples = apply_constraints(sampler(CONFIG_PATH, i))

    drone_count = random.choices([0, 1, 2, 3, 4], weights=[dist["0"], dist["1"], dist["2"], dist["3"], dist["4"]], k=1)[0]

    tags = derive_tags(environment_samples, drone_count)

    config_name = derive_config_name(environment_samples, i)

    session_dict = {
        "config_name": config_name,
        "seed": i,
        "tags": tags,
        
        "environment": {
            "terrain_preset": "urban",
            "time_of_day": environment_samples["time_of_day"],
            "cloud_coverage": environment_samples["cloud_coverage"],
            "fog_density": environment_samples["fog_density"],
            "rain_intensity": environment_samples["rain_intensity"],
            "snow_intensity": environment_samples["snow_intensity"],
            "wind_intensity": environment_samples["wind_intensity"],
            "ground_material_variant": environment_samples["ground_material_variant"]
        },

        "camera": {
            "zone_half_extent": 5.0,
            "zone_height": 1.5,
            "fov": 90.0,
            "look_at_jitter_deg": 15.0
        },

        "subjects": [
            {
                "class_label": "drone",
                "count": drone_count,
                "placement": "random",
                "asset_variant": 3,
                "spawn_volume": {
                    "xy_min_offset": 20.0,
                    "xy_max_offset": 80.0,
                    "altitude_min": 10.0,
                    "altitude_max": 120.0
                },
                "scale_variance": 0.15,
                "rotation_variance": 180.0,
                "propeller_speed_variance": 0.3,
                "motion_blur": {
                    "speed_min": 0.0,
                    "speed_max": 25.0,
                    "direction": "random"
                }
            }
        ],

        "capture": {
            "passes": ["rgb", "depth", "stencil"],
            "output_resolution": [1920, 1080]
        },

        "annotation": {
            "min_visible_pixel_fraction": 0.35,
            "min_bbox_area_px": 100,
            "discard_below_threshold": True
        },

        "output": {
            "base_dir": "output/",
            "save_depth": True,
            "save_stencil_mask": False
        }

    }

    session = SessionConfig(**session_dict)

    client.apply_schema(session)

    time.sleep(0.5)

    client.capture_RGB(config_name)

    output_path = write_session(session_dict, "output/", config_name)

    manifest.append(
        {
            "config_name": config_name,
            "tags": tags,
            "path": str(output_path)
        }
    )

with open("output/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=4, sort_keys=True, ensure_ascii=False)