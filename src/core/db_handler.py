# src/core/db_handler.py

import os
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch

logger = logging.getLogger(__name__)

class PostgresHandler:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "tephron"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            host=os.getenv("DB_HOST", "db")
        )
        self.cur = self.conn.cursor()
        logger.info("[+] Connected to PostgreSQL")

    def create_tables(self):
        cost_table_sql = """
            CREATE TABLE IF NOT EXISTS ec2_instances (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                instance_id TEXT,
                region TEXT,
                instance_type TEXT,
                state TEXT,
                hourly_rate NUMERIC(10, 5),
                monthly_cost NUMERIC(10, 2),
                underutilized BOOLEAN,
                cpu_utilization REAL,
                network_in REAL,
                network_out REAL,
                tags JSONB
            );
        """
        summary_view_sql = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS ec2_utilization_summary AS
            SELECT 
                instance_id,
                AVG(cpu_utilization) AS avg_cpu,
                MAX(monthly_cost) AS monthly_forecast,
                MAX(underutilized) AS underutilized
            FROM ec2_instances
            GROUP BY instance_id, region
            WITH DATA;
        """
        feedback_table_sql = """
            CREATE TABLE IF NOT EXISTS user_feedback (
                id SERIAL PRIMARY KEY,
                instance_id TEXT,
                action TEXT,
                reason TEXT,
                timestamp TIMESTAMP
            );
        """

        try:
            self.cur.execute(cost_table_sql)
            self.cur.execute(summary_view_sql)
            self.cur.execute(feedback_table_sql)
            self.conn.commit()
            logger.info("[+] Verified/created all cost tables/views")
        except Exception as e:
            logger.error(f"[!] Failed to initialize cost schema: {e}")
            self.conn.rollback()

    def save_instance_cost_data(self, instance_data: Dict[str, Any]):
        try:
            insert_sql = """
                INSERT INTO ec2_instances (
                    timestamp, instance_id, region, instance_type, state,
                    hourly_rate, monthly_cost, underutilized,
                    cpu_utilization, network_in, network_out, tags
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            values = (
                instance_data.get("timestamp"),
                instance_data.get("InstanceId"),
                instance_data.get("Region"),
                instance_data.get("InstanceType"),
                instance_data.get("State"),
                Decimal(instance_data.get("HourlyRate", "0")),
                Decimal(instance_data.get("MonthlyCostEstimate", "0")),
                instance_data.get("Underutilized", False),
                instance_data.get("CPUUtilization", 0),
                instance_data.get("NetworkIn", 0),
                instance_data.get("NetworkOut", 0),
                json.dumps(instance_data.get("Tags", {}))
            )
            self.cur.execute(insert_sql, values)
            self.conn.commit()
        except Exception as e:
            logger.error(f"[!] Failed to store cost data: {e}")
            self.conn.rollback()