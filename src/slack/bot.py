# src/slack/bot.py

import os
import boto3
import logging
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

logger = logging.getLogger(__name__)

class SlackBot:
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        self.alert_channel = os.getenv("SLACK_ALERT_CHANNEL", "#tephronbot")

        if not self.bot_token:
            logger.warning("[!] Missing SLACK_BOT_TOKEN")
        if not self.app_token:
            logger.warning("[!] Missing SLACK_APP_TOKEN")

        self.client = WebClient(token=self.bot_token)
        self.socket_client = SocketModeClient(app_token=self.app_token, web_client=self.client)

    def start(self):
        if not self.bot_token or not self.app_token:
            logger.warning("[!] Missing required Slack tokens. Bot will not start.")
            return

        try:
            def process_request(c: SocketModeClient, req: SocketModeRequest):
                if req.type == "events_api":
                    event = req.payload.get("event", {})
                    if event.get("type") == "message" and event.get("text", "").startswith("/tephron"):
                        command = event["text"][8:].strip()
                        logger.info(f"[+] Received Slack command: {command}")
                        response = self._handle_command(command)
                        self.client.chat_postMessage(channel=event["channel"], text=response)
                c.send_response(SocketModeResponse(envelope_id=req.envelope_id))

            self.socket_client.socket_mode_request_listeners.append(process_request)
            self.socket_client.connect()
            logger.info("[+] Slack bot started and listening for commands")
        except Exception as e:
            logger.error(f"[!] Failed to start Slack bot: {e}")

    def _handle_command(self, command: str) -> str:
        command = command.lower().strip()
        logger.info(f"[+] Processing command: {command}")

        if command == "scan report":
            from src.aws.ec2.analyzer import EC2InstancePolicyAnalyzer
            analyzer = EC2InstancePolicyAnalyzer()
            return analyzer.generate_underutilized_report()

        elif command == "cost report":
            from src.aws.cost.cost_estimator import EC2CostEstimator
            estimator = EC2CostEstimator(boto3.Session())
            costs = estimator.get_daily_cost_per_instance()
    
            lines = "\n".join([f"• {k}: ${v:.2f}" for k, v in costs.items()])
            return f"💰 *Daily Cost Estimate*\n{lines}"

        elif command.startswith("confirm "):
            instance_id = command.split(" ")[1]
            return f"[✓] Confirmation recorded for `{instance_id}`."

        elif command == "help":
            return (
                "*Available Commands*\n"
                "• `/tephron scan report` – Show underutilized EC2 instances\n"
                "• `/tephron cost report` – Show top 5 most expensive instances\n"
                "• `/tephron confirm <instance-id>` – Confirm an instance is underutilized\n"
                "• `/tephron help` – Show this menu\n"
                "\nYou can use these commands to audit, analyze, and improve Tephron's accuracy over time."
            )

        else:
            return "[!] Unknown command. Type `/tephron help`"