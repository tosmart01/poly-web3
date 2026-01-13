# -*- coding = utf-8 -*-
# @Time: 2025/12/19 15:29
# @Author: PinBar
# @Site:
# @File: const.py
# @Software: PyCharm
from web3 import Web3

GET_NONCE = "/nonce"
GET_RELAY_PAYLOAD = "/relay-payload"
GET_TRANSACTION = "/transaction"
GET_TRANSACTIONS = "/transactions"
SUBMIT_TRANSACTION = "/submit"
GET_DEPLOYED = "/deployed"
RPC_URL = "https://polygon-bor.publicnode.com" # "https://polygon-rpc.com"
RELAYER_URL = "https://relayer-v2.polymarket.com"

STATE_NEW = ("STATE_NEW",)
STATE_EXECUTED = "STATE_EXECUTED"
STATE_MINED = "STATE_MINED"
STATE_INVALID = "STATE_INVALID"
STATE_CONFIRMED = "STATE_CONFIRMED"
STATE_FAILED = "STATE_FAILED"

# address
CTF_ADDRESS = Web3.to_checksum_address("0x4d97dcd97ec945f40cf65f87097ace5ea0476045")
USDC_POLYGON = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
NEG_RISK_ADAPTER_ADDRESS = Web3.to_checksum_address(
    "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"
)
ZERO_BYTES32 = "0x" + "00" * 32
proxy_factory_address = Web3.to_checksum_address(
    "0xaB45c5A4B0c941a2F231C04C3f49182e1A254052"
)
SAFE_INIT_CODE_HASH = (
    "0x2bce2127ff07fb632d16c8347c4ebf501f4841168bed00d9e6ef715ddb6fcecf"
)
PROXY_INIT_CODE_HASH = (
    "0xd21df8dc65880a8606f09fe0ce3df9b8869287ab0b058be05aa9e8af6330a00b"
)

AMOY = {
    "ProxyContracts": {
        # Proxy factory unsupported on Amoy testnet
        "RelayHub": "",
        "ProxyFactory": "",
    },
    "SafeContracts": {
        "SafeFactory": "0xaacFeEa03eb1561C4e67d661e40682Bd20E3541b",
        "SafeMultisend": "0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761",
    },
}

POL = {
    "ProxyContracts": {
        "ProxyFactory": "0xaB45c5A4B0c941a2F231C04C3f49182e1A254052",
        "RelayHub": "0xD216153c06E857cD7f72665E0aF1d7D82172F494",
    },
    "SafeContracts": {
        "SafeFactory": "0xaacFeEa03eb1561C4e67d661e40682Bd20E3541b",
        "SafeMultisend": "0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761",
    },
}

# abi
CTF_ABI_REDEEM = [
    {
        "name": "redeemPositions",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "indexSets", "type": "uint256[]"},
        ],
        "outputs": [],
    }
]

NEG_RISK_ADAPTER_ABI_REDEEM = [
    {
        "name": "redeemPositions",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_conditionId", "type": "bytes32"},
            {"name": "_amounts", "type": "uint256[]"},
        ],
        "outputs": [],
    }
]

proxy_wallet_factory_abi = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "typeCode", "type": "uint8"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "data", "type": "bytes"},
                ],
                "name": "calls",
                "type": "tuple[]",
            }
        ],
        "name": "proxy",
        "outputs": [{"name": "returnValues", "type": "bytes[]"}],
        "stateMutability": "payable",
        "type": "function",
    }
]

CTF_ABI_PAYOUT = [
    {
        "name": "payoutDenominator",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "conditionId", "type": "bytes32"}],
        "outputs": [{"type": "uint256"}],
    },
    {
        "name": "payoutNumerators",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "conditionId", "type": "bytes32"},
            {"name": "index", "type": "uint256"},
        ],
        "outputs": [{"type": "uint256"}],
    },
    {
        "name": "getOutcomeSlotCount",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "conditionId", "type": "bytes32"}],
        "outputs": [{"type": "uint256"}],
    },
    {
        "name": "getCollectionId",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "indexSet", "type": "uint256"},
        ],
        "outputs": [{"type": "bytes32"}],
    },
    {
        "name": "getPositionId",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "collectionId", "type": "bytes32"},
        ],
        "outputs": [{"type": "uint256"}],
    },
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "id", "type": "uint256"},
        ],
        "outputs": [{"type": "uint256"}],
    },
]
