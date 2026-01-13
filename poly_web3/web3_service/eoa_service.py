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
        condition_ids: str | list[str],
        batch_size: int = 10,
    ):
        raise ImportError("EOA wallet redeem not supported")

    def redeem_all(self, batch_size: int = 10) -> list[dict]:
        raise ImportError("EOA wallet redeem not supported")
