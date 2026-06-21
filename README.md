# SynthVision

A synthetic data generation pipeline for drone detection, built in Unreal Engine 5. Automatically generates annotated training datasets from procedurally varied simulation environments and trains a YOLOv8 object detector end-to-end.

**Author:** Rodrigo Marquina  
**Built:** June 2026

---

## Overview

SynthVision replaces manual image collection and hand-labeling with a fully automated pipeline. A Python orchestrator drives Unreal Engine 5 via the Remote Control API, varying environment conditions across 1800 seeded sessions, capturing RGB renders, computing bounding box annotations from 3D projection math, and exporting a YOLO-format dataset ready for training.

The same seed always produces the same scene — every dataset is fully reproducible.

---

## Pipeline

```
orchestrator.json (config)
        │
        ▼
Python Orchestrator  ←  generates 1800 seeded sessions
        │                samples camera pose, drone positions (frustum-based)
        │                validates line-of-sight per drone
        ▼
Unreal Engine 5      ←  Remote Control API (port 30010)
        │                BP_WeatherManager: time of day, fog, rain, snow, wind
        │                BP_CaptureManager: camera transform, drone colors, RGB capture
        │                BP_Drone: color-randomized per session
        ▼
Annotation Engine    ←  pure Python 3D→2D projection (no stencil needed)
        │                YOLO bbox from frustum math + depth
        │                filters occluded / sub-pixel drones
        ▼
output/
  images/train/  (~1440 PNGs, 1920×1080)
  images/val/    (~360 PNGs)
  labels/train/  (YOLO .txt per image)
  labels/val/
  data.yaml
        │
        ▼
YOLOv8s Training     ←  Google Colab T4 GPU
        │                pretrained COCO weights, fine-tuned on synthetic data
        ▼
best.pt              ←  drone detector, mAP50 ~0.40 on synthetic val set
```

---

## Environment

- **Landscape:** 4km × 4km terrain generated from a Houdini heightmap (4033×4033, 16-bit PNG)
- **Vegetation:** PCG-placed trees across the terrain
- **Landscape material:** distance-based texture tiling via Material Parameter Collection — updates per capture so Scene Capture Component uses the correct camera position, not the editor viewport
- **Weather:** `BP_WeatherManager` controls time of day (Sky Atmosphere + directional light), volumetric clouds, exponential height fog, Niagara rain, Niagara snow (mutually exclusive with rain), wind
- **Drone:** custom-modeled quadcopter with two independently randomized color parameters (`MI_Plastic_Body → ColorTint`, `MI_Plastic_Detail → ColorTint`) set per-drone per session via Blueprint

---

## Domain Randomization

Each session samples independently:

| Parameter | Range |
|---|---|
| Time of day | 7:30 — 18:30 |
| Cloud coverage | 0 — 1 |
| Fog density | 0 — 1 |
| Rain intensity | 0 — 1 (25% probability) |
| Snow intensity | 0 — 1 (15% probability, exclusive with rain) |
| Wind intensity | 0 — 1 |
| Ground material variant | 0 — 5 |
| Camera height | 1.5 — 25m above terrain |
| Camera position | 1500m × 1500m zone |
| Camera pitch/yaw | random orientation |
| Drone count | 0–4 (weighted: 23% / 40% / 25% / 10% / 2%) |
| Drone colors | HSV-sampled, low saturation (gray/neutral tones) |

---

## Placement Algorithm

For each session, the orchestrator runs a retry loop (max 10 attempts):

1. Sample camera XY position and height above terrain (`GetGroundHeight` line trace)
2. Sample random pitch and yaw
3. Compute camera basis vectors (fwd, rgt, up) from pitch/yaw
4. For each drone: sample normalized screen coords (u, v) within frame margin and a random depth
5. Back-project to world space using the frustum
6. Reject if drone is underground (below terrain + min altitude)
7. Line trace (Visibility channel) from camera to each drone — reject if occluded
8. Accept if all drones pass LOS check

This guarantees every annotated drone is visible from the camera with no terrain or tree occlusion.

---

## Annotation

Bounding boxes are computed analytically from 3D positions — no stencil or depth pass required:

```python
# Project drone world position into camera space
depth  = dot(v, fwd)           # forward distance
r      = dot(v, rgt)           # right offset
u      = dot(v, up)            # up offset

# Normalize by FOV (90° → tan(45°) = 1.0)
norm_x = r / (depth * 1.0)
norm_y = u / (depth * 1.0)

# YOLO format (cx, cy, w, h) normalized to image size
cx = (norm_x + 1) / 2
cy = (1 - norm_y) / 2
w  = (drone_size_m / depth) * (IMG_W / 2) / IMG_W
h  = (drone_size_m / depth) * (IMG_W / 2) / IMG_H
```

Drones below the minimum pixel area threshold (36px²) are filtered out.

---

## Training

- **Model:** YOLOv8s (pretrained on COCO, fine-tuned on SynthVision data)
- **Images:** 1800 sessions → 1441 train / 360 val (80/20 split by seed)
- **Resolution:** 1280px
- **Epochs:** 100 (model still improving at epoch 100 — continued training recommended)
- **Best mAP50:** ~0.40 on synthetic validation set
- **Hardware:** Google Colab T4 GPU, ~3 hours per 100 epochs

---

## Project Structure

```
SynthVision/
├── python/
│   ├── orchestrator/
│   │   ├── __main__.py       # main loop, session sampling, annotation, export
│   │   ├── annotation.py     # 3D→2D projection, YOLO bbox generation
│   │   ├── unreal_client.py  # Remote Control API HTTP client
│   │   ├── sampler.py        # parameter sampling, color randomization
│   │   ├── naming.py         # config name and tag derivation
│   │   ├── constraints.py    # rain/snow mutual exclusion, parameter clamping
│   │   ├── writer.py         # session JSON writer
│   │   └── config.py         # UE5 actor paths, host/port, directories
│   └── schemas/
│       └── session_schema.py # Pydantic schema for session validation
├── configs/
│   ├── orchestrator.json     # main pipeline config
│   └── test_session.json     # single-session debug config
├── output/
│   ├── images/train/
│   ├── images/val/
│   ├── labels/train/
│   ├── labels/val/
│   └── data.yaml
└── SynthVision/              # Unreal Engine 5 project
    └── Content/
        └── Blueprints/
            ├── BP_WeatherManager.uasset
            ├── BP_CaptureManager.uasset
            └── BP_Drone.uasset
```

---

## Running the Pipeline

**Requirements:** Unreal Engine 5 open with the SynthVision project, Remote Control API plugin enabled (port 30010), Python 3.10+, `pip install requests pydantic`

```bash
# Full run (1800 sessions)
cd python
python -m orchestrator

# Resume from a specific seed after interruption
python -m orchestrator --start 450

# Single test session
python -m orchestrator --test
```

**Training on Google Colab:**

```python
!pip install ultralytics
from google.colab import drive
drive.mount('/content/drive')

!yolo detect train \
  model="yolov8s.pt" \
  data="/content/drive/MyDrive/SynthVision/output/data.yaml" \
  epochs=100 \
  imgsz=1280 \
  batch=8 \
  cache=True \
  project="/content/drive/MyDrive/SynthVision/runs"
```

**Inference:**

```python
from ultralytics import YOLO
model = YOLO("runs/train-2/weights/best.pt")
results = model("image.jpg", conf=0.25)
results[0].show()
```

---

## Key Design Decisions

**Remote Control API over C++:** The UE5 HTTP API on port 30010 lets the Python orchestrator drive the entire scene without a custom plugin. Blueprint functions are exposed as REST endpoints and called from Python with `requests`.

**Frustum-based placement:** Drones are sampled in normalized screen space (u, v) at a given depth, then back-projected to world space. This guarantees drones are always within the camera frustum on the first sample — no rejection sampling on world positions.

**3D projection annotation:** Computing bounding boxes analytically from drone world positions is faster, simpler, and more accurate than stencil-based pixel counting for non-occluded objects. The LOS check ensures the analytical bbox matches what's visible.

**MPC for landscape tiling:** `CameraPositionWS` does not update in Scene Capture Components — it uses the editor viewport camera. A Material Parameter Collection updated on every `SetCameraTransform` call passes the correct camera position to the landscape shader.

---

## Limitations and Future Work

- Single drone model — adding multiple drone types would improve generalization
- Synthetic-to-real gap — the model detects drones in synthetic renders but does not generalize to real photographs without fine-tuning on real images
- Urban environment only — expanding to additional biomes (forest, coastal, desert) would improve domain coverage
- Annotation bbox uses a fixed drone size (0.7m) rather than per-instance mesh bounds
