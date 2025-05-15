# src/aws/ec2/scanner.py

import boto3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union, Tuple, TypeVar

logger = logging.getLogger(__name__)

def get_all_regions(session=None):
    """Get list of active AWS regions using Boto3"""
    session = session or boto3.Session()
    ec2 = session.client("ec2", region_name="us-east-1")
    try:
        response = ec2.describe_regions()
        return [r["RegionName"] for r in response["Regions"]]
    except Exception as e:
        logger.error(f"[!] Failed to fetch region list: {e}")
        return ["us-east-1"]

class EC2Scanner:
    def __init__(self, region="us-east-1"):
        self.region = region
        self.session = boto3.Session()
        self.ec2_client = self.session.client("ec2", region_name=region)

    def scan_instances(self) -> List[Dict[str, Any]]:
        """Scan all running EC2 instances in current region"""
        try:
            logger.info(f"[+] Scanning EC2 instances in {self.region}")
            response = self.ec2_client.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
            reservations = response.get("Reservations", [])
            instances = []

            for reservation in reservations:
                for instance in reservation["Instances"]:
                    inst_data = {
                        "InstanceId": instance["InstanceId"],
                        "InstanceType": instance["InstanceType"],
                        "State": instance["State"]["Name"],
                        "LaunchTime": str(instance["LaunchTime"]),
                        "Region": self.region,
                        "Tags": {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                    }
                    instances.append(inst_data)

            logger.info(f"[+] Found {len(instances)} instance(s) in {self.region}")

            # Save raw scan data
            filename = f"/app/data/output/ec2/instances_{self.region}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            from src.core.utils import save_json
            save_json(instances, filename)

            return instances
        except Exception as e:
            logger.error(f"[!] Scan failed in {self.region}: {e}")
            return []
        
__all__ = ['EC2Scanner', 'get_all_regions']