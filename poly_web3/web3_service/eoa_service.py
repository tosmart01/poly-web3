# -*- coding = utf-8 -*-
# @Time: 2025-12-27 16:01:09
# @Author: PinBar
# @Site:
# @File: eoa_service.py
# @Software: PyCharm
from decimal import Decimal

from poly_web3.const import USDC_POLYGON, ZERO_BYTES32
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

    def split(
        self,
        condition_id: str,
        amount: int | float | str | Decimal,
        collateral_token: str = USDC_POLYGON,
        parent_collection_id: str = ZERO_BYTES32,
    ) -> dict | None:
        raise ImportError("EOA wallet split not supported")

    def merge(
        self,
        condition_id: str,
        amount: int | float | str | Decimal,
        collateral_token: str = USDC_POLYGON,
        parent_collection_id: str = ZERO_BYTES32,
    ) -> dict | None:
        raise ImportError("EOA wallet merge not supported")
