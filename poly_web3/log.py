# -*- coding = utf-8 -*-
# @Time: 2026-01-13 14:40:20
# @Author: PinBar
# @Site: 
# @File: log.py
# @Software: PyCharm
import sys
import logging

logger = logging.getLogger("poly_web3")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
