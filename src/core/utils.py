# src/core/utils.py

import os
import json
from datetime import datetime
from src.core.logger import logger

def generate_timestamp():
    return datetime.utcnow().isoformat()

def save_json(data, filename):
    """Save structured output with timestamp"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump({
                "timestamp": generate_timestamp(),
                "data": data
            }, f, indent=4)
        logger.info(f"[+] Saved JSON output to {filename}")
    except Exception as e:
        logger.error(f"[!] Failed to save JSON output: {e}")
        raise

def load_json_files(directory="/app/data/output/ec2/"):
    """Load all JSON files from given directory"""
    if not os.path.exists(directory):
        logger.warning(f"[!] Directory not found: {directory}")
        return []

    files = [f for f in os.listdir(directory) if f.endswith(".json")]
    logger.info(f"[+] Found {len(files)} JSON files to process")

    all_data = []
    for filename in files:
        path = os.path.join(directory, filename)
        try:
            with open(path, "r") as f:
                content = json.load(f)
                all_data.extend(content.get("data", []))
        except Exception as e:
            logger.error(f"[!] Error loading {path}: {e}")

    logger.info(f"[+] Loaded {len(all_data)} instance records")
    return all_data