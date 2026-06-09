import json
from pathlib import Path

def write_session(session_dict, output_dir, config_name):
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)

    output_path = p / f"{config_name}.json"

    with open(output_path, "w", encoding="utf-8") as f:
            json.dump(session_dict, f, indent=4, sort_keys=True, ensure_ascii=False)
        
    return output_path

