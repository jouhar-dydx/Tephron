# scripts/run_cost_analysis.py

import os
import boto3
import logging
from datetime import datetime
from src.aws.ec2.scanner import EC2Scanner
from src.aws.ec2.analyzer import EC2Analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("[*] Starting Tephron AI – Cost Analysis Engine")

    session = boto3.Session()
    scanner = EC2Scanner(session.region_name)
    analyzer = EC2Analyzer(session=session)

    # Step 1: Scan all active regions
    from src.aws.ec2.scanner import get_all_regions
    regions = get_all_regions(session)
    logger.info(f"[+] Found {len(regions)} active regions")

    all_instances = []
    for region in regions:
        scanner = EC2Scanner(region)
        instances = scanner.scan_instances()
        analyzed = [analyzer.analyze_instance(inst) for inst in instances]
        all_instances.extend(analyzed)
        logger.info(f"[+] Analyzed {len(instances)} instance(s) in {region}")

    # Step 2: Save structured output
    output_file = f"/app/data/output/cost/cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    from src.core.utils import save_json
    save_json({"instances": all_instances}, output_file)

if __name__ == "__main__":
    main()