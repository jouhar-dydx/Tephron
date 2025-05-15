# src/aws/cost/explorer.py

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union, Tuple, TypeVar
from src.core.logger import setup_logger

logger = setup_logger(__name__)

class CostExplorerAPI:
    def __init__(self, session=None):
        self.session = session or boto3.Session()
        self.ce_client = self.session.client("ce", region_name="us-east-1")

    def get_daily_cost_per_instance(self, instance_ids: List[str], days: int = 7) -> Dict[str, Decimal]:
        """Get daily unblended cost per instance using AWS Cost Explorer"""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = datetime.utcnow().strftime("%Y-%m-%d")

            logger.info(f"[+] Fetching {days}-day cost data via Cost Explorer API")

            response = self.ce_client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "INSTANCE_TYPE"}],
                Filter={
                    "Dimensions": {
                        "Key": "INSTANCE_ID",
                        "Values": instance_ids,
                        "MatchOptions": ["EQUALS"]
                    }
                }
            )

            results_by_time = response.get("ResultsByTime", [])
            cost_data = {}

            for result in results_by_time:
                for group in result.get("Groups", []):
                    instance_type = group["Keys"][0]
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    cost_data[instance_type] = Decimal(amount).quantize(Decimal("0.00"))

            logger.info(f"[+] Retrieved daily cost for {len(cost_data)} instances")
            return cost_data

        except Exception as e:
            logger.error(f"[!] Cost Explorer API error: {e}")
            return {}