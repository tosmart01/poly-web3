# -*- coding = utf-8 -*-
# @Time: 2025-12-30 12:00:00
# @Author: PinBar
# @Site:
# @File: example_split_merge.py
# @Software: PyCharm
import os

import dotenv
from py_builder_relayer_client.client import RelayClient
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
from py_clob_client_v2 import ClobClient

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
    creds = client.create_or_derive_api_key()
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

    condition_id = "0xa2637ee58d82670126d380b8b2f442538757e0b3c715211d30cc57be78e1e619"
    amount = 10  # amount in human pUSD units

    split_result = service.split(condition_id, amount)
    print(split_result)

    merge_result = service.merge(condition_id, amount)
    print(merge_result)

    split_batch_result = service.split_batch([{"condition_id": condition_id, "amount": 10}])
    print(split_batch_result.model_dump_json(indent=2))

    merge_batch_result = service.merge_batch([{"condition_id": condition_id, "amount": 10}])
    print(merge_batch_result.model_dump_json(indent=2))

    merge_all_result = service.merge_all(min_usdc=1, batch_size=10)
    print(merge_all_result)

    merge_plan = service.plan_merge_all(min_usdc=5, exclude_neg_risk=True)
    for i in merge_plan:
        print(i.model_dump_json(indent=2))
