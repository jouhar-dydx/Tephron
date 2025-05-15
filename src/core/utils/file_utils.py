# src/core/utils/file_utils.py

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
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump(full_data, f, indent=4)
        print(f"[+] Saved JSON output to {filename}")
    except Exception as e:
        print(f"[!] Failed to save JSON output: {e}")
        raise

def load_json(filepath):
    """Load a single JSON file"""
    try:
        with open(filepath, "r") as f:
            return json.load(f).get("data", [])
    except Exception as e:
        print(f"[!] Error loading {filepath}: {e}")
        return []

def load_json_files(directory):
    """Load all JSON files from a directory"""
    if not os.path.exists(directory):
        print(f"[!] Directory not found: {directory}")
        return []

    files = [f for f in os.listdir(directory) if f.endswith(".json")]
    all_instances = []
    for filename in files:
        path = os.path.join(directory, filename)
        instances = load_json(path)
        all_instances.extend(instances)
        print(f"[+] Loaded {len(instances)} instance(s) from {filename}")

    return all_instances