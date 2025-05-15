# src/aws/ec2/analyzer.py

from src.aws.cloudwatch.metrics_collector import CloudWatchMetrics
from src.core.logger import logger
from decimal import Decimal

class EC2Analyzer:
    def __init__(self, session=None):
        self.session = session or boto3.Session()

    def analyze_instance(self, instance_data: dict) -> dict:
        """Add metrics to instance data using CloudWatch"""
        instance_id = instance_data.get("InstanceId")
        region = instance_data.get("Region", "us-east-1")

        cw = CloudWatchMetrics(self.session, region)

        cpu_utilization = cw.get_cpu_utilization(instance_id)
        network = cw.get_network_io(instance_id)

        network_in = network.get("network_in_bytes", 0.0)
        network_out = network.get("network_out_bytes", 0.0)

        analyzed = {
            **instance_data,
            "CPUUtilization": cpu_utilization,
            "NetworkIn": network_in,
            "NetworkOut": network_out,
            "Underutilized": cpu_utilization < 10 and network_in < 100000
        }

        logger.info(f"[+] Analyzed {instance_id} | CPU: {cpu_utilization:.2f}% | Monthly: ${analyzed.get('MonthlyCostEstimate', 0):.2f}")
        return analyzed