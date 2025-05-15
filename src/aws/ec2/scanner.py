# src/aws/ec2/scanner.py

import os
import json
import boto3
import logging
from concurrent.futures import ThreadPoolExecutor
from src.core.utils import save_json
from src.aws.ec2.cost_estimator import EC2CostEstimator

logger = logging.getLogger(__name__)
OUTPUT_DIR = "/app/data/output/ec2/"

class EC2Scanner:
    def __init__(self, region: str):
        self.region = region
        self.session = boto3.Session(region_name=region)
        self.ec2_client = self.session.client('ec2')
        self.cost_estimator = EC2CostEstimator(self.session)

    def scan_instances(self) -> List[Dict]:
        try:
            response = self.ec2_client.describe_instances()
            instances = []

            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_info = {
                        "InstanceId": instance.get("InstanceId"),
                        "InstanceType": instance.get("InstanceType"),
                        "State": instance.get("State", {}).get("Name"),
                        "LaunchTime": str(instance.get("LaunchTime")),
                        "PublicIpAddress": instance.get("PublicIpAddress"),
                        "Tags": {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])},
                        "Region": self.region
                    }

                    instances.append(instance_info)

            filename = f"{OUTPUT_DIR}instances_{self.region}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            save_json(instances, filename)
            logger.info(f"[+] Scanned {len(instances)} EC2 instances in {self.region}")
            return instances
        except Exception as e:
            logger.error(f"[!] Failed to scan instances in {self.region}: {e}")
            return []

    def run_parallel_scan(self, max_workers: int = 10) -> List[Dict]:
        from src.aws.ec2.scanner import get_all_regions
        regions = get_all_regions(self.session)
        logger.info(f"[+] Found active regions: {regions}")

        all_instances = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.scan_instances, region) for region in regions]
            for future in futures:
                all_instances.extend(future.result())

        logger.info(f"[+] Enriching {len(all_instances)} instances with cost data")
        cost_enriched = self.cost_estimator.estimate_and_enhance_instances(all_instances)

        return cost_enriched