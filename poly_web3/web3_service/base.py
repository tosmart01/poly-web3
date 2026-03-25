# -*- coding = utf-8 -*-
# @Time: 2025-12-27 15:57:07
# @Author: PinBar
# @Site:
# @File: base.py
# @Software: PyCharm
from typing import Any
from decimal import Decimal, InvalidOperation, ROUND_DOWN
import re

from py_builder_relayer_client.client import RelayClient
from py_clob_client.client import ClobClient
from eth_utils import to_checksum_address
from web3 import Web3

from poly_web3.const import (
    RPC_URL,
    CTF_ADDRESS,
    CTF_ABI_PAYOUT,
    ZERO_BYTES32,
    USDC_POLYGON,
    CTF_ABI_REDEEM,
    CTF_ABI_SPLIT,
    CTF_ABI_MERGE,
    NEG_RISK_ADAPTER_ADDRESS,
    POL,
    AMOY,
    NEG_RISK_ADAPTER_ABI_REDEEM,
    NEG_RISK_ADAPTER_ABI_SPLIT,
    NEG_RISK_ADAPTER_ABI_MERGE,
)
from poly_web3.schema import (
    BatchBinaryOperationItem,
    BatchBinaryOperationErrorItem,
    BatchBinaryOperationResult,
    BatchBinaryOperationSuccessItem,
    MergeAllResult,
    MergeErrorItem,
    MergePlanItem,
    MergeSuccessItem,
    RedeemErrorItem,
    RedeemResult,
    WalletType,
)
from poly_web3.log import logger
from poly_web3.web3_service.api_client import PolymarketAPIClient


class BaseWeb3Service:
    RELAYER_DAILY_SUBMIT_LIMIT = 100
    RELAYER_RECOMMENDED_SUBMIT_INTERVAL_MINUTES = 15

    def __init__(
            self,
            clob_client: ClobClient = None,
            relayer_client: RelayClient = None,
            rpc_url: str | None = None,
    ):
        self.relayer_client = relayer_client
        self.clob_client: ClobClient = clob_client
        if self.clob_client:
            self.wallet_type: WalletType = WalletType.get_with_code(
                self.clob_client.builder.sig_type
            )
        else:
            self.wallet_type = WalletType.PROXY
        self.rpc_url = rpc_url or RPC_URL
        self.api_client = PolymarketAPIClient(rpc_url=self.rpc_url)
        self.w3: Web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if self.wallet_type == WalletType.PROXY and relayer_client is None:
            raise Exception("relayer_client must be provided")

    def _resolve_user_address(self):
        funder = getattr(getattr(self.clob_client, "builder", None), "funder", None)
        if funder:
            return funder
        return self.clob_client.get_address()

    def is_condition_resolved(self, condition_id: str) -> bool:
        ctf = self.w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI_PAYOUT)
        return ctf.functions.payoutDenominator(condition_id).call() > 0

    def get_winning_indexes(self, condition_id: str) -> list[int]:
        ctf = self.w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI_PAYOUT)
        if not self.is_condition_resolved(condition_id):
            return []
        outcome_count = ctf.functions.getOutcomeSlotCount(condition_id).call()
        winners: list[int] = []
        for i in range(outcome_count):
            if ctf.functions.payoutNumerators(condition_id, i).call() > 0:
                winners.append(i)
        return winners

    def get_redeemable_index_and_balance(
            self, condition_id: str
    ) -> list[tuple]:
        owner = self._resolve_user_address()
        winners = self.get_winning_indexes(condition_id)
        if not winners:
            return []
        ctf = self.w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI_PAYOUT)
        owner_checksum = to_checksum_address(owner)
        redeemable: list[tuple] = []
        for index in winners:
            index_set = 1 << index
            collection_id = ctf.functions.getCollectionId(
                ZERO_BYTES32, condition_id, index_set
            ).call()
            position_id = ctf.functions.getPositionId(
                USDC_POLYGON, collection_id
            ).call()
            balance = ctf.functions.balanceOf(owner_checksum, position_id).call()
            if balance > 0:
                redeemable.append((index, balance / 1000000))
        return redeemable

    def build_ctf_redeem_tx_data(self, condition_id: str) -> str:
        ctf = self.w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI_REDEEM)
        return ctf.functions.redeemPositions(
            USDC_POLYGON,
            ZERO_BYTES32,
            condition_id,
            [1, 2],
        )._encode_transaction_data()

    def build_ctf_split_tx_data(
            self,
            condition_id: str,
            partition: list[int],
            amount: int,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
    ) -> str:
        ctf = self.w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI_SPLIT)
        return ctf.functions.splitPosition(
            collateral_token,
            parent_collection_id,
            condition_id,
            partition,
            amount,
        )._encode_transaction_data()

    def build_ctf_merge_tx_data(
            self,
            condition_id: str,
            partition: list[int],
            amount: int,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
    ) -> str:
        ctf = self.w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI_MERGE)
        return ctf.functions.mergePositions(
            collateral_token,
            parent_collection_id,
            condition_id,
            partition,
            amount,
        )._encode_transaction_data()

    def build_neg_risk_split_tx_data(
            self,
            condition_id: str,
            partition: list[int],
            amount: int,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
    ) -> str:
        nr_adapter = self.w3.eth.contract(
            address=NEG_RISK_ADAPTER_ADDRESS, abi=NEG_RISK_ADAPTER_ABI_SPLIT
        )
        return nr_adapter.functions.splitPosition(
            collateral_token,
            parent_collection_id,
            condition_id,
            partition,
            amount,
        )._encode_transaction_data()

    def build_neg_risk_merge_tx_data(
            self,
            condition_id: str,
            partition: list[int],
            amount: int,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
    ) -> str:
        nr_adapter = self.w3.eth.contract(
            address=NEG_RISK_ADAPTER_ADDRESS, abi=NEG_RISK_ADAPTER_ABI_MERGE
        )
        return nr_adapter.functions.mergePositions(
            collateral_token,
            parent_collection_id,
            condition_id,
            partition,
            amount,
        )._encode_transaction_data()

    def build_neg_risk_redeem_tx_data(
            self, condition_id: str, redeem_amounts: list[int]
    ) -> str:
        nr_adapter = self.w3.eth.contract(
            address=NEG_RISK_ADAPTER_ADDRESS, abi=NEG_RISK_ADAPTER_ABI_REDEEM
        )
        return nr_adapter.functions.redeemPositions(
            condition_id,
            redeem_amounts,
        )._encode_transaction_data()

    def get_market_by_condition_id(self, condition_id: str) -> dict | None:
        return self.api_client.get_market_by_condition_id(condition_id)

    def is_negative_risk_condition(self, condition_id: str) -> bool:
        market = self.get_market_by_condition_id(condition_id)
        return bool(market and market.get("negRisk"))

    def _resolve_negative_risk_flag(
            self, condition_id: str, negative_risk: bool | None
    ) -> bool:
        if negative_risk is not None:
            return negative_risk
        return self.is_negative_risk_condition(condition_id)

    def _build_redeem_tx(self, to: str, data: str) -> Any:
        raise NotImplementedError("redeem tx builder not implemented")

    def _build_ctf_tx(self, to: str, data: str) -> Any:
        return self._build_redeem_tx(to, data)

    @staticmethod
    def _normalize_batch_binary_operation_items(
            operations: list[BatchBinaryOperationItem | dict]
    ) -> list[BatchBinaryOperationItem]:
        if not operations:
            raise Exception("operations must not be empty")
        return [BatchBinaryOperationItem.model_validate(item) for item in operations]

    def _build_binary_market_tx(
            self,
            action: str,
            condition_id: str,
            amount: int | float | str | Decimal,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
            negative_risk: bool | None = None,
    ) -> tuple[bool, Any]:
        is_negative_risk = self._resolve_negative_risk_flag(
            condition_id=condition_id,
            negative_risk=negative_risk,
        )
        amount_base_units = self._to_usdc_base_units(amount)
        to = NEG_RISK_ADAPTER_ADDRESS if is_negative_risk else CTF_ADDRESS

        if action == "split":
            data = (
                self.build_neg_risk_split_tx_data(
                    condition_id=condition_id,
                    partition=[1, 2],
                    amount=amount_base_units,
                    collateral_token=collateral_token,
                    parent_collection_id=parent_collection_id,
                )
                if is_negative_risk
                else self.build_ctf_split_tx_data(
                    condition_id=condition_id,
                    partition=[1, 2],
                    amount=amount_base_units,
                    collateral_token=collateral_token,
                    parent_collection_id=parent_collection_id,
                )
            )
        elif action == "merge":
            data = (
                self.build_neg_risk_merge_tx_data(
                    condition_id=condition_id,
                    partition=[1, 2],
                    amount=amount_base_units,
                    collateral_token=collateral_token,
                    parent_collection_id=parent_collection_id,
                )
                if is_negative_risk
                else self.build_ctf_merge_tx_data(
                    condition_id=condition_id,
                    partition=[1, 2],
                    amount=amount_base_units,
                    collateral_token=collateral_token,
                    parent_collection_id=parent_collection_id,
                )
            )
        else:
            raise Exception(f"unsupported action: {action}")

        tx = self._build_ctf_tx(to, data)
        return is_negative_risk, tx

    def _submit_binary_market_batch(
            self,
            action: str,
            operations: list[BatchBinaryOperationItem | dict],
            batch_size: int = 10,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
    ) -> BatchBinaryOperationResult:
        normalized_operations = self._normalize_batch_binary_operation_items(
            operations
        )
        if batch_size <= 0:
            raise Exception("batch_size must be greater than 0")
        grouped_operations: dict[bool, list[tuple[BatchBinaryOperationItem, Any]]] = {
            False: [],
            True: [],
        }

        for operation in normalized_operations:
            is_negative_risk, tx = self._build_binary_market_tx(
                action=action,
                condition_id=operation.condition_id,
                amount=operation.amount,
                collateral_token=collateral_token,
                parent_collection_id=parent_collection_id,
                negative_risk=operation.negative_risk,
            )
            grouped_operations[is_negative_risk].append((operation, tx))

        batch_result = BatchBinaryOperationResult()
        for is_negative_risk in (False, True):
            grouped = grouped_operations[is_negative_risk]
            if not grouped:
                continue
            for grouped_chunk in self._chunk_grouped_operations(grouped, batch_size):
                condition_ids = [item.condition_id for item, _ in grouped_chunk]
                txs = [tx for _, tx in grouped_chunk]
                try:
                    submit_result = self._submit_transactions(txs, action)
                    if submit_result is None:
                        raise Exception(f"{action} execute returned None")
                    batch_result.success_list.append(
                        BatchBinaryOperationSuccessItem(
                            negative_risk=is_negative_risk,
                            condition_ids=condition_ids,
                            result=submit_result,
                        )
                    )
                except Exception as exc:
                    batch_result.error_list.append(
                        BatchBinaryOperationErrorItem(
                            negative_risk=is_negative_risk,
                            condition_ids=condition_ids,
                            error=str(exc),
                        )
                    )
        return batch_result

    def _build_redeem_txs_from_positions(self, positions: list[dict]) -> list[Any]:
        neg_amounts_by_condition: dict[str, list[float]] = {}
        normal_conditions: set[str] = set()
        for pos in positions:
            condition_id = pos.get("conditionId")
            if not condition_id:
                continue
            if pos.get("negativeRisk"):
                idx = pos.get("outcomeIndex")
                size = pos.get("size")
                if idx is None or size is None:
                    continue
                amounts = neg_amounts_by_condition.setdefault(condition_id, [0.0, 0.0])
                if idx not in (0, 1):
                    raise Exception(f"negRisk outcomeIndex out of range: {idx}")
                amounts[idx] += size
            else:
                normal_conditions.add(condition_id)
        txs: list[Any] = []
        for condition_id, amounts in neg_amounts_by_condition.items():
            int_amounts = [int(amount * 1e6) for amount in amounts]
            txs.append(
                self._build_redeem_tx(
                    NEG_RISK_ADAPTER_ADDRESS,
                    self.build_neg_risk_redeem_tx_data(condition_id, int_amounts),
                )
            )
        for condition_id in normal_conditions:
            txs.append(
                self._build_redeem_tx(
                    CTF_ADDRESS,
                    self.build_ctf_redeem_tx_data(condition_id),
                )
            )
        return txs

    def _submit_transactions(self, txs: list[Any], metadata: str) -> dict | None:
        raise NotImplementedError("transaction submit not implemented")

    def _submit_redeem(self, txs: list[Any]) -> dict | None:
        return self._submit_transactions(txs, "redeem")

    @staticmethod
    def _normalize_position_size(size: Any) -> float:
        try:
            return float(size or 0)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _build_merge_plan_from_positions(
            cls,
            positions: list[dict],
            min_usdc: int | float | str | Decimal = 5,
            exclude_neg_risk: bool = True,
    ) -> list[MergePlanItem]:
        min_usdc_float = float(Decimal(str(min_usdc)))
        positions_by_condition: dict[str, list[dict]] = {}
        for pos in positions:
            condition_id = pos.get("conditionId")
            if not condition_id:
                continue
            positions_by_condition.setdefault(condition_id, []).append(pos)

        plan_list: list[MergePlanItem] = []
        for condition_id, condition_positions in positions_by_condition.items():
            yes_balance = 0.0
            no_balance = 0.0
            negative_risk = False
            market_slug = None
            invalid_outcome_index = False

            for pos in condition_positions:
                market_slug = market_slug or pos.get("slug")
                negative_risk = negative_risk or bool(pos.get("negativeRisk"))
                outcome_index = pos.get("outcomeIndex")
                size = cls._normalize_position_size(pos.get("size"))
                if outcome_index == 0:
                    yes_balance += size
                elif outcome_index == 1:
                    no_balance += size
                else:
                    invalid_outcome_index = True

            mergeable = min(yes_balance, no_balance)
            reason = None
            if invalid_outcome_index:
                reason = "unsupported_outcome_index"
            elif exclude_neg_risk and negative_risk:
                reason = "negative_risk_excluded"
            elif yes_balance <= 0 or no_balance <= 0:
                reason = "missing_opposite_side"
            elif mergeable < min_usdc_float:
                reason = "below_min_usdc"

            plan_list.append(
                MergePlanItem(
                    condition_id=condition_id,
                    market_slug=market_slug,
                    yes_balance=yes_balance,
                    no_balance=no_balance,
                    mergeable=mergeable,
                    negative_risk=negative_risk,
                    reason=reason,
                )
            )

        return sorted(
            plan_list,
            key=lambda item: (
                item.reason is not None,
                -item.mergeable,
                item.market_slug or "",
                item.condition_id,
            ),
        )

    @staticmethod
    def _build_redeem_error_items(
            batch_positions: list[dict], error: Exception
    ) -> list[RedeemErrorItem]:
        error_message = str(error)
        error_items: list[RedeemErrorItem] = []
        seen_condition_ids: set[str] = set()

        for pos in batch_positions:
            condition_id = pos.get("conditionId")
            if not condition_id or condition_id in seen_condition_ids:
                continue
            seen_condition_ids.add(condition_id)
            error_items.append(
                RedeemErrorItem(
                    condition_id=condition_id,
                    market_slug=pos.get("slug"),
                    error=error_message,
                )
            )
        return error_items

    def _redeem_batch(
            self, condition_ids: list[str], batch_size: int
    ) -> RedeemResult:
        """
        Fetch positions by condition IDs in batches, then redeem each batch.
        """
        if not condition_ids:
            return RedeemResult()
        user_address = self._resolve_user_address()
        redeem_result = RedeemResult()
        for batch in self._chunk_condition_ids(condition_ids, batch_size):
            positions = self.api_client.fetch_positions_by_condition_ids(
                user_address=user_address, condition_ids=batch
            )
            batch_result = self._redeem_from_positions(positions, len(batch))
            redeem_result.success_list.extend(batch_result.success_list)
            redeem_result.error_list.extend(batch_result.error_list)
        return redeem_result

    def _redeem_from_positions(
            self, positions: list[dict], batch_size: int
    ) -> RedeemResult:
        """
        Build and submit redeem transactions from a list of positions.
        """
        if not positions:
            return RedeemResult()
        positions_by_condition: dict[str, list[dict]] = {}
        for pos in positions:
            condition_id = pos.get("conditionId")
            if not condition_id:
                continue
            positions_by_condition.setdefault(condition_id, []).append(pos)

        redeem_result = RedeemResult()
        condition_ids = list(positions_by_condition.keys())
        for batch in self._chunk_condition_ids(condition_ids, batch_size):
            batch_positions = []
            for condition_id in batch:
                batch_positions.extend(positions_by_condition.get(condition_id, []))
            try:
                txs = self._build_redeem_txs_from_positions(batch_positions)
                if not txs:
                    continue
                redeem_res = self._submit_redeem(txs)
                if redeem_res is None:
                    raise Exception("redeem execute returned None")
                redeem_result.success_list.append(redeem_res)
                for pos in batch_positions:
                    buy_price = pos.get("avgPrice")
                    size = pos.get("size")
                    if not buy_price or not size:
                        continue
                    volume = 1 / buy_price * (buy_price * size)
                    logger.info(
                        f"{pos.get('slug')} redeem success, volume={volume:.4f} usdc"
                    )
            except Exception as e:
                redeem_result.error_list.extend(
                    self._build_redeem_error_items(batch_positions, e)
                )
                logger.error(f"redeem batch error, {batch=}, error={e}")
        if redeem_result.error_list:
            logger.warning(
                "error redeem condition list, "
                f"{[item.condition_id for item in redeem_result.error_list]}"
            )
        return redeem_result

    def _get_relay_payload(self, address: str, wallet_type: WalletType):
        return self.api_client.get_relay_payload(address, wallet_type)

    @classmethod
    def _raise_relayer_quota_exceeded_if_needed(cls, error_payload: Any):
        if error_payload is None:
            return
        if isinstance(error_payload, dict):
            raw_error = (
                str(error_payload.get("error"))
                if error_payload.get("error") is not None
                else str(error_payload.get("message") or error_payload)
            )
        else:
            raw_error = str(error_payload)

        if "quota exceeded" not in raw_error.lower():
            return

        reset_seconds = cls._extract_quota_reset_seconds(raw_error)
        reset_hint = ""
        if reset_seconds is not None:
            reset_hint = f" 当前剩余额度将在约 {reset_seconds} 秒后重置。"
        raise Exception(
            "Polymarket relayer 提交配额已超限：每天最多提交 "
            f"{cls.RELAYER_DAILY_SUBMIT_LIMIT} 次。"
            "建议降低调用频率（例如每 "
            f"{cls.RELAYER_RECOMMENDED_SUBMIT_INTERVAL_MINUTES} 分钟最多执行 1 次）。"
            f"{reset_hint} 原始错误: {raw_error}"
        )

    @staticmethod
    def _extract_quota_reset_seconds(raw_error: str) -> int | None:
        match = re.search(r"resets in (\d+) seconds", raw_error, re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1))

    def get_contract_config(self) -> dict:
        if self.clob_client.chain_id == 137:
            return POL
        elif self.clob_client.chain_id == 80002:
            return AMOY
        raise Exception("Invalid network")

    def estimate_gas(self, tx):
        return self.api_client.estimate_gas(tx)

    @classmethod
    def _chunk_condition_ids(
            cls, condition_ids: list[str], batch_size: int
    ) -> list[list[str]]:
        if batch_size <= 0:
            raise Exception("batch_size must be greater than 0")
        return [
            condition_ids[i: i + batch_size]
            for i in range(0, len(condition_ids), batch_size)
        ]

    @classmethod
    def _chunk_grouped_operations(
            cls,
            grouped_operations: list[tuple[BatchBinaryOperationItem, Any]],
            batch_size: int,
    ) -> list[list[tuple[BatchBinaryOperationItem, Any]]]:
        if batch_size <= 0:
            raise Exception("batch_size must be greater than 0")
        return [
            grouped_operations[i: i + batch_size]
            for i in range(0, len(grouped_operations), batch_size)
        ]

    @staticmethod
    def _to_usdc_base_units(amount: int | float | str | Decimal) -> int:
        try:
            if isinstance(amount, Decimal):
                human = amount
            elif isinstance(amount, int):
                human = Decimal(amount)
            else:
                human = Decimal(str(amount))
        except (InvalidOperation, ValueError) as exc:
            raise Exception(f"invalid amount: {amount}") from exc
        if human <= 0:
            raise Exception("amount must be greater than 0")
        base_units = (human * Decimal("1000000")).quantize(
            Decimal("1"), rounding=ROUND_DOWN
        )
        if base_units <= 0:
            raise Exception("amount too small after conversion")
        return int(base_units)

    def redeem(
            self,
            condition_ids: str | list[str],
            batch_size: int = 10,
    ) -> RedeemResult:
        """
        Redeem positions for the given condition IDs.
        """
        if isinstance(condition_ids, str):
            condition_ids = [condition_ids]
        return self._redeem_batch(condition_ids, batch_size)

    def redeem_all(self, batch_size: int = 10) -> RedeemResult:
        """
        Redeem all currently redeemable positions for the user.
        """
        positions = self.api_client.fetch_redeemable_positions(
            user_address=self._resolve_user_address()
        )
        return self._redeem_from_positions(positions, batch_size)

    def plan_merge_all(
            self,
            min_usdc: int | float | str | Decimal = 0.5,
            exclude_neg_risk: bool = False,
    ) -> list[MergePlanItem]:
        """
        Scan current positions and compute merge opportunities without executing.
        """
        positions = self.api_client.fetch_all_mergeable_positions(
            user_address=self._resolve_user_address()
        )
        return self._build_merge_plan_from_positions(
            positions=positions,
            min_usdc=min_usdc,
            exclude_neg_risk=exclude_neg_risk,
        )

    def merge_all(
            self,
            min_usdc: int | float | str | Decimal = 0.5,
            exclude_neg_risk: bool = False,
            max_markets: int = 100,
            batch_size: int = 10,
    ) -> MergeAllResult:
        """
        Plan and optionally execute merge operations across all mergeable markets.
        """
        if max_markets <= 0:
            raise Exception("max_markets must be greater than 0")

        plan_list = self.plan_merge_all(
            min_usdc=min_usdc,
            exclude_neg_risk=exclude_neg_risk,
        )
        merge_result = MergeAllResult(
            plan_list=plan_list,
        )

        min_usdc_float = float(Decimal(str(min_usdc)))

        executable_plans = [
            item
            for item in plan_list
            if item.reason is None
            and item.mergeable > 0
            and item.mergeable >= min_usdc_float
        ][:max_markets]
        if not executable_plans:
            return merge_result

        plan_by_condition = {
            item.condition_id: item for item in executable_plans
        }
        batch_result = self.merge_batch(
            operations=[
                {
                    "condition_id": item.condition_id,
                    "amount": item.mergeable,
                    "negative_risk": item.negative_risk,
                }
                for item in executable_plans
            ],
            batch_size=batch_size,
        )

        for success in batch_result.success_list:
            for condition_id in success.condition_ids:
                item = plan_by_condition.get(condition_id)
                if item is None:
                    continue
                merge_result.success_list.append(
                    MergeSuccessItem(
                        condition_id=item.condition_id,
                        market_slug=item.market_slug,
                        mergeable=item.mergeable,
                        result=success.result,
                    )
                )
                logger.info(
                    f"{item.market_slug} merge success, mergeable={item.mergeable:.4f} usdc"
                )

        for error in batch_result.error_list:
            for condition_id in error.condition_ids:
                item = plan_by_condition.get(condition_id)
                if item is None:
                    continue
                merge_result.error_list.append(
                    MergeErrorItem(
                        condition_id=item.condition_id,
                        market_slug=item.market_slug,
                        mergeable=item.mergeable,
                        error=error.error,
                    )
                )
                logger.error(
                    "merge market error, "
                    f"condition_id={item.condition_id}, market_slug={item.market_slug}, error={error.error}"
                )
        return merge_result

    def split(
            self,
            condition_id: str,
            amount: int | float | str | Decimal,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
            negative_risk: bool | None = None,
    ) -> dict | None:
        """
        Split a binary market (Yes/No) position, amount in human units.
        """
        _, tx = self._build_binary_market_tx(
            action="split",
            condition_id=condition_id,
            amount=amount,
            collateral_token=collateral_token,
            parent_collection_id=parent_collection_id,
            negative_risk=negative_risk,
        )
        return self._submit_transactions([tx], "split")

    def split_batch(
            self,
            operations: list[BatchBinaryOperationItem | dict],
            batch_size: int = 10,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
    ) -> BatchBinaryOperationResult:
        """
        Split multiple binary markets in batches. Each operation carries its own amount.
        """
        return self._submit_binary_market_batch(
            action="split",
            operations=operations,
            batch_size=batch_size,
            collateral_token=collateral_token,
            parent_collection_id=parent_collection_id,
        )

    def merge(
            self,
            condition_id: str,
            amount: int | float | str | Decimal,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
            negative_risk: bool | None = None,
    ) -> dict | None:
        """
        Merge binary positions (Yes/No) back into a single position,
        amount in human units.
        """
        _, tx = self._build_binary_market_tx(
            action="merge",
            condition_id=condition_id,
            amount=amount,
            collateral_token=collateral_token,
            parent_collection_id=parent_collection_id,
            negative_risk=negative_risk,
        )
        return self._submit_transactions([tx], "merge")

    def merge_batch(
            self,
            operations: list[BatchBinaryOperationItem | dict],
            batch_size: int = 10,
            collateral_token: str = USDC_POLYGON,
            parent_collection_id: str = ZERO_BYTES32,
    ) -> BatchBinaryOperationResult:
        """
        Merge multiple binary markets in batches. Each operation carries its own amount.
        """
        return self._submit_binary_market_batch(
            action="merge",
            operations=operations,
            batch_size=batch_size,
            collateral_token=collateral_token,
            parent_collection_id=parent_collection_id,
        )
