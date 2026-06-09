def derive_tags(environment_samples, subject_count):

    tag_list = []

    if environment_samples["time_of_day"] > 8.0 and environment_samples["time_of_day"] < 18.0:
        tag_list.append("daytime")
    elif environment_samples["time_of_day"] > 18.0 and environment_samples["time_of_day"] < 20.0:
        tag_list.append("dusk")
    elif environment_samples["time_of_day"] > 6.0 and environment_samples["time_of_day"] < 8.0:
        tag_list.append("dawn")
    else:
        tag_list.append("night")
    
    if environment_samples["cloud_coverage"] < 0.3 and environment_samples["rain_intensity"] == 0.0 and environment_samples["snow_intensity"] == 0.0:
        tag_list.append("clear")
    
    if environment_samples["cloud_coverage"] >= 0.3:
        tag_list.append("overcast")

    if environment_samples["rain_intensity"] > 0.0 and environment_samples["rain_intensity"] <= 0.5:  
        tag_list.append("light_rain")
    
    if environment_samples["rain_intensity"] > 0.5:  
        tag_list.append("heavy_rain")
    
    if environment_samples["snow_intensity"] > 0.0:  
        tag_list.append("snow")

    if environment_samples["fog_density"] > 0.3:
        tag_list.append("fog")

    if subject_count == 0:
        tag_list.append("empty")
    elif subject_count == 1:  
        tag_list.append("single")
    elif subject_count > 1:  
        tag_list.append("multi")

    return tag_list

def derive_config_name(environment_samples, seed):

    config = derive_tags(environment_samples, 0)

    time_tag = next((t for t in config if t in {"daytime", "dusk", "dawn", "night"}), "unknown")
    weather_tag = next((t for t in config if t in {"clear", "overcast", "light_rain", "heavy_rain", "snow"}), "unknown")
    
    return f"{time_tag}_{weather_tag}_s{seed}"
    