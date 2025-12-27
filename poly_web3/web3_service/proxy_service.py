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

    def redeem(
        self,
        condition_id: str,
        neg_risk: bool = False,
        redeem_amounts: list[int] | None = None,
    ):
        if neg_risk:
            if redeem_amounts is None or len(redeem_amounts) != 2:
                raise Exception("negRisk redeem requires redeem_amounts with length 2")
            tx_data = self.build_neg_risk_redeem_tx_data(condition_id, redeem_amounts)
            tx_to = NEG_RISK_ADAPTER_ADDRESS
        else:
            tx_data = self.build_ctf_redeem_tx_data(condition_id)
            tx_to = CTF_ADDRESS
        tx = {"to": tx_to, "data": tx_data, "value": 0, "typeCode": 1}
        if self.clob_client is None:
            raise Exception("signer not found")
        _from = Web3.to_checksum_address(self.clob_client.get_address())
        rp = self._get_relay_payload(_from, self.wallet_type)
        args = {
            "from": _from,
            "gasPrice": "0",
            "data": self.encode_proxy_transaction_data([tx]),
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
