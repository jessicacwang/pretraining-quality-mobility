import json
from typing import Dict


def load_config(config_path: str) -> Dict:
    with open(config_path, "r") as cf:
        return json.load(cf)
