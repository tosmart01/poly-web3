# -*- coding = utf-8 -*-
# @Time: 2025/12/19 15:31
# @Author: PinBar
# @Site:
# @File: model.py
# @Software: PyCharm
from enum import Enum


class WalletType(str, Enum):
    EOA = "EOA"
    SAFE = "SAFE"
    PROXY = "PROXY"

    @classmethod
    def get_with_code(cls, code: int):
        if code == 0:
            return cls.EOA
        elif code == 1:
            return cls.PROXY
        elif code == 2:
            return cls.SAFE
