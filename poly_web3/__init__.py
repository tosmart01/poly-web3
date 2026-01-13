# -*- coding = utf-8 -*-
# @Time: 2025/12/19 15:24
# @Author: PinBar
# @Site:
# @File: __init__.py.py
# @Software: PyCharm
from typing import Union

from py_clob_client.client import ClobClient
from py_builder_relayer_client.client import RelayClient

from poly_web3.const import RELAYER_URL
from poly_web3.web3_service.base import BaseWeb3Service
from poly_web3.schema import WalletType
from poly_web3.web3_service import SafeWeb3Service, EOAWeb3Service, ProxyWeb3Service


def PolyWeb3Service(
    clob_client: ClobClient,
    relayer_client: RelayClient = None,
    rpc_url: str | None = None,
) -> Union[SafeWeb3Service, EOAWeb3Service, ProxyWeb3Service]:  # noqa
    services = {
        WalletType.EOA: EOAWeb3Service,
        WalletType.PROXY: ProxyWeb3Service,
        WalletType.SAFE: SafeWeb3Service,
    }

    wallet_type = WalletType.get_with_code(clob_client.builder.sig_type)
    if service := services.get(wallet_type):
        return service(clob_client, relayer_client, rpc_url=rpc_url)
    else:
        raise Exception(f"Unknown wallet type: {wallet_type}")
