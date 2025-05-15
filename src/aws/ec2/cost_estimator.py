# src/aws/ec2/cost_estimator.py

"""
cost_estimator.py

Enterprise-grade cost estimation engine for EC2 instances.
Uses AWS Pricing API to fetch accurate hourly rates and determines if underutilized based on metrics.

Key Features:
- Dynamic region + instance-type pricing lookup
- Handles missing regions or unknown types gracefully
- Supports tagging, environment classification (prod/dev/test)
- Stores structured results for ingestion into DB
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import boto3
import logging
import decimal
from decimal import Decimal
from src.core.logger import setup_logger
from src.aws.cloudwatch.metrics_collector import CloudWatchMetrics
from src.core.utils import save_json

logger = logging.getLogger(__name__)
OUTPUT_DIR = "/app/data/output/ec2/"

# Set high precision for cost calculations
decimal.getcontext().prec = 10

def generate_timestamp():
    return datetime.utcnow().isoformat()

class EC2CostEstimator:
    def __init__(self, session: boto3.Session):
        self.session = session
        self.pricing_client = session.client('pricing', region_name='us-east-1')  # Global endpoint
        self.costexplorer_client = session.client('ce', region_name='us-east-1')
        self.ec2_client = session.client('ec2', region_name=session.region_name)

    def _get_on_demand_hourly_rate(self, instance_type: str, region: str) -> Decimal:
        """Fetches on-demand hourly rate from AWS Pricing API"""
        try:
            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
                ],
                MaxResults=1
            )

            if response['PriceList']:
                price_data = json.loads(response['PriceList'][0])
                hourly_cost = Decimal(price_data['terms']['OnDemand'].popitem()[1]['priceDimensions'].popitem()[1]['pricePerUnit']['USD'])
                logger.info(f"[+] Fetched on-demand rate for {instance_type} in {region}: ${hourly_cost}/hr")
                return hourly_cost
            else:
                logger.warning(f"[!] No pricing data found for {instance_type}")
                return Decimal(0)
        except Exception as e:
            logger.error(f"[!] Error fetching pricing for {instance_type}: {e}")
            return Decimal(0)

    def _get_spot_hourly_rate(self, instance_type: str, region: str) -> Decimal:
        """Fetches current spot price from CloudWatch"""
        try:
            ec2_regional = self.session.client('ec2', region_name=region)
            response = ec2_regional.describe_spot_price_history(
                InstanceTypes=[instance_type],
                ProductDescriptions=["Linux/UNIX"],
                MaxResults=1
            )
            if response['SpotPriceHistory']:
                logger.info(f"[+] Fetched spot rate for {instance_type} in {region}: ${response['SpotPriceHistory'][0]['SpotPrice']}/hr")
                return Decimal(response['SpotPriceHistory'][0]['SpotPrice'])
            else:
                return Decimal(0)
        except Exception as e:
            logger.warning(f"[!] Spot pricing not available for {instance_type} in {region}: {e}")
            return Decimal(0)

    def estimate_monthly_cost_from_metrics(self, instance_id: str, avg_cpu: float, hourly_rate: Decimal) -> Decimal:
        """
        Estimate monthly cost using average CPU utilization and known hourly rate.
        Assumes ~730 hours/month for simplification.
        """
        try:
            # Heuristic: If CPU < 10%, suggest downsizing
            if avg_cpu < 10:
                logger.warning(f"[!] Low CPU Utilization: {avg_cpu}% for {instance_id}")
                return hourly_rate * Decimal(730) * Decimal(0.5)  # Assume 50% usage
            else:
                return hourly_rate * Decimal(730)
        except Exception as e:
            logger.error(f"[!] Error calculating cost for {instance_id}: {e}")
            return Decimal(0)

    def estimate_and_enhance_instances(self, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main method to enrich scanned EC2 instances with cost data
        """
        result = []
        cw_clients = {}

        for inst in instances:
            try:
                region = inst["Region"]
                instance_type = inst["InstanceType"]
                instance_id = inst["InstanceId"]

                # Get CloudWatch client per region
                if region not in cw_clients:
                    cw_clients[region] = CloudWatchMetrics(self.session, region)

                # Get CPU utilization from CloudWatch
                cloudwatch_agent = cw_clients[region]
                cpu_utilization = cloudwatch_agent.get_cpu_utilization(instance_id) or 0

                # Try spot first, then fall back to on-demand
                hourly_rate = self._get_spot_hourly_rate(instance_type, region)
                if hourly_rate == 0:
                    hourly_rate = self._get_on_demand_hourly_rate(instance_type, region)

                # Estimate monthly bill
                monthly_forecast = self.estimate_monthly_cost_from_metrics(instance_id, cpu_utilization, hourly_rate)

                # Enrich instance dict with cost data
                inst["HourlyRate"] = str(hourly_rate)
                inst["MonthlyCostEstimate"] = str(monthly_forecast)
                inst["Underutilized"] = bool(cpu_utilization < 10 and hourly_rate > Decimal("0.01"))
                inst["CPUUtilization"] = round(cpu_utilization, 2)
                inst["CostImpactRank"] = "high" if monthly_forecast > Decimal("50") else "medium" if monthly_forecast > Decimal("10") else "low"

                result.append(inst)

            except Exception as e:
                logger.error(f"[!] Failed to enrich instance {inst.get('InstanceId', 'unknown')}: {e}")

        return result

    def get_current_month_cost_explorer_report(self) -> Dict[str, Decimal]:
        """
        Uses AWS Cost Explorer API to get real billing data
        """
        try:
            response = self.costexplorer_client.get_cost_and_usage(
                TimePeriod={
                    'Start': datetime.utcnow().replace(day=1).strftime('%Y-%m-%d'),
                    'End': datetime.utcnow().strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}]
            )

            costs_by_instance_type = {}
            for group in response.get("ResultsByTime", [{}])[0].get("Groups", []):
                instance_type = group.get("Keys", ["unknown-instance"])[0]
                cost = Decimal(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0"))
                costs_by_instance_type[instance_type] = cost

            logger.info("[+] Got month-to-date cost report via Cost Explorer API")
            return costs_by_instance_type
        except Exception as e:
            logger.error(f"[!] Failed to fetch cost explorer data: {e}")
            return {}

    def flag_expensive_underutilized_instances(self, instances: List[Dict]) -> List[Dict]:
        """
        Returns list of instances that:
        - Are costing more than $10/month
        - Have less than 10% CPU utilization
        """
        enriched_instances = self.estimate_and_enhance_instances(instances)
        flagged = [
            inst for inst in enriched_instances
            if inst.get("Underutilized") and inst.get("MonthlyCostEstimate") > Decimal("10")
        ]
        logger.info(f"[+] Flagged {len(flagged)} expensive underutilized instances")
        return flagged