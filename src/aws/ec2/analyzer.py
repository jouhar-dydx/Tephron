# src/aws/ec2/analyzer.py

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.ai.ml.anomaly_detector import generate_timestamp

logger = logging.getLogger(__name__)
DATA_DIR = "/app/data/output/ec2/"

class EC2InstancePolicyAnalyzer:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.history_days = 7
        self.cpu_threshold_low = 10  # % CPU threshold
        self.cpu_threshold_high = 80
        self.duration_underutilized_days = 3
        self.cost_weight = 0.6  # 60% weight to cost
        self.utilization_weight = 0.4  # 40% weight to CPU usage

    def load_instance_history(self, instance_id: str) -> List[Dict]:
        """Load historical records for a specific instance"""
        try:
            history = []
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.data_dir, filename)
                    with open(filepath, 'r') as f:
                        content = json.load(f)
                        for record in content.get("data", []):
                            if record["InstanceId"] == instance_id:
                                history.append(record)

            # Sort by timestamp
            history.sort(key=lambda x: x.get("timestamp"))
            return history
        except Exception as e:
            logger.error(f"[!] Failed to load instance history for {instance_id}: {e}")
            return []

    def analyze_underutilization(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single instance for underutilization"""
        instance_id = instance_data.get("InstanceId")
        region = instance_data.get("Region")

        if not instance_id or not region:
            logger.warning("[!] Missing InstanceId or Region in input")
            return {}

        history = self.load_instance_history(instance_id)
        if not history:
            logger.info(f"[+] No historical data found for {instance_id}")
            return {}

        cpu_values = [
            entry.get("Metrics", {}).get("CPUUtilization", {}).get("value")
            for entry in history[-self.duration_underutilized_days:]
        ]
        cpu_values = [v for v in cpu_values if isinstance(v, (int, float))]

        if len(cpu_values) < self.duration_underutilized_days:
            logger.warning(f"[!] Not enough history for {instance_id} (<{self.duration_underutilized_days} days)")
            return {}

        avg_cpu = sum(cpu_values) / len(cpu_values)
        underutilized = avg_cpu < self.cpu_threshold_low

        # Check for sudden spike
        current_cpu = cpu_values[-1]
        previous_avg = sum(cpu_values[:-1]) / (len(cpu_values) - 1) if len(cpu_values) > 1 else current_cpu
        spike_detected = (current_cpu > self.cpu_threshold_high and previous_avg < 10)

        # Build structured result
        result = {
            "InstanceId": instance_id,
            "Region": region,
            "InstanceType": instance_data.get("InstanceType"),
            "Underutilized": underutilized,
            "SpikeDetected": spike_detected,
            "AvgCPU": round(avg_cpu, 2),
            "CurrentCPU": round(current_cpu, 2),
            "HistoryDaysUsed": len(cpu_values),
            "Timestamp": generate_timestamp()
        }

        if underutilized:
            result["Recommendation"] = "Downsize to smaller instance or convert to Lambda/Fargate"

        if spike_detected:
            result["AlertLevel"] = "high"
            result["Message"] = f"🚨 CPU Spike Detected: {current_cpu}% from average {previous_avg}%"

        return result

    def analyze_all_instances(self, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply underutilization logic to all instances"""
        results = []
        for inst in instances:
            analysis = self.analyze_underutilization(inst)
            if analysis:
                results.append(analysis)

        return results