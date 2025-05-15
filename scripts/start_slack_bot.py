# scripts/start_slack_bot.py

import logging
from src.slack.bot import SlackBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("[*] Starting Tephron AI Slack Bot")

    bot = SlackBot()
    bot.start()

if __name__ == "__main__":
    main()