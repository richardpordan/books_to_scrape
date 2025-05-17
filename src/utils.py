"""Misc utils"""

import datetime
import logging


def create_logger(logs_folder_path = None):
    """Create a customised logger instance. Stream if no filepath provided."""
    lvl = logging.INFO
    fmt = "%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s"

    timestamp = str(datetime.datetime.now().isoformat())

    if not logs_folder_path:
        logging.basicConfig(
            level = lvl,
            format = fmt,
        )

    if logs_folder_path:
        logging.basicConfig(
            level = lvl,
            format = fmt,
            filename=f"{logs_folder_path}/log_{timestamp}.txt",
            encoding='utf-8',
        )

    logger = logging.getLogger(__name__)

    return logger
