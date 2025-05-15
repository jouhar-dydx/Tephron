# src/aws/cost/pricing.py

import boto3
import logging
from decimal import Decimal
from typing import Optional
from typing import Dict, Any, List, Optional, Union, Tuple, TypeVar

logger = logging.getLogger(__name__)

class InstancePricing:
    def __init__(self, session=None):
        self.session = session or boto3.Session()
        self.pricing_client = self.session.client('pricing', region_name='us-east-1')  # Global endpoint

    def _parse_price(self, price_string: str) -> Decimal:
        """Convert AWS price string to numeric value"""
        try:
            return Decimal(price_string)
        except Exception as e:
            logger.warning(f"[!] Failed to parse price: {e}")
            return Decimal(0)

    def get_on_demand_hourly_rate(self, instance_type: str, region: str = "us-east-1") -> Decimal:
        """
        Get hourly on-demand rate for EC2 instance
        
        Args:
        - instance_type: e.g., 't3.micro'
        - region: AWS region name
        
        Returns:
        - Hourly rate in USD (Decimal)
        """
        try:
            logger.info(f"[+] Fetching pricing for {instance_type} in {region}")

            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'No'}
                ],
                MaxResults=1
            )

            if not response["PriceList"]:
                logger.warning(f"[!] No pricing found for {instance_type}")
                return Decimal(0)

            product = json.loads(response["PriceList"][0])
            terms = product.get("terms", {}).get("OnDemand", {})
            price_per_unit = list(terms.values())[0]["priceDimensions"].values().__next__()["pricePerUnit"]

            hourly_rate = self._parse_price(price_per_unit.get("USD", "0"))
            logger.info(f"[✓] Fetched rate: ${hourly_rate}/hr for {instance_type}")
            return hourly_rate

        except Exception as e:
            logger.error(f"[!] Pricing fetch failed: {e}")
            return Decimal(0)