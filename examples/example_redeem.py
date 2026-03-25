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
        signature_type=1,  # signature_type=2 for Safe
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
    service = PolyWeb3Service(
        clob_client=client,
        relayer_client=relayer_client,
        rpc_url="https://polygon-bor.publicnode.com",
    )

    # Redeem all positions that are currently redeemable
    redeem_all = service.redeem_all(batch_size=10)
    print(redeem_all)
    if redeem_all.error_list:
        print("Redeem all failed items:", redeem_all.error_list)
        print("Retry condition ids:", redeem_all.error_condition_ids)

    # Redeem in batch
    condition_ids = [
        "0xaba28be5f981580aa29a123afc8d233dd66c1f236f0d7e1bfffe07777cdb6cc5",
    ]
    redeem_batch = service.redeem(condition_ids, batch_size=10)
    print(redeem_batch)
    if redeem_batch.error_list:
        print("Redeem batch failed items:", redeem_batch.error_list)
        print("Retry condition ids:", redeem_batch.error_condition_ids)


