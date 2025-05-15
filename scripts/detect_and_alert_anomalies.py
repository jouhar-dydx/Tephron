# scripts/detect_and_alert_anomalies.py

import os
import logging
from src.aws.ec2.analyzer import EC2InstancePolicyAnalyzer
from src.slack.bot import SlackBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("[*] Starting Tephron AI – Intelligent Anomaly Evaluation")

    # Load latest scanned instances
    from src.aws.ec2.scanner import EC2Scanner, get_all_regions

    regions = get_all_regions()
    logger.info(f"[+] Found {len(regions)} active AWS regions")

    all_instances = []
    for region in regions:
        scanner = EC2Scanner(region)
        instances = scanner.scan_instances()
        all_instances.extend(instances)

    # Analyze using policy engine
    analyzer = EC2InstancePolicyAnalyzer()
    evaluations = analyzer.evaluate_all_instances(all_instances)

    if not evaluations:
        logger.info("[+] No anomalies detected across all instances")
        return

    # Send intelligent alerts via Slack
    bot = SlackBot()
    for eval_result in evaluations:
        instance_id = eval_result.get("InstanceId")
        avg_cpu = eval_result.get("AvgCPU")
        region = eval_result.get("Region")
        cost_estimate = eval_result.get("MonthlyCostEstimate", 0)

        if not instance_id or not region:
            continue

        if eval_result.get("Underutilized", False):
            msg = (
                f"⚠️ Underutilized Instance: `{instance_id}` in `{region}`\n"
                f"• Avg CPU: {avg_cpu:.2f}% over {eval_result['HistoryCount']} days\n"
                f"• Monthly Forecast: ${cost_estimate:.2f}\n"
                f"• Recommendation: Consider downsizing or converting to Lambda\n"
                f"Type `/tephron confirm {instance_id}` to validate"
            )
            bot.send_alert(msg)

        if eval_result.get("SpikeDetected", False):
            msg = (
                f"🚨 CPU Spike Detected: `{instance_id}` in `{region}`\n"
                f"• From: ~{eval_result.get('AvgCPU', 0):.2f}% → To: {eval_result.get('RecentCPUSpike', 0):.2f}%\n"
                f"• Monthly Forecast: ${cost_estimate:.2f}"
            )
            bot.send_alert(msg)

if __name__ == "__main__":
    main()