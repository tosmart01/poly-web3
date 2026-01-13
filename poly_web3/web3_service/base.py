# -*- coding = utf-8 -*-
# @Time: 2025-12-27 15:57:07
# @Author: PinBar
# @Site:
# @File: base.py
# @Software: PyCharm
import requests
from py_builder_relayer_client.client import RelayClient
from py_clob_client.client import ClobClient
from web3 import Web3

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

    def redeem(
            self,
            condition_ids: str | list[str],
    ):  # noqa:
        raise ImportError()

    def redeem_all(self) -> list[dict] | None:
        raise ImportError()
