import random
import json
import time
import math
import sys
import os
import shutil

from .constraints import apply_constraints
from .naming import derive_tags, derive_config_name
from .writer import write_session
from schemas.session_schema import SessionConfig
from .unreal_client import UnrealClient
from orchestrator.config import host, port, WEATHER_MANAGER_PATH, CAPTURE_MANAGER_PATH, SCREENSHOTS_DIR, DRONE_PATHS
from .sampler import sampler, random_drone_color
from .annotation import generate_labels

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../configs/orchestrator.json")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../output")
TEST_MODE  = "--test" in sys.argv
START_SEED = int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 0
TEST_SESSION_PATH = os.path.join(os.path.dirname(__file__), "../../configs/test_session.json")

for split in ("train", "val"):
    os.makedirs(os.path.join(OUTPUT_DIR, "images", split), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "labels", split), exist_ok=True)

client = UnrealClient(host, port, WEATHER_MANAGER_PATH, CAPTURE_MANAGER_PATH, DRONE_PATHS)

with open(CONFIG_PATH) as f:
    orch_config = json.load(f)

dist = orch_config["drone_count_distribution"]
cam_cfg = orch_config["camera"]
sv_cfg = orch_config["spawn_volume"]

manifest = []

if TEST_MODE:
    with open(TEST_SESSION_PATH) as f:
        test_cfg = json.load(f)
    sessions = [test_cfg["seed"]]
else:
    total = int(orch_config["session_count"] * orch_config["overage_factor"])
    sessions = range(START_SEED, total)

total_sessions = len(sessions)
run_start = time.time()

for session_idx, i in enumerate(sessions):
    if TEST_MODE:
        environment_samples = test_cfg["environment"]
        environment_samples["ground_material_variant"] = test_cfg.get("ground_material_variant", 0)
        drone_count = test_cfg["drone_count"]
        cam_pitch_override = test_cfg.get("cam_pitch")
        cam_yaw_override   = test_cfg.get("cam_yaw")


    else:
        environment_samples = apply_constraints(sampler(CONFIG_PATH, i))
        drone_count = random.choices([0, 1, 2, 3, 4], weights=[dist["0"], dist["1"], dist["2"], dist["3"], dist["4"]], k=1)[0]

    tags = derive_tags(environment_samples, drone_count)
    config_name = derive_config_name(environment_samples, i, drone_count)

    cam_rng = random.Random(i)
    cam_roll = 0.0

    sv        = test_cfg["spawn_volume"] if TEST_MODE else sv_cfg
    margin    = sv.get("frame_margin", 0.8)
    depth_min = sv["depth_min"]
    depth_max = sv["depth_max"]
    alt_min   = sv["altitude_min"]

    MAX_RETRIES = 10
    cam_x = cam_y = cam_z = cam_pitch = cam_yaw = 0.0
    drone_positions = []

    for attempt in range(MAX_RETRIES):
        # 1. Sample a position on the terrain surface
        cam_x = cam_rng.uniform(-cam_cfg["zone_half_extent"], cam_cfg["zone_half_extent"])
        cam_y = cam_rng.uniform(-cam_cfg["zone_half_extent"], cam_cfg["zone_half_extent"])
        cam_z = client.get_ground_height(cam_x, cam_y) + cam_rng.uniform(cam_cfg["zone_height_min"], cam_cfg["zone_height_max"])

        # 2. Sample a random orientation
        pitch_min = -30.0 if drone_count == 0 else -80.0
        yaw_r   = math.radians(cam_rng.uniform(0.0, 360.0))
        pitch_r = math.radians(cam_rng.uniform(pitch_min, 80.0))
        cam_yaw   = math.degrees(yaw_r)
        cam_pitch = math.degrees(pitch_r)

        if TEST_MODE and cam_pitch_override is not None:
            cam_pitch = cam_pitch_override
            cam_yaw   = cam_yaw_override
            pitch_r   = math.radians(cam_pitch)
            yaw_r     = math.radians(cam_yaw)

        # 3. Compute camera basis vectors
        fwd = ( math.cos(pitch_r)*math.cos(yaw_r),
                math.cos(pitch_r)*math.sin(yaw_r),
                math.sin(pitch_r) )
        rgt = ( -math.sin(yaw_r),
                 math.cos(yaw_r),
                 0.0 )
        up  = ( -math.sin(pitch_r)*math.cos(yaw_r),
                -math.sin(pitch_r)*math.sin(yaw_r),
                 math.cos(pitch_r) )

        # 4. Frustum-sample drone positions — reject orientation if any drone is underground
        drone_positions = []
        underground = False
        for _ in range(drone_count):
            u     = cam_rng.uniform(-margin, margin)
            v     = cam_rng.uniform(-margin, margin)
            depth = cam_rng.uniform(depth_min, depth_max)
            drone_x = cam_x + fwd[0]*depth + rgt[0]*u*depth + up[0]*v*depth*(9/16)
            drone_y = cam_y + fwd[1]*depth + rgt[1]*u*depth + up[1]*v*depth*(9/16)
            drone_z = cam_z + fwd[2]*depth + up[2]*v*depth*(9/16)
            drone_terrain_z = client.get_ground_height(drone_x, drone_y)
            if drone_z < drone_terrain_z + alt_min:
                underground = True
                break
            drone_positions.append((drone_x, drone_y, drone_z))

        if underground:
            continue

        if drone_count == 0:
            break

        # 5. Place in scene and validate line of sight
        client.set_camera_transform([cam_x, cam_y, cam_z], [cam_pitch, cam_yaw, cam_roll])
        client.set_drone_transform(drone_positions)

        if all(client.check_line_of_sight(p) for p in drone_positions):
            break

        if attempt == MAX_RETRIES - 1:
            print(f"[WARN] session {i}: no valid pose after {MAX_RETRIES} attempts")
            
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
            "position": [cam_x, cam_y, cam_z],
            "rotation": [cam_pitch, cam_yaw, cam_roll],
            "zone_half_extent": cam_cfg["zone_half_extent"],
            "zone_height_min": cam_cfg["zone_height_min"],
            "zone_height_max": cam_cfg["zone_height_max"],
            "fov": cam_cfg["fov"],
        },

        "subjects": [
            {
                "class_label": "drone",
                "count": drone_count,
                "placement": "random",
                "spawn_volume": {
                    "depth_min": depth_min,
                    "depth_max": depth_max,
                    "altitude_min": alt_min,
                    "frame_margin": margin
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
            "base_dir": OUTPUT_DIR,
            "save_depth": True,
            "save_stencil_mask": False
        }
    }

    session = SessionConfig(**session_dict)

    client.apply_schema(session)
    client.set_drone_transform(drone_positions)
    for idx in range(len(drone_positions)):
        client.set_drone_colors(idx, random_drone_color(cam_rng), random_drone_color(cam_rng))

    has_precipitation = environment_samples.get("rain_intensity", 0) > 0 or environment_samples.get("snow_intensity", 0) > 0
    time.sleep(3.0 if has_precipitation else 0.5)

    client.capture_RGB(config_name)

    split = "val" if i % 5 == 0 else "train"

    labels = generate_labels(drone_positions, (cam_x, cam_y, cam_z), fwd, rgt, up)

    with open(os.path.join(OUTPUT_DIR, "labels", split, config_name + ".txt"), "w") as f:
        f.write("\n".join(labels))

    src = os.path.join(SCREENSHOTS_DIR, config_name + ".png")
    dst = os.path.join(OUTPUT_DIR, "images", split, config_name + ".png")
    if os.path.exists(src):
        shutil.copy2(src, dst)

    done = session_idx + 1
    elapsed = time.time() - run_start
    rate = elapsed / done
    eta_s = int((total_sessions - done) * rate)
    print(f"[{done+START_SEED}/{total_sessions+START_SEED}] {config_name} | "
          f"elapsed {int(elapsed//60)}m{int(elapsed%60):02d}s | "
          f"ETA {eta_s//3600}h{(eta_s%3600)//60:02d}m{eta_s%60:02d}s")

    output_path = write_session(session_dict, OUTPUT_DIR, config_name)

    with open(os.path.join(OUTPUT_DIR, "data.yaml"), "w") as f:
        f.write("path: .\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("nc: 1\n")
        f.write("names: ['drone']\n")

    manifest.append(
        {
            "config_name": config_name,
            "tags": tags,
            "path": str(output_path)
        }
    )

with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=4, sort_keys=True, ensure_ascii=False)