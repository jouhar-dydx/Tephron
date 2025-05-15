# src/ai/ml/analyzer.py

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
DATA_DIR = "/app/data/output/ec2/"

class InstancePolicyEvaluator:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.policies = {
            "underutilized": {
                "cpu_threshold_percent": 10,
                "min_days_to_flag": 3,
                "ignore_states": ["stopped", "terminated"]
            },
            "spike_detection": {
                "cpu_jump_threshold": 50,
                "lookback_hours": 24
            }
        }

    def load_instance_history(self, instance_id: str) -> List[Dict]:
        """Load historical scan data for one instance"""
        try:
            history = []
            for filename in os.listdir(DATA_DIR):
                if filename.endswith(".json"):
                    with open(os.path.join(DATA_DIR, filename), "r") as f:
                        content = json.load(f)
                        for record in content.get("data", []):
                            if record.get("InstanceId") == instance_id:
                                history.append(record)

            history.sort(key=lambda x: x["timestamp"])
            return history
        except Exception as e:
            logger.error(f"[!] Error loading history for {instance_id}: {e}")
            return []

    def evaluate_underutilization(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate instance based on multi-day utilization"""
        instance_id = instance_data.get("InstanceId")
        region = instance_data.get("Region")
        state = instance_data.get("State", "").lower()

        if state in self.policies["underutilized"]["ignore_states"]:
            return {}

        history = self.load_instance_history(instance_id)
        timestamps = [h["timestamp"] for h in history]
        cpus = [h.get("Metrics", {}).get("CPUUtilization", {}).get("value") for h in history]
        cpus = [c for c in cpus if isinstance(c, (int, float))]

        if len(cpus) < self.policies["underutilized"]["min_days_to_flag"]:
            return {}

        avg_cpu = sum(cpus) / len(cpus)
        underutilized = avg_cpu < self.policies["underutilized"]["cpu_threshold_percent"]

        # Evaluate recent spike
        recent = [c for t, c in zip(timestamps, cpus) if (
            datetime.fromisoformat(t[:26]) > datetime.utcnow() - timedelta(hours=self.policies["spike_detection"]["lookback_hours"])
        ]
        spike_detected = False
        if len(recent) >= 2:
            jump = recent[-1] - recent[0]
            spike_detected = jump > self.policies["spike_detection"]["cpu_jump_threshold"]

        result = {
            "InstanceId": instance_id,
            "Region": region,
            "InstanceType": instance_data.get("InstanceType"),
            "Underutilized": underutilized,
            "SpikeDetected": spike_detected,
            "AvgCPU": round(avg_cpu, 2),
            "RecentCPUSpike": round(jump, 2) if spike_detected else None,
            "EvaluationTimestamp": generate_timestamp(),
            "HistoryCount": len(history)
        }

        return result

    def evaluate_all_instances(self, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate all instances against defined policies"""
        evaluations = []
        for inst in instances:
            evaluation = self.evaluate_underutilization(inst)
            if evaluation:
                evaluations.append(evaluation)
        return evaluations