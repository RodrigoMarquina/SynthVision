def apply_constraints(environment_samples):
    if environment_samples["snow_intensity"] > 0.0 and environment_samples["rain_intensity"] > 0.0:
        environment_samples["rain_intensity"] = 0.0
    precipitation = max(environment_samples["rain_intensity"], environment_samples["snow_intensity"])
    if precipitation > 0:
        environment_samples["cloud_coverage"] = max(environment_samples["cloud_coverage"], 0.3 + precipitation * 0.5)
    return environment_samples
