# src/aws/cloudwatch/metrics_collector.py

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union, Tuple, TypeVar
from src.core.logger import logger

class CloudWatchMetrics:
    def __init__(self, session=None, region="us-east-1"):
        self.session = session or boto3.Session()
        self.region = region
        try:
            self.cloudwatch = self.session.client("cloudwatch", region_name=region)
        except Exception as e:
            logger.error(f"[!] Failed to initialize CloudWatch client in {region}: {e}")
            self.cloudwatch = None

    def _fetch_metric(self, instance_id: str, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Fetch latest value for a CloudWatch metric"""
        if not self.cloudwatch:
            logger.warning("[!] CloudWatch client not initialized")
            return {"value": Decimal(0), "unit": "N/A"}

        try:
            logger.debug(f"[+] Fetching {metric_name} for {instance_id} in {self.region}")
            stats = self.cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName=metric_name,
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=datetime.utcnow() - timedelta(days=days),
                EndTime=datetime.utcnow(),
                Period=604800,  # Weekly average
                Statistics=["Average"]
            )
            datapoints = sorted(stats.get("Datapoints", []), key=lambda x: x["Timestamp"])
            latest_value = datapoints[-1]["Average"] if datapoints else None

            return {
                "value": Decimal(latest_value).quantize(Decimal("0.00")) if latest_value else Decimal(0),
                "unit": "percent" if "CPU" in metric_name else "bytes/sec"
            }

        except Exception as e:
            logger.warning(f"[!] Error fetching {metric_name} for {instance_id}: {e}")
            return {"value": Decimal(0), "unit": "N/A"}

    def get_cpu_utilization(self, instance_id: str) -> float:
        """Get latest CPU utilization (weekly average)"""
        metric = self._fetch_metric(instance_id, "CPUUtilization")
        return round(float(metric["value"]), 2)

    def get_network_io(self, instance_id: str) -> Dict[str, float]:
        """Get network traffic metrics"""
        in_metric = self._fetch_metric(instance_id, "NetworkIn")
        out_metric = self._fetch_metric(instance_id, "NetworkOut")

        return {
            "network_in_bytes": float(in_metric["value"]),
            "network_out_bytes": float(out_metric["value"])
        }