# src/core/utils.py

import os
import json
from datetime import datetime

def generate_timestamp():
    return datetime.utcnow().isoformat()

def save_json(data, filename):
    full_data = {
        "timestamp": generate_timestamp(),
        "data": data
    }
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, 'w') as f:
            json.dump(full_data, f, indent=4, default=str)
        logger.info(f"[+] Saved JSON output to {filename}")
    except Exception as e:
        logger.error(f"[!] Failed to save JSON output: {e}")
        raise