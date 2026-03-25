# -*- coding = utf-8 -*-
# @Time: 2026-03-25
# @Author: Codex
# @File: api_client.py
from typing import Any

import requests

from poly_web3.const import (
    DATA_API_POSITIONS_URL,
    GAMMA_MARKETS_URL,
    GET_RELAY_PAYLOAD,
    HTTP_REQUEST_TIMEOUT_SECONDS,
    RELAYER_URL,
    RPC_URL,
    SUBMIT_TRANSACTION,
)
from poly_web3.log import logger
from poly_web3.schema import WalletType


class PolymarketAPIClient:
    def __init__(
            self,
            rpc_url: str | None = None,
            relayer_url: str = RELAYER_URL,
            timeout: int = HTTP_REQUEST_TIMEOUT_SECONDS,
            session: requests.Session | None = None,
    ):
        self.rpc_url = rpc_url or RPC_URL
        self.relayer_url = relayer_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def fetch_redeemable_positions(self, user_address: str) -> list[dict]:
        params = {
            "user": user_address,
            "sizeThreshold": 1,
            "limit": 100,
            "redeemable": True,
            "sortBy": "RESOLVING",
            "sortDirection": "DESC",
        }
        try:
            response = self.session.get(
                DATA_API_POSITIONS_URL,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            positions = response.json()
            return [item for item in positions if self._is_positive_percent_pnl(item)]
        except Exception as exc:
            logger.error(f"Failed to fetch positions from API: {exc}")
            return []

    def fetch_positions_by_condition_ids(
            self, user_address: str, condition_ids: list[str]
    ) -> list[dict]:
        if not condition_ids:
            return []
        params = {
            "user": user_address,
            "market": ",".join(condition_ids),
            "sizeThreshold": 1,
        }
        try:
            response = self.session.get(
                DATA_API_POSITIONS_URL,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            positions = response.json()
            return [item for item in positions if self._is_positive_percent_pnl(item)]
        except Exception as exc:
            logger.error(f"Failed to fetch positions from API: {exc}")
            return []

    def fetch_all_positions(self, user_address: str) -> list[dict]:
        return self._fetch_all_positions(
            user_address=user_address,
            extra_params={},
        )

    def fetch_all_mergeable_positions(self, user_address: str) -> list[dict]:
        return self._fetch_all_positions(
            user_address=user_address,
            extra_params={"mergeable": True},
        )

    def _fetch_all_positions(
            self, user_address: str, extra_params: dict[str, Any]
    ) -> list[dict]:
        limit = 500
        offset = 0
        positions: list[dict] = []

        try:
            while True:
                params = {
                    "user": user_address,
                    "sizeThreshold": 1,
                    "limit": limit,
                    "offset": offset,
                    "sortBy": "TOKENS",
                    "sortDirection": "DESC",
                }
                params.update(extra_params)
                response = self.session.get(
                    DATA_API_POSITIONS_URL,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                page = response.json()
                if not isinstance(page, list) or not page:
                    break
                positions.extend(page)
                if len(page) < limit:
                    break
                offset += limit
            return positions
        except Exception as exc:
            logger.error(f"Failed to fetch all positions from API: {exc}")
            return []

    def get_market_by_condition_id(self, condition_id: str) -> dict | None:
        if not condition_id:
            return None
        try:
            response = self.session.get(
                GAMMA_MARKETS_URL,
                params={"condition_ids": condition_id, "limit": 1},
                timeout=self.timeout,
            )
            response.raise_for_status()
            markets = response.json()
            if isinstance(markets, list) and markets:
                return markets[0]
        except Exception as exc:
            logger.warning(
                f"failed to fetch market metadata for condition_id={condition_id}: {exc}"
            )
        return None

    def get_relay_payload(self, address: str, wallet_type: WalletType) -> dict:
        response = self.session.get(
            f"{self.relayer_url}{GET_RELAY_PAYLOAD}",
            params={"address": address, "type": wallet_type.value},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def submit_relayer_transaction(self, req: dict, headers: dict) -> dict:
        response = self.session.post(
            f"{self.relayer_url}{SUBMIT_TRANSACTION}",
            json=req,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def estimate_gas(self, tx: dict[str, Any]) -> str:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_estimateGas",
            "params": [tx],
            "id": 1,
        }
        response = self.session.post(
            self.rpc_url,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        if "result" not in result:
            raise Exception("Estimate gas error: " + str(result))
        return str(int(result["result"], 16))

    @staticmethod
    def _is_positive_percent_pnl(position: dict) -> bool:
        try:
            return float(position.get("percentPnl") or 0) > 0
        except (TypeError, ValueError):
            return False


DEFAULT_POLYMARKET_API_CLIENT = PolymarketAPIClient()
