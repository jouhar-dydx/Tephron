# src/main.py

import os
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from src.aws.ec2.scanner import EC2Scanner, get_all_regions
from src.core.db_handler import PostgresHandler
from src.ai.ml.anomaly_detector import InstanceAnomalyDetector
from src.slack.bot import SlackBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_timestamp():
    return datetime.utcnow().isoformat()

def run_scanner():
    logger.info("[*] Starting EC2 scanner")
    regions = get_all_regions()
    logger.info(f"[+] Found {len(regions)} active AWS regions")

    all_instances = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for region in regions:
            scanner = EC2Scanner(region)
            futures.append(executor.submit(scanner.scan_instances))

        for future in futures:
            instances = future.result()
            all_instances.extend(instances)
            logger.info(f"[+] Scanned {len(instances)} instance(s) in region")

    # Save raw scan results
    filename = f"/app/data/output/ec2/ec2_scan_{generate_timestamp().replace(':', '-').split('.')[0]}.json"
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": generate_timestamp(),
                "data": all_instances
            }, f, indent=4)
        logger.info(f"[+] Saved EC2 scan data to {filename}")
    except Exception as e:
        logger.error(f"[!] Failed to save scan data: {e}")

    return all_instances

def run_anomaly_detection(instances):
    detector = InstanceAnomalyDetector()
    anomalies = detector.flag_underutilized_instances(instances)

    if anomalies:
        logger.info(f"[+] Detected {len(anomalies)} underutilized instances")
    else:
        logger.info("[+] No underutilized instances detected")

    return anomalies

def main():
    logger.info("[*] Starting Tephron AI Engine")

    # Step 1: Scan EC2 instances across all regions
    instances = run_scanner()
    if not instances:
        logger.warning("[!] No EC2 instances found during scan")
        return

    # Step 2: Detect underutilized instances
    anomalies = run_anomaly_detection(instances)

    # Step 3: Send alerts via Slack
    if anomalies:
        logger.info("[+] Sending alerts to Slack")
        bot = SlackBot()
        for anomaly in anomalies:
            msg = (
                f"⚠️ Underutilized Instance: `{anomaly['InstanceId']}` in `{anomaly['Region']}`\n"
                f"• CPU Utilization: {anomaly.get('CPUUtilization', 0):.2f}%\n"
                f"• Monthly Forecast: ${anomaly.get('monthly_forecast', 0):.2f}\n"
                f"Type `/tephron confirm {anomaly['InstanceId']}` to validate"
            )
            bot.send_alert(msg)

if __name__ == "__main__":
    main()