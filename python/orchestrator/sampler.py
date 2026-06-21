import random
import json
import colorsys

def sampler(orchestrator_path, seed):
    random.seed(seed)

    with open(orchestrator_path) as f: #"configs/orchestrator.json"
        config = json.load(f)

    ranges = config["sampling_ranges"]

    environment_samples = {
        "time_of_day": random.uniform(ranges["time_of_day_min"], ranges["time_of_day_max"]),
        "cloud_coverage": random.uniform(ranges["cloud_coverage_min"], ranges["cloud_coverage_max"]),
        "fog_density": random.uniform(ranges["fog_density_min"], ranges["fog_density_max"]),
        "rain_intensity": random.uniform(ranges["rain_intensity_min"], ranges["rain_intensity_max"]) if random.random() < ranges["rain_probability"] else 0.0,
        "snow_intensity": random.uniform(ranges["snow_intensity_min"], ranges["snow_intensity_max"]) if random.random() < ranges["snow_probability"] else 0.0,
        "wind_intensity": random.uniform(ranges["wind_intensity_min"], ranges["wind_intensity_max"]),
        "ground_material_variant": random.randint(ranges["ground_material_variant_min"], ranges["ground_material_variant_max"]),
    }

    return environment_samples

def random_drone_color(rng):
    h = rng.uniform(0.0, 1.0)
    s = rng.uniform(0.0, 0.55)
    v = rng.uniform(0.05, 0.9)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (round(r, 4), round(g, 4), round(b, 4))