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
    RELAYER_URL,
    PROXY_INIT_CODE_HASH,
    SUBMIT_TRANSACTION,
    STATE_MINED,
    STATE_CONFIRMED,
    STATE_FAILED,
)
from poly_web3.web3_service.base import BaseWeb3Service
from poly_web3.signature.build import derive_proxy_wallet, create_struct_hash
from poly_web3.signature.hash_message import hash_message
from poly_web3.signature import secp256k1
class ProxyWeb3Service(BaseWeb3Service):
    def _build_redeem_tx(self, to: str, data: str) -> dict:
        return {
            "to": to,
            "data": data,
            "value": 0,
            "typeCode": 1,
        }

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

    def _submit_redeem(self, txs: list[dict]) -> dict:
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
