# src/core/logger.py

import logging
import sys

def setup_logger(name):
    """Set up structured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s: %(message)s")
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger

# Export shared logger
logger = setup_logger(__name__)