# src/aws/cost/estimator.py

import os
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union, Tuple, TypeVar
from src.aws.cost.explorer import CostExplorerAPI
from src.core.db_handler import PostgresHandler

logger = logging.getLogger(__name__)

class CostEstimator:
    def __init__(self, session=None):
        self.session = session or boto3.Session()
        self.cost_explorer = CostExplorerAPI(self.session)
        self.db_handler = PostgresHandler()

    def estimate_instance_cost(self, instance_id: str, region: str = "us-east-1") -> Dict[str, Any]:
        """
        Estimate cost for one EC2 instance:
        - Today's actual cost (via CE API)
        - Weekly projection based on usage pattern
        - Monthly forecast using CPU + network activity
        
        Returns:
        {
            'instance_id': str,
            'region': str,
            'today_cost': float,
            'weekly_forecast': float,
            'monthly_forecast': float,
            'currency': 'USD',
            'timestamp': isoformat,
            'underutilized': bool
        }
        """
        try:
            from src.aws.ec2.scanner import EC2Scanner
            scanner = EC2Scanner(region)
            instance_data = scanner.scan_instances()[0]

            hourly_rate = self._get_hourly_rate(instance_data)
            today_cost = self._get_today_cost(instance_data)

            weekly_forecast = self._forecast_weekly_cost(instance_data, hourly_rate)
            monthly_forecast = self._forecast_monthly_cost(instance_data, hourly_rate)

            result = {
                "instance_id": instance_id,
                "region": region,
                "today_cost": today_cost,
                "weekly_forecast": weekly_forecast,
                "monthly_forecast": monthly_forecast,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat(),
                "underutilized": monthly_forecast > 10 and today_cost < 0.5
            }

            self._store_cost_data(result)
            return result

        except Exception as e:
            logger.error(f"[!] Cost estimation failed: {e}")
            return {}

    def _get_hourly_rate(self, instance_data: Dict[str, Any]) -> Decimal:
        """Get accurate hourly rate using AWS Pricing API"""
        instance_type = instance_data.get("InstanceType")
        region = instance_data.get("Region", "us-east-1")

        from src.aws.cost.pricing import InstancePricing
        ip = InstancePricing(boto3.Session())
        return ip.get_on_demand_hourly_rate(instance_type, region)

    def _get_today_cost(self, instance_data: Dict[str, Any]) -> Decimal:
        """Use Cost Explorer to get today's actual cost"""
        instance_id = instance_data.get("InstanceId")
        return self.cost_explorer.get_daily_cost_per_instance([instance_id]).get(instance_id, Decimal(0))

    def _forecast_weekly_cost(self, instance_data: Dict[str, Any], hourly_rate: Decimal) -> Decimal:
        """Forecast weekly cost based on CPU utilization"""
        avg_cpu = instance_data.get("CPUUtilization", 0)
        utilization_factor = 1.0 if avg_cpu >= 75 else 0.6 if avg_cpu >= 25 else 0.4
        weekly_cost = hourly_rate * 24 * 7 * utilization_factor
        return weekly_cost.quantize(Decimal("0.00"))

    def _forecast_monthly_cost(self, instance_data: Dict[str, Any], hourly_rate: Decimal) -> Decimal:
        """Monthly forecast based on CPU and network activity"""
        avg_cpu = instance_data.get("CPUUtilization", 0)
        network_out = instance_data.get("NetworkOut", 0)

        utilization_factor = 1.0 if avg_cpu >= 75 else 0.6 if avg_cpu >= 25 else 0.4
        network_surcharge = Decimal(0.01) * (network_out / 1000)  # $0.01 per GB over 1TB/month

        base_monthly = hourly_rate * 24 * 30
        final_monthly = base_monthly * utilization_factor + network_surcharge
        return final_monthly.quantize(Decimal("0.00"))

    def _store_cost_data(self, cost_data: Dict[str, Any]):
        """Save cost data into PostgreSQL"""
        insert_sql = """
            INSERT INTO ec2_costs (
                instance_id, region, today_cost, weekly_forecast, monthly_forecast, underutilized
            ) VALUES (%s, %s, %s, %s, %s, %s);
        """
        try:
            values = (
                cost_data["instance_id"],
                cost_data["region"],
                cost_data["today_cost"],
                cost_data["weekly_forecast"],
                cost_data["monthly_forecast"],
                cost_data["underutilized"]
            )
            self.db_handler.cur.execute(insert_sql, values)
            self.db_handler.conn.commit()
            logger.info(f"[+] Stored cost data for {cost_data['instance_id']}")
        except Exception as e:
            logger.error(f"[!] Failed to store cost data: {e}")
            self.db_handler.conn.rollback()