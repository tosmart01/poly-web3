# -*- coding = utf-8 -*-
# @Time: 2025-12-27 16:01:09
# @Author: PinBar
# @Site:
# @File: eoa_service.py
# @Software: PyCharm
from poly_web3.web3_service.base import BaseWeb3Service


class EOAWeb3Service(BaseWeb3Service):
    def redeem(
        self,
        condition_id: str,
        neg_risk: bool = False,
        redeem_amounts: list[int] | None = None,
    ):
        raise ImportError("EOA wallet redeem not supported")
