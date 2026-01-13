# -*- coding = utf-8 -*-
# @Time: 2026-01-13 14:40:20
# @Author: PinBar
# @Site: 
# @File: log.py
# @Software: PyCharm
import logging
import sys

LOGGER_NAME = "poly_web3"

logger = logging.getLogger(LOGGER_NAME)
logger.addHandler(logging.NullHandler())


def configure_logging(
        level: int = logging.INFO,
        stream=sys.stdout,
        formatter: logging.Formatter | None = None,
):
    if formatter is None:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    target = logging.getLogger(LOGGER_NAME)
    for existing in list(target.handlers):
        if isinstance(existing, logging.StreamHandler):
            target.removeHandler(existing)
    target.addHandler(handler)
    target.setLevel(level)
    return target


def _ensure_default_logging():
    target = logging.getLogger(LOGGER_NAME)
    if target.handlers and not all(
        isinstance(h, logging.NullHandler) for h in target.handlers
    ):
        return
    if logging.getLogger().handlers:
        return
    configure_logging()


_ensure_default_logging()
