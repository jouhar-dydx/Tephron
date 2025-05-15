# src/aws/ec2/cost_estimator.py

import os
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from src.core.logger import logger
from src.aws.cloudwatch.metrics_collector import CloudWatchMetrics

class EC2CostEstimator:
    def __init__(self, session=None):
        self.session = session or boto3.Session()
        self.pricing_client = self.session.client('pricing', region_name='us-east-1')
        self.cache_file = "/app/data/cache/ec2_pricing_cache.json"
        self.instance_cost_cache = self._load_cache()
        self.cloudwatch = CloudWatchMetrics(session=self.session)

    def _load_cache(self) -> dict:
        """Load cached pricing data to avoid repeated API calls"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"[!] Failed to load pricing cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save current pricing cache to disk"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.instance_cost_cache, f, indent=4)
            logger.info("[+] Saved pricing cache")
        except Exception as e:
            logger.error(f"[!] Failed to save pricing cache: {e}")

    def _get_hourly_rate_from_api(self, instance_type: str, region: str) -> Decimal:
        """Get real-time hourly rate from AWS Pricing API"""
        try:
            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "shared"},
                    {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "No"}
                ],
                MaxResults=1
            )

            if not response["PriceList"]:
                logger.warning(f"[!] No pricing found for {instance_type}")
                return Decimal("0.0")

            product = json.loads(response["PriceList"][0])
            terms = product.get("terms", {}).get("OnDemand", {})
            price_per_unit = list(terms.values())[0]["priceDimensions"].values().__next__()["pricePerUnit"]

            hourly_rate = Decimal(price_per_unit.get("USD", "0.0"))
            cache_key = f"{region}:{instance_type}"
            self.instance_cost_cache[cache_key] = float(hourly_rate)
            self._save_cache()
            return hourly_rate.quantize(Decimal("0.0000"))

        except Exception as e:
            logger.error(f"[!] Error fetching price for {instance_type}: {e}")
            return Decimal("0.0")

    def _get_hourly_rate(self, instance_data: Dict[str, Any]) -> Decimal:
        """Get accurate hourly rate using AWS Pricing API"""
        instance_type = instance_data.get("InstanceType")
        region = instance_data.get("Region", "us-east-1")
        cache_key = f"{region}:{instance_type}"

        if cache_key in self.instance_cost_cache:
            return Decimal(self.instance_cost_cache[cache_key])

        return self._get_hourly_rate_from_api(instance_type, region)

    def get_instance_cost(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate monthly cost based on usage pattern.
        
        Updates instance_data with:
        - HourlyRate
        - DailyCostEstimate
        - WeeklyCostEstimate
        - MonthlyCostEstimate
        - UptimeHours
        - Underutilized flag
        """
        instance_id = instance_data.get("InstanceId")
        instance_type = instance_data.get("InstanceType")
        region = instance_data.get("Region", "us-east-1")

        # Get hourly rate
        hourly_rate = self._get_hourly_rate(instance_data)

        # Ensure numeric comparison
        cpu_utilization = instance_data.get("CPUUtilization", 0)
        network_in = instance_data.get("NetworkIn", 0)
        network_out = instance_data.get("NetworkOut", 0)

        if isinstance(cpu_utilization, str):
            try:
                cpu_utilization = float(cpu_utilization)
            except ValueError:
                cpu_utilization = 0.0

        daily_cost = hourly_rate * 24
        weekly_cost = daily_cost * 7
        monthly_cost = daily_cost * 30

        underutilized = cpu_utilization < 10 and hourly_rate > Decimal("0.02")

        result = {
            "HourlyRate": float(hourly_rate),
            "DailyCostEstimate": float(daily_cost),
            "WeeklyCostEstimate": float(weekly_cost),
            "MonthlyCostEstimate": float(monthly_cost),
            "Underutilized": underutilized,
            "timestamp": generate_timestamp(),
            "instance_id": instance_id,
            "region": region,
            "network_in_bytes_sec": network_in,
            "network_out_bytes_sec": network_out
        }

        logger.info(f"[+] Analyzed {instance_id} | CPU: {cpu_utilization:.2f}% | Monthly: ${monthly_cost:.2f}")
        return {**instance_data, **result}