# === FILE: tree_mark/logging_config.py ===
from loguru import logger
import sys


def configure_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(sys.stderr, level=level, backtrace=True, diagnose=False, enqueue=True)