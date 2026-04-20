import logging
import sys

def get_logger(name):
    """
    Returns a configured UTF-8 logger for the Market-Rover ecosystem.
    Strictly [Emoji-Free] and Python 3.13 compatible.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Ensure UTF-8 formatting
        formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
