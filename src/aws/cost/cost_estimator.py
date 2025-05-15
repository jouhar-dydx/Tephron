# src/aws/cost/cost_estimator.py

import boto3
import logging
from datetime import datetime, timedelta
from dateutil.tz import tzutc

logger = logging.getLogger(__name__)

class CostExplorerEstimator:
    def __init__(self, session, region="us-east-1"):
        self.session = session
        self.region = region
        self.client = session.client('ce', region_name="us-east-1")  # CE is global

    def get_daily_cost_per_instance(self, days=7):
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d'),
                    'End': datetime.utcnow().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}]
            )

            costs = {}
            for result_by_time in response['ResultsByTime']:
                for group in result_by_time['Groups']:
                    key = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    costs[key] = costs.get(key, 0) + amount

            logger.info("[+] Successfully fetched cost data from Cost Explorer")
            return costs
        except Exception as e:
            logger.error(f"[!] Failed to fetch cost data: {e}")
            return {}

    def estimate_monthly_cost(self, daily_costs):
        """Convert daily average to monthly forecast"""
        monthly_costs = {}
        for instance_type, cost in daily_costs.items():
            monthly_costs[instance_type] = round(cost * 30, 2)
        return monthly_costs