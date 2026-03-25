# -*- coding = utf-8 -*-
# @Time: 2025-12-27 16:01:09
# @Author: PinBar
# @Site:
# @File: eoa_service.py
# @Software: PyCharm
from decimal import Decimal

from poly_web3.const import USDC_POLYGON, ZERO_BYTES32
from poly_web3.schema import (
    BatchBinaryOperationItem,
    BatchBinaryOperationResult,
    MergeAllResult,
    MergePlanItem,
    RedeemResult,
)
from poly_web3.web3_service.base import BaseWeb3Service


class EOAWeb3Service(BaseWeb3Service):
    def redeem(
        self,
        condition_ids: str | list[str],
        batch_size: int = 10,
    ) -> RedeemResult:
        raise ImportError("EOA wallet redeem not supported")

    def redeem_all(self, batch_size: int = 10) -> RedeemResult:
        raise ImportError("EOA wallet redeem not supported")

    def plan_merge_all(
        self,
        min_usdc: int | float | str | Decimal = 5,
        exclude_neg_risk: bool = True,
    ) -> list[MergePlanItem]:
        raise ImportError("EOA wallet merge not supported")

    def merge_all(
        self,
        min_usdc: int | float | str | Decimal = 5,
        exclude_neg_risk: bool = True,
        max_markets: int = 20,
        batch_size: int = 10,
    ) -> MergeAllResult:
        raise ImportError("EOA wallet merge not supported")

    def split(
        self,
        condition_id: str,
        amount: int | float | str | Decimal,
        collateral_token: str = USDC_POLYGON,
        parent_collection_id: str = ZERO_BYTES32,
        negative_risk: bool | None = None,
    ) -> dict | None:
        raise ImportError("EOA wallet split not supported")

    def split_batch(
        self,
        operations: list[BatchBinaryOperationItem | dict],
        batch_size: int = 10,
        collateral_token: str = USDC_POLYGON,
        parent_collection_id: str = ZERO_BYTES32,
    ) -> BatchBinaryOperationResult:
        raise ImportError("EOA wallet split not supported")

    def merge(
        self,
        condition_id: str,
        amount: int | float | str | Decimal,
        collateral_token: str = USDC_POLYGON,
        parent_collection_id: str = ZERO_BYTES32,
        negative_risk: bool | None = None,
    ) -> dict | None:
        raise ImportError("EOA wallet merge not supported")

    def merge_batch(
        self,
        operations: list[BatchBinaryOperationItem | dict],
        batch_size: int = 10,
        collateral_token: str = USDC_POLYGON,
        parent_collection_id: str = ZERO_BYTES32,
    ) -> BatchBinaryOperationResult:
        raise ImportError("EOA wallet merge not supported")
