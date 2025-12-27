# -*- coding = utf-8 -*-
# @Time: 2025-12-27 17:01:20
# @Author: PinBar
# @Site:
# @File: example_redeem.py
# @Software: PyCharm
import os

import dotenv
from py_builder_relayer_client.client import RelayClient
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds

from py_clob_client.client import ClobClient

from poly_web3 import RELAYER_URL, PolyWeb3Service

dotenv.load_dotenv()

if __name__ == "__main__":
    host: str = "https://clob.polymarket.com"
    chain_id: int = 137  # No need to adjust this
    client = ClobClient(
        host,
        key=os.getenv("POLY_API_KEY"),
        chain_id=chain_id,
        signature_type=1,
        funder=os.getenv("POLYMARKET_PROXY_ADDRESS"),
    )
    creds = client.create_or_derive_api_creds()
    client.set_api_creds(creds)
    relayer_client = RelayClient(
        RELAYER_URL,
        chain_id,
        os.getenv("POLY_API_KEY"),
        BuilderConfig(
            local_builder_creds=BuilderApiKeyCreds(
                key=os.getenv("BUILDER_KEY"),
                secret=os.getenv("BUILDER_SECRET"),
                passphrase=os.getenv("BUILDER_PASSPHRASE"),
            )
        ),
    )
    condition_id = "0xc3df016175463c44f9c9f98bddaa3bf3daaabb14b069fb7869621cffe73ddd1c"
    service = PolyWeb3Service(clob_client=client, relayer_client=relayer_client)
    redeem = service.redeem(condition_id=condition_id)
    can_redeem = service.is_condition_resolved(condition_id)
    redeem_balance = service.get_redeemable_index_and_balance(
        condition_id, owner=client.builder.funder
    )
    print(can_redeem, redeem_balance, redeem)
