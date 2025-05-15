# scripts/ingest_json_to_postgres.py

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, TypeVar
from src.core.db_handler import PostgresHandler
from src.core.utils.file_utils import load_json_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INPUT_DIR = "/app/data/output/ec2/"

def infer_schema(data: List[Dict[str, Any]]) -> Dict[str, str]:
    """Infer schema based on JSON file structure"""
    schema = {}
    for item in data:
        for key, value in item.items():
            if isinstance(value, str):
                schema[key] = "TEXT"
            elif isinstance(value, int):
                schema[key] = "INTEGER"
            elif isinstance(value, float):
                schema[key] = "REAL"
            elif isinstance(value, dict) or isinstance(value, list):
                schema[key] = "JSONB"
            elif value is None:
                schema[key] = "TEXT"
    return schema

def serialize_dict_values(data: List[Dict], columns: List[str]) -> List[tuple]:
    """Prepare data for PostgreSQL insertion"""
    serialized = []
    for item in data:
        row = []
        for col in columns:
            val = item.get(col)
            if isinstance(val, (dict, list)):
                row.append(json.dumps(val))
            else:
                row.append(val)
        serialized.append(tuple(row))
    return serialized

def main():
    pg = PostgresHandler()
    raw_data = load_json_files(INPUT_DIR)

    if not raw_data:
        logger.info("[!] No data found to ingest.")
        return

    schema = infer_schema(raw_data)
    logger.info(f"[+] Creating or migrating table 'ec2_instances' with inferred schema")

    pg.create_table("ec2_instances", schema)

    columns = list(schema.keys())
    formatted_data = serialize_dict_values(raw_data, columns)

    pg.insert_data("ec2_instances", columns, formatted_data)

if __name__ == "__main__":
    main()