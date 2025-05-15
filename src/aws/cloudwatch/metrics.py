# src/aws/cloudwatch/metrics_collector.py

import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CloudWatchMetrics:
    def __init__(self, session: boto3.Session, region: str):
        self.session = session
        self.region = region
        self.client = self.session.client('cloudwatch', region_name=region)

    def _get_metric_statistics(self, namespace: str, dimensions: List[Dict[str, str]], metric_name: str) -> Optional[float]:
        try:
            response = self.client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=datetime.utcnow() - timedelta(days=7),
                EndTime=datetime.utcnow(),
                Period=604800,  # Weekly average
                Statistics=['Average']
            )
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'], reverse=True)
            return datapoints[0]['Average'] if datapoints else None
        except Exception as e:
            logger.error(f"[!] Failed to fetch {metric_name} metric in {self.region}: {e}")
            return None

    def get_cpu_utilization(self, instance_id: str) -> Optional[float]:
        dimensions = [{'Name': 'InstanceId', 'Value': instance_id}]
        return self._get_metric_statistics("AWS/EC2", dimensions, "CPUUtilization")

    def get_network_in(self, instance_id: str) -> Optional[float]:
        dimensions = [{'Name': 'InstanceId', 'Value': instance_id}]
        return self._get_metric_statistics("AWS/EC2", dimensions, "NetworkIn")

    def get_network_out(self, instance_id: str) -> Optional[float]:
        dimensions = [{'Name': 'InstanceId', 'Value': instance_id}]
        return self._get_metric_statistics("AWS/EC2", dimensions, "NetworkOut")