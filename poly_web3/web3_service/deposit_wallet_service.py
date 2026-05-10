# -*- coding = utf-8 -*-
"""DepositWalletWeb3Service — POLY_1271 deposit wallet (CLOB signature_type=3)。

提交方式：构造 redeem / split / merge 的 calldata，封装成
``py_builder_relayer_client.models.DepositWalletCall`` 列表，再调
``relayer.execute_deposit_wallet_batch(...)``。
"""

import time as _time
from typing import Any

from poly_web3.const import (
    STATE_CONFIRMED,
    STATE_FAILED,
    STATE_MINED,
    SUBMIT_TRANSACTION,
)
from poly_web3.web3_service.base import BaseWeb3Service


class DepositWalletWeb3Service(BaseWeb3Service):
    """Polymarket v2 deposit wallet (EIP-1271)。

    所有 redeem/split/merge 通过 builder relayer 的
    ``execute_deposit_wallet_batch`` 提交。
    """

    DEFAULT_DEADLINE_SEC = 240

    def _build_redeem_tx(self, to: str, data: str) -> dict:
        # 字段与 ProxyWeb3Service 保持一致以复用基类逻辑；
        # 在 _submit_transactions 中再转成 DepositWalletCall。
        return {
            "to": to,
            "data": data,
            "value": 0,
        }

    def _submit_transactions(self, txs: list[dict], metadata: str) -> dict:
        if self.clob_client is None:
            raise Exception("clob_client not found")
        if self.relayer_client is None:
            raise Exception("relayer_client must be provided for DEPOSIT_WALLET")
        if not txs:
            raise Exception("empty tx batch")

        # 局部 import 避免 module 顶层引入 relayer client 失败时影响其他 service。
        from py_builder_relayer_client.models import (
            DepositWalletCall,
            TransactionType,
        )

        deposit_wallet = self._resolve_user_address()
        signer_address = self.relayer_client.signer.address()
        nonce_payload = self.relayer_client.get_nonce(
            signer_address,
            TransactionType.WALLET.value,
        )
        wallet_nonce = str(nonce_payload["nonce"])

        calls = [
            DepositWalletCall(
                target=tx["to"],
                value=str(tx.get("value", 0)),
                data=tx["data"],
            )
            for tx in txs
        ]

        deadline = str(int(_time.time()) + self.DEFAULT_DEADLINE_SEC)
        response = self.relayer_client.execute_deposit_wallet_batch(
            calls=calls,
            wallet_address=deposit_wallet,
            nonce=wallet_nonce,
            deadline=deadline,
        )
        confirmed = response.wait()
        if confirmed is None:
            raise Exception(
                f"deposit-wallet relayer batch unconfirmed (metadata={metadata})"
            )
        return confirmed

    def _submit_redeem(self, txs: list[dict]) -> dict:
        return self._submit_transactions(txs, "redeem")
