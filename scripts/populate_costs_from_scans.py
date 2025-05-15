# scripts/populate_costs_from_scans.py

import logging
import os
from src.core.db_handler import PostgresHandler
from src.aws.ec2.scanner import EC2Scanner
from src.aws.ec2.cost_estimator import EC2CostEstimator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("[*] Starting cost population service")
    session = boto3.Session()
    scanner = EC2Scanner(session.region_name)
    instances = scanner.scan_instances()

    if not instances:
        logger.info("[+] No instances found during scan")
        return

    cost_estimator = EC2CostEstimator(session)
    enriched_instances = cost_estimator.estimate_and_enhance_instances(instances)

    db_handler = PostgresHandler()
    db_handler.create_tables()

    for inst in enriched_instances:
        db_handler.save_instance_cost_data(inst)

    logger.info(f"[+] Stored cost data for {len(enriched_instances)} instances")

if __name__ == "__main__":
    main()