# src/core/db_handler.py

import os
import logging
import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, Any, List, Optional, Union, Tuple, TypeVar

logger = logging.getLogger(__name__)

class PostgresHandler:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "tephron-db"),
            database=os.getenv("DB_NAME", "tephron"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
        self.cur = self.conn.cursor()
        logger.info("[+] Connected to PostgreSQL")

    def create_tables(self):
        """Create required tables if they don't exist"""
        try:
            ec2_table_sql = """
                CREATE TABLE IF NOT EXISTS ec2_instances (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP,
                    instance_id TEXT,
                    region TEXT,
                    instance_type TEXT,
                    state TEXT,
                    cpu_utilization REAL,
                    network_in REAL,
                    network_out REAL,
                    hourly_rate NUMERIC(10, 5),
                    monthly_forecast NUMERIC(10, 2),
                    underutilized BOOLEAN,
                    tags JSONB
                );
            """

            self.cur.execute(ec2_table_sql)
            self.conn.commit()
            logger.info("[+] Verified/created ec2_instances table")
        except Exception as e:
            logger.error(f"[!] Failed to initialize DB schema: {e}")
            self.conn.rollback()

    def save_ec2_instance(self, instance_data: Dict[str, Any]):
        """Insert EC2 instance data into PostgreSQL"""
        insert_sql = """
            INSERT INTO ec2_instances (
                timestamp, instance_id, region, instance_type, state,
                cpu_utilization, network_in, network_out,
                hourly_rate, monthly_forecast, underutilized, tags
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        try:
            values = (
                instance_data.get("timestamp"),
                instance_data.get("InstanceId"),
                instance_data.get("Region"),
                instance_data.get("InstanceType"),
                instance_data.get("State"),
                instance_data.get("CPUUtilization"),
                instance_data.get("NetworkIn"),
                instance_data.get("NetworkOut"),
                instance_data.get("HourlyRate"),
                instance_data.get("MonthlyCostEstimate"),
                instance_data.get("Underutilized"),
                json.dumps(instance_data.get("Tags", {}))
            )

            self.cur.execute(insert_sql, values)
            self.conn.commit()
        except Exception as e:
            logger.error(f"[!] DB Insert failed: {e}")
            self.conn.rollback()