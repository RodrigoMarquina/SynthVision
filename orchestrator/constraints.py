def apply_constraints(environment_samples):
    if environment_samples["snow_intensity"] > 0.0 and environment_samples["rain_intensity"] > 0.0:
        environment_samples["rain_intensity"] = 0.0
    return environment_samples
