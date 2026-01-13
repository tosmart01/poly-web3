# -*- coding = utf-8 -*-
# @Time: 2025-12-27 16:00:42
# @Author: PinBar
# @Site:
# @File: proxy_service.py
# @Software: PyCharm
import requests

from web3 import Web3
from eth_utils import to_bytes

from poly_web3.const import (
    proxy_wallet_factory_abi,
    CTF_ADDRESS,
    RELAYER_URL,
    PROXY_INIT_CODE_HASH,
    SUBMIT_TRANSACTION,
    STATE_MINED,
    STATE_CONFIRMED,
    STATE_FAILED,
    NEG_RISK_ADAPTER_ADDRESS,
)
from poly_web3.web3_service.base import BaseWeb3Service
from poly_web3.signature.build import derive_proxy_wallet, create_struct_hash
from poly_web3.signature.hash_message import hash_message
from poly_web3.signature import secp256k1
from poly_web3.log import logger


class ProxyWeb3Service(BaseWeb3Service):
    def build_proxy_transaction_request(self, args: dict) -> dict:
        proxy_contract_config = self.get_contract_config()["ProxyContracts"]
        to = proxy_contract_config["ProxyFactory"]
        proxy = derive_proxy_wallet(args["from"], to, PROXY_INIT_CODE_HASH)
        relayer_fee = "0"
        relay_hub = proxy_contract_config["RelayHub"]
        gas_limit_str = self.estimate_gas(
            tx={"from": args["from"], "to": to, "data": args["data"]}
        )
        sig_params = {
            "gasPrice": args.get("gasPrice"),
            "gasLimit": gas_limit_str,
            "relayerFee": relayer_fee,
            "relayHub": relay_hub,
            "relay": args.get("relay"),
        }
        tx_hash = create_struct_hash(
            args["from"],
            to,
            args["data"],
            relayer_fee,
            args.get("gasPrice"),
            gas_limit_str,
            args["nonce"],
            relay_hub,
            args.get("relay"),
        )
        message = {"raw": list(to_bytes(hexstr=tx_hash))}

        r, s, recovery = secp256k1.sign(
            hash_message(message)[2:], self.clob_client.signer.private_key
        )
        signature = {
            "r": secp256k1.int_to_hex(r, 32),
            "s": secp256k1.int_to_hex(s, 32),
            "v": 28 if recovery else 27,
            "yParity": recovery,
        }
        final_sig = secp256k1.serialize_signature(**signature, to="hex")
        req = {
            "from": args["from"],
            "to": to,
            "proxyWallet": proxy,
            "data": args["data"],
            "nonce": args["nonce"],
            "signature": final_sig,
            "signatureParams": sig_params,
            "type": self.wallet_type.value,
            "metadata": "redeem",
        }
        return req

    def encode_proxy_transaction_data(self, txns):
        # Prepare the arguments for the 'proxy' function
        calls_data = [
            (txn["typeCode"], txn["to"], txn["value"], txn["data"]) for txn in txns
        ]

        # Create the contract object
        contract = self.w3.eth.contract(abi=proxy_wallet_factory_abi)

        # Encode function data
        function_data = contract.encodeABI(fn_name="proxy", args=[calls_data])

        return function_data

    def _build_redeem_txs_from_positions(self, positions: list[dict]) -> list[dict]:
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
        txs: list[dict] = []
        for condition_id, amounts in neg_amounts_by_condition.items():
            int_amounts = [int(amount * 1e6) for amount in amounts]
            txs.append(
                {
                    "to": NEG_RISK_ADAPTER_ADDRESS,
                    "data": self.build_neg_risk_redeem_tx_data(condition_id, int_amounts),
                    "value": 0,
                    "typeCode": 1,
                }
            )
        for condition_id in normal_conditions:
            txs.append(
                {
                    "to": CTF_ADDRESS,
                    "data": self.build_ctf_redeem_tx_data(condition_id),
                    "value": 0,
                    "typeCode": 1,
                }
            )
        return txs

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

    def _redeem_batch(self, condition_ids: list[str], batch_size: int) -> list[dict]:
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

    def _submit_proxy_redeem(self, txs: list[dict]) -> dict:
        if self.clob_client is None:
            raise Exception("signer not found")
        _from = Web3.to_checksum_address(self.clob_client.get_address())
        rp = self._get_relay_payload(_from, self.wallet_type)
        args = {
            "from": _from,
            "gasPrice": "0",
            "data": self.encode_proxy_transaction_data(txs),
            "relay": rp["address"],
            "nonce": rp["nonce"],
        }
        req = self.build_proxy_transaction_request(args)
        headers = self.relayer_client._generate_builder_headers(
            "POST", SUBMIT_TRANSACTION, req
        )
        response = requests.post(
            RELAYER_URL + SUBMIT_TRANSACTION, json=req, headers=headers
        ).json()
        redeem_res = self.relayer_client.poll_until_state(
            transaction_id=response["transactionID"],
            states=[STATE_MINED, STATE_CONFIRMED],
            fail_state=STATE_FAILED,
            max_polls=100,
        )
        return redeem_res

    def _redeem_from_positions(
            self, positions: list[dict], batch_size: int
    ) -> list[dict]:
        if not positions:
            return []
        positions_by_condition: dict[str, list[dict]] = {}
        for pos in positions:
            condition_id = pos.get("conditionId")
            if not condition_id:
                continue
            positions_by_condition.setdefault(condition_id, []).append(pos)

        redeem_list = []
        condition_ids = list(positions_by_condition.keys())
        for batch in self._chunk_condition_ids(condition_ids, batch_size):
            batch_positions = []
            for condition_id in batch:
                batch_positions.extend(positions_by_condition.get(condition_id, []))
            try:
                txs = self._build_redeem_txs_from_positions(batch_positions)
                if not txs:
                    continue
                redeem_res = self._submit_proxy_redeem(txs)
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
                logger.info(f"redeem batch error, {batch=}, error={e}")
        return redeem_list

    def redeem(
            self,
            condition_ids: str | list[str],
            batch_size: int = 10,
    ):
        if isinstance(condition_ids, str):
            condition_ids = [condition_ids]
        return self._redeem_batch(condition_ids, batch_size)

    def redeem_all(self, batch_size: int = 10) -> list[dict]:
        positions = self.fetch_positions(user_address=self._resolve_user_address())
        return self._redeem_from_positions(positions, batch_size)
