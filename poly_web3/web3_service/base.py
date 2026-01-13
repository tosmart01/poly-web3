# -*- coding = utf-8 -*-
# @Time: 2025-12-27 15:57:07
# @Author: PinBar
# @Site:
# @File: base.py
# @Software: PyCharm
from typing import Any

from py_builder_relayer_client.client import RelayClient
from py_clob_client.client import ClobClient
from web3 import Web3
import requests

from poly_web3.const import (
    RPC_URL,
    CTF_ADDRESS,
    CTF_ABI_PAYOUT,
    ZERO_BYTES32,
    USDC_POLYGON,
    CTF_ABI_REDEEM,
    NEG_RISK_ADAPTER_ADDRESS,
    RELAYER_URL,
    POL,
    AMOY,
    GET_RELAY_PAYLOAD,
    NEG_RISK_ADAPTER_ABI_REDEEM,
)
from poly_web3.schema import WalletType
from poly_web3.log import logger


class BaseWeb3Service:
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
        self.w3: Web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if self.wallet_type == WalletType.PROXY and relayer_client is None:
            raise Exception("relayer_client must be provided")

    def _resolve_user_address(self):
        funder = getattr(getattr(self.clob_client, "builder", None), "funder", None)
        if funder:
            return funder
        return self.clob_client.get_address()

    @classmethod
    def fetch_positions(cls, user_address: str) -> list[dict]:
        """
        Fetches current positions for a user from the official Polymarket API.

        :param user_address: User wallet address (0x-prefixed, 40 hex chars)
        :return: List of position dictionaries from the API
        """
        url = "https://data-api.polymarket.com/positions"
        params = {
            "user": user_address,
            "sizeThreshold": 1,
            "limit": 100,
            "redeemable": True,
            "sortBy": "RESOLVING",
            "sortDirection": "DESC",
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            positions = response.json()
            return [i for i in positions if i.get("percentPnl") > 0]
        except Exception as e:
            logger.error(f"Failed to fetch positions from API: {e}")
            return []

    @classmethod
    def fetch_positions_by_condition_ids(
            cls, user_address: str, condition_ids: list[str]
    ) -> list[dict]:
        """
        Fetches positions for a user filtered by condition IDs.

        :param user_address: User wallet address (0x-prefixed, 40 hex chars)
        :param condition_ids: List of condition IDs to filter by
        :return: List of position dictionaries from the API
        """
        if not condition_ids:
            return []
        url = "https://data-api.polymarket.com/positions"
        params = {
            "user": user_address,
            "market": ",".join(condition_ids),
            "sizeThreshold": 1
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            positions = response.json()
            return [i for i in positions if i.get("percentPnl") > 0]
        except Exception as e:
            print(f"Failed to fetch positions from API: {e}")
            return []

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
        owner_checksum = Web3.to_checksum_address(owner)
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
        # 只需要 calldata：encodeABI 即可
        return ctf.functions.redeemPositions(
            USDC_POLYGON,
            ZERO_BYTES32,
            condition_id,
            [1, 2],
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

    def _build_redeem_tx(self, to: str, data: str) -> Any:
        raise NotImplementedError("redeem tx builder not implemented")

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

    def _submit_redeem(self, txs: list[Any]) -> dict | None:
        raise NotImplementedError("redeem submit not implemented")

    def _redeem_batch(self, condition_ids: list[str], batch_size: int) -> list[dict]:
        """
        Fetch positions by condition IDs in batches, then redeem each batch.
        """
        if not condition_ids:
            return []
        user_address = self._resolve_user_address()
        redeem_list = []
        for batch in self._chunk_condition_ids(condition_ids, batch_size):
            positions = self.fetch_positions_by_condition_ids(
                user_address=user_address, condition_ids=batch
            )
            redeem_list.extend(self._redeem_from_positions(positions, len(batch)))
        return redeem_list

    def _redeem_from_positions(
            self, positions: list[dict], batch_size: int
    ) -> list[dict]:
        """
        Build and submit redeem transactions from a list of positions.
        """
        if not positions:
            return []
        positions_by_condition: dict[str, list[dict]] = {}
        for pos in positions:
            condition_id = pos.get("conditionId")
            if not condition_id:
                continue
            positions_by_condition.setdefault(condition_id, []).append(pos)

        redeem_list = []
        error_list: list[str] = []
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
                redeem_list.append(redeem_res)
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
                error_list.extend(batch)
                logger.info(f"redeem batch error, {batch=}, error={e}")
        if error_list:
            logger.warning(f"error redeem condition list, {error_list}")
        return redeem_list

    @classmethod
    def _get_relay_payload(cls, address: str, wallet_type: WalletType):
        return requests.get(
            RELAYER_URL + GET_RELAY_PAYLOAD,
            params={"address": address, "type": wallet_type},
        ).json()

    def get_contract_config(self) -> dict:
        if self.clob_client.chain_id == 137:
            return POL
        elif self.clob_client.chain_id == 80002:
            return AMOY
        raise Exception("Invalid network")

    def estimate_gas(self, tx):
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_estimateGas",
            "params": [tx],
            "id": 1,
        }

        response = requests.post(self.rpc_url, json=payload)
        result = response.json()

        if "result" in result:
            # 返回的是16进制 gas 数量
            gas_hex = result["result"]
            return str(int(gas_hex, 16))
        else:
            raise Exception("Estimate gas error: " + str(result))

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

    def redeem(
            self,
            condition_ids: str | list[str],
            batch_size: int = 10,
    ):
        """
        Redeem positions for the given condition IDs.
        """
        if isinstance(condition_ids, str):
            condition_ids = [condition_ids]
        return self._redeem_batch(condition_ids, batch_size)

    def redeem_all(self, batch_size: int = 10) -> list[dict]:
        """
        Redeem all currently redeemable positions for the user.
        """
        positions = self.fetch_positions(user_address=self._resolve_user_address())
        return self._redeem_from_positions(positions, batch_size)
